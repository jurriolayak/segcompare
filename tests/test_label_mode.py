import io
import sys

import nibabel as nib
import numpy as np

from segcompare.cli import load_label_file, main
from segcompare.metrics import compare_masks_by_labels


def _write_nifti(path, data):
    img = nib.Nifti1Image(data.astype(np.int16), affine=np.eye(4))
    nib.save(img, str(path))


def test_load_label_file_parses_itksnap_format(tmp_path):
    label_file = tmp_path / "labels.txt"
    label_file.write_text(
        '# comment\n'
        '    1   204    0    0        1  1  1    "Piriform Cortex Left"\n'
        '    2   255   90   90        1  1  1    "Piriform Cortex Right"\n',
        encoding='utf-8',
    )

    labels = load_label_file(label_file)

    assert labels == {1: "Piriform Cortex Left", 2: "Piriform Cortex Right"}


def test_compare_masks_by_labels_keeps_running_with_missing_roi(tmp_path):
    mask1 = tmp_path / "mask1.nii.gz"
    mask2 = tmp_path / "mask2.nii.gz"
    arr1 = np.zeros((2, 2, 2), dtype=np.int16)
    arr2 = np.zeros((2, 2, 2), dtype=np.int16)
    arr1[0, 0, 0] = 1
    arr2[0, 0, 0] = 1
    _write_nifti(mask1, arr1)
    _write_nifti(mask2, arr2)

    results = compare_masks_by_labels(mask1, mask2, {1: "ROI 1", 2: "ROI 2"})

    assert len(results["rows"]) == 2
    assert results["rows"][0]["dice"] == 1.0
    assert set(results["warnings"]) == {
        f'Warning: no label 2 ("ROI 2") in {mask1}',
        f'Warning: no label 2 ("ROI 2") in {mask2}',
    }


def test_cli_label_mode_outputs_csv(tmp_path, monkeypatch):
    mask1 = tmp_path / "mask1.nii.gz"
    mask2 = tmp_path / "mask2.nii.gz"
    labels = tmp_path / "labels.label"
    arr1 = np.zeros((2, 2, 2), dtype=np.int16)
    arr2 = np.zeros((2, 2, 2), dtype=np.int16)
    arr1[0, 0, 0] = 1
    arr2[0, 0, 1] = 1
    _write_nifti(mask1, arr1)
    _write_nifti(mask2, arr2)
    labels.write_text('1 255 0 0 1 1 1 "ROI 1"\n', encoding='utf-8')

    stdout = io.StringIO()
    stderr = io.StringIO()
    argv = ["segcompare", str(mask1), str(mask2), "-l", str(labels), "-dice", "--csv"]

    monkeypatch.setattr(sys, "argv", argv)
    monkeypatch.setattr(sys, "stdout", stdout)
    monkeypatch.setattr(sys, "stderr", stderr)

    main()

    assert "label_idx,label_name,Dice" in stdout.getvalue()
