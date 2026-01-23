# segcompare

A command-line tool to compare two segmentation masks and calculate common evaluation metrics used in medical image segmentation.

## Features

- **Dice Similarity Coefficient (DSC)** - Overlap metric (0-1, higher is better)
- **Jaccard Index (IoU)** - Intersection over Union
- **Volume Similarity** - How similar the volumes are
- **95th Percentile Hausdorff Distance (HD95)** - Surface distance metric in mm
- **Average Surface Distance (ASD)** - Mean surface distance in mm
- **Volume measurements** - In mm³

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

Output:
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

# Quiet mode (just DSC value)
segcompare mask1.nii.gz mask2.nii.gz -q
```

### Scripting example

```bash
# Get just the Dice coefficient for scripting
dice=$(segcompare mask1.nii.gz mask2.nii.gz -q)
echo "Dice: $dice"

# Process multiple files
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

## Metrics Explained

| Metric | Range | Best Value | Description |
|--------|-------|------------|-------------|
| DSC | 0-1 | 1 | Dice Similarity Coefficient, measures overlap |
| IoU | 0-1 | 1 | Jaccard Index, intersection over union |
| VS | 0-1 | 1 | Volume Similarity, penalizes volume differences |
| HD95 | 0-∞ mm | 0 | 95th percentile of surface distances |
| ASD | 0-∞ mm | 0 | Average of all surface distances |

## Supported Formats

- NIfTI (.nii, .nii.gz)
- Any format supported by nibabel

## Requirements

- Python ≥ 3.8
- numpy
- nibabel
- scipy

Optional:
- surface-distance (DeepMind) - for more accurate HD95/ASD calculation

## License

MIT License - see [LICENSE](LICENSE) file.

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
