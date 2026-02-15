# segcompare

A command-line tool for comparing two segmentation masks and calculating common evaluation metrics used in medical image segmentation.

## Features

- **Dice Similarity Coefficient (DSC)** — overlap metric (0–1, higher is better)
- **Jaccard Index (IoU)** — intersection over union
- **Volume Similarity** — quantifies volumetric agreement between masks
- **95th Percentile Hausdorff Distance (HD95)** — robust surface distance metric in mm
- **Average Surface Distance (ASD)** — mean surface distance in mm
- **Volume measurements** — reported in mm³

## Installation

### From GitHub (recommended)

```bash
pip install git+https://github.com/jurriolayak/segcompare.git
```

### With faster surface distance calculation

```bash
pip install "segcompare[fast] @ git+https://github.com/jurriolayak/segcompare.git"
```

This installs DeepMind's `surface-distance` library for more accurate surface metrics.

### From source

```bash
git clone https://github.com/jurriolayak/segcompare.git
cd segcompare
pip install -e .
```

## Usage

### Basic comparison

```bash
segcompare mask1.nii.gz mask2.nii.gz
```

Example output:

```
============================================================
  SEGMENTATION COMPARISON RESULTS
============================================================

  Mask 1: mask1.nii.gz
  Mask 2: mask2.nii.gz

  OVERLAP METRICS
  ----------------------------------------
    Dice Coefficient (DSC):    0.8542
    Jaccard Index (IoU):       0.7456
    Volume Similarity:         0.9234

  SURFACE DISTANCE METRICS
  ----------------------------------------
    HD95:                      2.45 mm
    Avg Surface Distance:      0.89 mm

  VOLUME
  ----------------------------------------
    Mask 1 volume:             1234.5 mm³
    Mask 2 volume:             1198.2 mm³
    Overlap volume:            1056.3 mm³
    Volume difference:         36.3 mm³

  IMAGE INFO
  ----------------------------------------
    Shape:                     [256, 256, 180]
    Voxel spacing:             ['1.00', '1.00', '1.00'] mm

============================================================
```

### Output formats

```bash
# JSON output
segcompare mask1.nii.gz mask2.nii.gz --json

# CSV output
segcompare mask1.nii.gz mask2.nii.gz --csv

# Save to file
segcompare mask1.nii.gz mask2.nii.gz -o results.csv

# Quiet mode (DSC value only)
segcompare mask1.nii.gz mask2.nii.gz -q
```

### Per-structure metrics with label files

segcompare supports ITK-SNAP style label files (`.txt` or `.label`) for per-structure evaluation:

```bash
segcompare mask1.nii.gz mask2.nii.gz -l labels.txt -dice
segcompare mask1.nii.gz mask2.nii.gz -l labels.txt -jaccard
segcompare mask1.nii.gz mask2.nii.gz -l labels.txt -hd
segcompare mask1.nii.gz mask2.nii.gz -l labels.txt -all --csv
```

If a label defined in the label file is missing from one of the masks, segcompare prints a warning and continues processing the remaining structures.

### Scripting examples

```bash
# Get just the Dice coefficient for scripting
dice=$(segcompare mask1.nii.gz mask2.nii.gz -q)
echo "Dice: $dice"

# Batch processing
for pred in predictions/*.nii.gz; do
    name=$(basename "$pred" .nii.gz)
    segcompare "ground_truth/${name}.nii.gz" "$pred" --csv >> results.csv
done
```

### Python API

```python
from segcompare import compare_masks

results = compare_masks("mask1.nii.gz", "mask2.nii.gz")
print(f"Dice: {results['dice']:.4f}")
print(f"HD95: {results['hd95_mm']:.2f} mm")
```

## Metrics

| Metric | Range | Ideal | Description |
|--------|-------|-------|-------------|
| DSC | 0–1 | 1 | Dice Similarity Coefficient; measures spatial overlap |
| IoU | 0–1 | 1 | Jaccard Index; intersection over union |
| VS | 0–1 | 1 | Volume Similarity; penalises volume differences |
| HD95 | 0–inf mm | 0 | 95th percentile of symmetric surface distances |
| ASD | 0–inf mm | 0 | Mean of all symmetric surface distances |

## Supported formats

Any format supported by [nibabel](https://nipy.org/nibabel/), including NIfTI (`.nii`, `.nii.gz`).

## Requirements

- Python >= 3.8
- numpy
- nibabel
- scipy
- surface-distance (optional) — DeepMind's library for more accurate HD95/ASD calculation

## Licence

MIT Licence. See [LICENSE](LICENSE) for details.

## Author

Javier Urriola Yaksic
GitHub: [@jurriolayak](https://github.com/jurriolayak)

## Citation

If you use this tool in your research, please consider citing:

```bibtex
@software{segcompare,
  author = {Urriola Yaksic, Javier},
  title = {segcompare: CLI tool for segmentation mask comparison},
  url = {https://github.com/jurriolayak/segcompare},
  year = {2026}
}
```
