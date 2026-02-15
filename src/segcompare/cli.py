"""
Command-line interface for segcompare.
"""

import argparse
import sys
import json
import re
from pathlib import Path

import numpy as np

from .metrics import compare_masks, compare_masks_by_labels, is_using_surface_distance_lib


def format_results(results, fmt='table'):
    """
    Format comparison results for output.
    
    Parameters
    ----------
    results : dict
        Output from compare_masks()
    fmt : str
        Output format: 'table', 'json', or 'csv'
    
    Returns
    -------
    str
        Formatted results string
    """
    if fmt == 'json':
        # Convert numpy types to Python types
        clean = {}
        for k, v in results.items():
            if isinstance(v, (np.floating, np.integer)):
                clean[k] = float(v)
            elif isinstance(v, np.ndarray):
                clean[k] = v.tolist()
            else:
                clean[k] = v
        return json.dumps(clean, indent=2)
    
    elif fmt == 'csv':
        header = ','.join(results.keys())
        values = ','.join(str(v) for v in results.values())
        return f"{header}\n{values}"
    
    else:  # table format
        lines = [
            "",
            "=" * 60,
            "  SEGMENTATION COMPARISON RESULTS",
            "=" * 60,
            "",
            f"  Mask 1: {Path(results['mask1']).name}",
            f"  Mask 2: {Path(results['mask2']).name}",
            "",
            "  OVERLAP METRICS",
            "  " + "-" * 40,
            f"    Dice Coefficient (DSC):    {results['dice']:.4f}",
            f"    Jaccard Index (IoU):       {results['jaccard']:.4f}",
            f"    Volume Similarity:         {results['volume_similarity']:.4f}",
            "",
            "  SURFACE DISTANCE METRICS",
            "  " + "-" * 40,
        ]
        
        if np.isinf(results['hd95_mm']):
            lines.append("    HD95:                      N/A (no overlap)")
            lines.append("    Avg Surface Distance:      N/A")
        else:
            lines.append(f"    HD95:                      {results['hd95_mm']:.2f} mm")
            lines.append(f"    Avg Surface Distance:      {results['asd_mm']:.2f} mm")
        
        lines.extend([
            "",
            "  VOLUME",
            "  " + "-" * 40,
            f"    Mask 1 volume:             {results['volume1_mm3']:.1f} mm³",
            f"    Mask 2 volume:             {results['volume2_mm3']:.1f} mm³",
            f"    Overlap volume:            {results['overlap_mm3']:.1f} mm³",
            f"    Volume difference:         {abs(results['volume1_mm3'] - results['volume2_mm3']):.1f} mm³",
            "",
            "  IMAGE INFO",
            "  " + "-" * 40,
            f"    Shape:                     {results['shape']}",
            f"    Voxel spacing:             {[f'{x:.2f}' for x in results['voxel_spacing_mm']]} mm",
            "",
            "=" * 60,
        ])
        
        if is_using_surface_distance_lib():
            lines.append("  (Using DeepMind surface-distance library)")
        else:
            lines.append("  (Using scipy fallback for surface distances)")
        lines.append("")
        
        return "\n".join(lines)


def load_label_file(path):
    """Load ITK-SnAP style label file into {label_idx: label_name}."""
    labels = {}
    for raw_line in Path(path).read_text(encoding='utf-8').splitlines():
        line = raw_line.strip()
        if not line or line.startswith('#'):
            continue
        match = re.search(r'^(\d+)\b.*?"([^"]+)"', line)
        if match:
            labels[int(match.group(1))] = match.group(2)
    if not labels:
        raise ValueError(f"No labels found in file: {path}")
    return labels


def format_label_results(results, metric='all', fmt='table'):
    """Format per-label results."""
    metric_columns = {
        'dice': [('dice', 'Dice')],
        'jaccard': [('jaccard', 'Jaccard')],
        'hd': [('hd95_mm', 'HD95 (mm)')],
        'all': [('dice', 'Dice'), ('jaccard', 'Jaccard'), ('hd95_mm', 'HD95 (mm)')],
    }[metric]

    if fmt == 'json':
        return json.dumps(results, indent=2)

    if fmt == 'csv':
        headers = ['label_idx', 'label_name'] + [h for _, h in metric_columns]
        lines = [','.join(headers)]
        for row in results['rows']:
            values = [str(row['label_idx']), f"\"{row['label_name']}\""]
            for key, _ in metric_columns:
                value = row[key]
                values.append(f"{value:.4f}" if np.isfinite(value) else "nan")
            lines.append(','.join(values))
        return "\n".join(lines)

    header = f"{'IDX':>4}  {'LABEL':<35}" + "".join(f"{h:>14}" for _, h in metric_columns)
    lines = [
        "",
        "=" * max(70, len(header)),
        "  SEGMENTATION PER-LABEL RESULTS",
        "=" * max(70, len(header)),
        "",
        f"  Mask 1: {Path(results['mask1']).name}",
        f"  Mask 2: {Path(results['mask2']).name}",
        "",
        header,
        "-" * len(header),
    ]
    for row in results['rows']:
        values = []
        for key, _ in metric_columns:
            value = row[key]
            values.append(f"{value:>14.4f}" if np.isfinite(value) else f"{'nan':>14}")
        lines.append(f"{row['label_idx']:>4}  {row['label_name'][:35]:<35}" + "".join(values))
    lines.append("")
    return "\n".join(lines)


def main():
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(
        description='Compare two segmentation masks and calculate metrics.',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
    segcompare mask1.nii.gz mask2.nii.gz
    segcompare mask1.nii.gz mask2.nii.gz --json
    segcompare mask1.nii.gz mask2.nii.gz -o results.csv

Metrics:
    DSC   - Dice Similarity Coefficient (0-1, higher is better)
    IoU   - Jaccard Index / Intersection over Union
    VS    - Volume Similarity (0-1, higher is better)
    HD95  - 95th percentile Hausdorff Distance (mm, lower is better)
    ASD   - Average Surface Distance (mm, lower is better)

Install surface-distance for more accurate HD95/ASD:
    pip install surface-distance
        """
    )
    
    parser.add_argument('mask1', type=str, help='Path to first mask (NIfTI)')
    parser.add_argument('mask2', type=str, help='Path to second mask (NIfTI)')
    parser.add_argument('--json', action='store_true', help='Output as JSON')
    parser.add_argument('--csv', action='store_true', help='Output as CSV')
    parser.add_argument('-o', '--output', type=str, help='Save results to file')
    parser.add_argument('-q', '--quiet', action='store_true', help='Minimal output (just DSC)')
    parser.add_argument('-l', '--labels', type=str, help='Path to label file (.txt or .label)')
    metric_group = parser.add_mutually_exclusive_group()
    metric_group.add_argument('-dice', action='store_true', help='Per-label Dice metric (requires -l)')
    metric_group.add_argument('-hd', action='store_true', help='Per-label HD95 metric (requires -l)')
    metric_group.add_argument('-jaccard', action='store_true', help='Per-label Jaccard metric (requires -l)')
    metric_group.add_argument('-all', action='store_true', help='Per-label Dice, Jaccard and HD95 (requires -l)')
    parser.add_argument('--version', action='version', version='%(prog)s 1.0.0')
    
    args = parser.parse_args()
    
    # Validate inputs
    if not Path(args.mask1).exists():
        print(f"Error: File not found: {args.mask1}", file=sys.stderr)
        sys.exit(1)
    if not Path(args.mask2).exists():
        print(f"Error: File not found: {args.mask2}", file=sys.stderr)
        sys.exit(1)
    if args.labels and not Path(args.labels).exists():
        print(f"Error: File not found: {args.labels}", file=sys.stderr)
        sys.exit(1)
    if args.labels and Path(args.labels).suffix.lower() not in {'.txt', '.label'}:
        print("Error: -l/--labels file must be .txt or .label", file=sys.stderr)
        sys.exit(1)

    if any([args.dice, args.hd, args.jaccard, args.all]) and not args.labels:
        print("Error: -dice/-hd/-jaccard/-all require -l/--labels", file=sys.stderr)
        sys.exit(1)

    metric = 'all'
    if args.dice:
        metric = 'dice'
    elif args.hd:
        metric = 'hd'
    elif args.jaccard:
        metric = 'jaccard'
    
    try:
        if args.labels:
            label_map = load_label_file(args.labels)
            results = compare_masks_by_labels(args.mask1, args.mask2, label_map)
        else:
            results = compare_masks(args.mask1, args.mask2)
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)
    
    # Format output
    if args.labels:
        if args.quiet:
            print("Error: -q/--quiet is not supported with per-label mode", file=sys.stderr)
            sys.exit(1)
        if args.json:
            output = format_label_results(results, metric, 'json')
        elif args.csv:
            output = format_label_results(results, metric, 'csv')
        else:
            output = format_label_results(results, metric, 'table')
        for warning in results.get('warnings', []):
            print(warning, file=sys.stderr)
    elif args.quiet:
        output = f"{results['dice']:.4f}"
    elif args.json:
        output = format_results(results, 'json')
    elif args.csv:
        output = format_results(results, 'csv')
    else:
        output = format_results(results, 'table')
    
    # Output
    if args.output:
        with open(args.output, 'w') as f:
            f.write(output)
        if not args.quiet:
            print(f"Results saved to: {args.output}")
    else:
        print(output)


if __name__ == '__main__':
    main()
