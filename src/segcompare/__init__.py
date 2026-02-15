"""
segcompare - Compare segmentation masks and calculate metrics
=============================================================

A command-line tool and Python library for comparing two segmentation masks
and calculating common evaluation metrics used in medical image segmentation.

Example usage:
    >>> from segcompare import compare_masks
    >>> results = compare_masks("mask1.nii.gz", "mask2.nii.gz")
    >>> print(f"Dice: {results['dice']:.4f}")

CLI usage:
    $ segcompare mask1.nii.gz mask2.nii.gz
"""

from .metrics import (
    compare_masks,
    compare_masks_by_labels,
    calculate_dice,
    calculate_volume_similarity,
    calculate_surface_metrics,
)

__version__ = "1.0.0"
__author__ = "Javier Urriola Yaksic"
__email__ = "jurriolayak@users.noreply.github.com"

__all__ = [
    "compare_masks",
    "compare_masks_by_labels",
    "calculate_dice",
    "calculate_volume_similarity",
    "calculate_surface_metrics",
]
