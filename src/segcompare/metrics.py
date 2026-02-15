"""
Core metrics calculation functions for segmentation comparison.
"""

import numpy as np
import nibabel as nib

# Try to import DeepMind's surface_distance (more accurate)
try:
    import surface_distance as sd
    USE_SD_LIB = True
except ImportError:
    USE_SD_LIB = False
    from scipy import ndimage
    from scipy.ndimage import binary_erosion
    from scipy.spatial import cKDTree


def calculate_dice(mask1, mask2):
    """
    Calculate Dice Similarity Coefficient.
    
    Parameters
    ----------
    mask1 : np.ndarray
        First binary mask (will be binarized if not already)
    mask2 : np.ndarray
        Second binary mask (will be binarized if not already)
    
    Returns
    -------
    float
        Dice coefficient between 0 and 1
    """
    intersection = np.sum((mask1 > 0) & (mask2 > 0))
    sum_masks = np.sum(mask1 > 0) + np.sum(mask2 > 0)
    if sum_masks == 0:
        return 0.0
    return 2.0 * intersection / sum_masks


def calculate_volume_similarity(mask1, mask2):
    """
    Calculate Volume Similarity.
    
    VS = 1 - |V1 - V2| / (V1 + V2)
    
    Parameters
    ----------
    mask1 : np.ndarray
        First binary mask
    mask2 : np.ndarray
        Second binary mask
    
    Returns
    -------
    float
        Volume similarity between 0 and 1, where 1 is perfect match
    """
    v1 = np.sum(mask1 > 0)
    v2 = np.sum(mask2 > 0)
    if v1 + v2 == 0:
        return 0.0
    return 1.0 - abs(v1 - v2) / (v1 + v2)


def _surface_distances_scipy(mask1, mask2, voxel_spacing):
    """Calculate surface distances using scipy (fallback method)."""
    from scipy import ndimage
    from scipy.ndimage import binary_erosion
    from scipy.spatial import cKDTree
    
    struct = ndimage.generate_binary_structure(3, 1)
    surface1 = mask1 & ~binary_erosion(mask1, struct)
    surface2 = mask2 & ~binary_erosion(mask2, struct)
    
    coords1 = np.array(np.where(surface1)).T * voxel_spacing
    coords2 = np.array(np.where(surface2)).T * voxel_spacing
    
    if len(coords1) == 0 or len(coords2) == 0:
        return np.array([np.inf]), np.array([np.inf])
    
    tree2 = cKDTree(coords2)
    dist1to2, _ = tree2.query(coords1)
    
    tree1 = cKDTree(coords1)
    dist2to1, _ = tree1.query(coords2)
    
    return dist1to2, dist2to1


def calculate_surface_metrics(mask1, mask2, voxel_spacing):
    """
    Calculate surface-based metrics: HD95 and Average Surface Distance.
    
    Parameters
    ----------
    mask1 : np.ndarray
        First binary mask
    mask2 : np.ndarray
        Second binary mask
    voxel_spacing : tuple or list
        Voxel dimensions in mm (e.g., [1.0, 1.0, 1.0])
    
    Returns
    -------
    dict
        Dictionary with 'hd95' and 'asd' in mm
    """
    if np.sum(mask1) == 0 or np.sum(mask2) == 0:
        return {'hd95': np.inf, 'asd': np.inf}
    
    if USE_SD_LIB:
        # Use DeepMind surface_distance library (more accurate)
        surface_distances = sd.compute_surface_distances(
            mask1.astype(bool), 
            mask2.astype(bool), 
            spacing_mm=voxel_spacing
        )
        hd95 = sd.compute_robust_hausdorff(surface_distances, 95)
        asd = sd.compute_average_surface_distance(surface_distances)
        # asd returns (avg_dist_1to2, avg_dist_2to1), take mean
        asd = np.mean(asd)
    else:
        # Fallback to scipy implementation
        dist1to2, dist2to1 = _surface_distances_scipy(
            mask1 > 0, mask2 > 0, np.array(voxel_spacing)
        )
        all_dist = np.concatenate([dist1to2, dist2to1])
        valid = all_dist[~np.isinf(all_dist)]
        
        if len(valid) > 0:
            hd95 = np.percentile(valid, 95)
            asd = np.mean(valid)
        else:
            hd95 = np.inf
            asd = np.inf
    
    return {'hd95': hd95, 'asd': asd}


def _compare_binary_masks(mask1_bin, mask2_bin, voxel_spacing):
    """Calculate all metrics from two binary masks."""
    voxel_volume = np.prod(voxel_spacing)

    dice = calculate_dice(mask1_bin, mask2_bin)
    vol_sim = calculate_volume_similarity(mask1_bin, mask2_bin)

    vol1 = np.sum(mask1_bin) * voxel_volume
    vol2 = np.sum(mask2_bin) * voxel_volume

    overlap = np.sum(mask1_bin & mask2_bin) * voxel_volume
    union = np.sum(mask1_bin | mask2_bin) * voxel_volume
    jaccard = overlap / union if union > 0 else 0.0

    surf_metrics = calculate_surface_metrics(mask1_bin, mask2_bin, voxel_spacing)

    return {
        'dice': float(dice),
        'jaccard': float(jaccard),
        'volume_similarity': float(vol_sim),
        'hd95_mm': float(surf_metrics['hd95']),
        'asd_mm': float(surf_metrics['asd']),
        'volume1_mm3': float(vol1),
        'volume2_mm3': float(vol2),
        'overlap_mm3': float(overlap),
    }


def compare_masks(path1, path2):
    """
    Load two masks and calculate all comparison metrics.
    
    Parameters
    ----------
    path1 : str or Path
        Path to first NIfTI mask
    path2 : str or Path
        Path to second NIfTI mask
    
    Returns
    -------
    dict
        Dictionary containing all metrics:
        - dice: Dice Similarity Coefficient
        - jaccard: Jaccard Index (IoU)
        - volume_similarity: Volume Similarity
        - hd95_mm: 95th percentile Hausdorff Distance in mm
        - asd_mm: Average Surface Distance in mm
        - volume1_mm3: Volume of first mask in mm³
        - volume2_mm3: Volume of second mask in mm³
        - overlap_mm3: Overlap volume in mm³
        - voxel_spacing_mm: Voxel dimensions
        - shape: Image dimensions
    
    Raises
    ------
    ValueError
        If masks have different shapes
    FileNotFoundError
        If mask files don't exist
    
    Example
    -------
    >>> results = compare_masks("ground_truth.nii.gz", "prediction.nii.gz")
    >>> print(f"Dice: {results['dice']:.4f}")
    >>> print(f"HD95: {results['hd95_mm']:.2f} mm")
    """
    # Load images
    img1 = nib.load(str(path1))
    img2 = nib.load(str(path2))
    
    mask1 = img1.get_fdata()
    mask2 = img2.get_fdata()
    
    # Get voxel spacing from first image
    voxel_spacing = img1.header.get_zooms()[:3]
    # Check shapes match
    if mask1.shape != mask2.shape:
        raise ValueError(f"Shape mismatch: {mask1.shape} vs {mask2.shape}")

    metrics = _compare_binary_masks(mask1 > 0, mask2 > 0, voxel_spacing)

    return {
        'mask1': str(path1),
        'mask2': str(path2),
        **metrics,
        'voxel_spacing_mm': list(voxel_spacing),
        'shape': list(mask1.shape),
    }


def compare_masks_by_labels(path1, path2, labels):
    """
    Load two masks and calculate metrics per label index.

    Parameters
    ----------
    path1 : str or Path
        Path to first mask
    path2 : str or Path
        Path to second mask
    labels : dict[int, str]
        Mapping of label index -> label name
    """
    img1 = nib.load(str(path1))
    img2 = nib.load(str(path2))

    mask1 = img1.get_fdata()
    mask2 = img2.get_fdata()

    if mask1.shape != mask2.shape:
        raise ValueError(f"Shape mismatch: {mask1.shape} vs {mask2.shape}")

    voxel_spacing = img1.header.get_zooms()[:3]
    rows = []
    warnings = []

    for label_idx, label_name in labels.items():
        label_mask1 = mask1 == label_idx
        label_mask2 = mask2 == label_idx

        if np.sum(label_mask1) == 0:
            warnings.append(
                f'Warning: no label {label_idx} ("{label_name}") in {path1}'
            )
        if np.sum(label_mask2) == 0:
            warnings.append(
                f'Warning: no label {label_idx} ("{label_name}") in {path2}'
            )

        rows.append({
            'label_idx': int(label_idx),
            'label_name': label_name,
            **_compare_binary_masks(label_mask1, label_mask2, voxel_spacing),
        })

    return {
        'mask1': str(path1),
        'mask2': str(path2),
        'rows': rows,
        'warnings': warnings,
        'voxel_spacing_mm': list(voxel_spacing),
        'shape': list(mask1.shape),
    }


def is_using_surface_distance_lib():
    """Check if DeepMind's surface-distance library is available."""
    return USE_SD_LIB
