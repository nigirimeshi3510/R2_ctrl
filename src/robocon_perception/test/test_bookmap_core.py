from pathlib import Path

import pytest

from robocon_perception.bookmap_core import (
    DetectionObservation,
    EMPTY_LABEL,
    R2_LABEL,
    UNKNOWN_LABEL,
    build_bookmap_arrays,
    load_lut_regions,
    map_point_to_cell_id,
)


@pytest.fixture
def lut_regions():
    lut_path = (
        Path(__file__).resolve().parents[1] / "config" / "bookmap_lut.yaml"
    )
    return load_lut_regions(str(lut_path))


def test_point_mapping_works(lut_regions):
    assert map_point_to_cell_id(10.0, 10.0, lut_regions) == 1
    assert map_point_to_cell_id(500.0, 100.0, lut_regions) == 2
    assert map_point_to_cell_id(1000.0, 500.0, lut_regions) == 12


def test_fixed_detections_map_to_expected_cells(lut_regions):
    detections = [
        DetectionObservation(cx=100.0, cy=100.0, class_id="R2", score=0.90),
        DetectionObservation(cx=350.0, cy=420.0, class_id="R1", score=0.95),
    ]

    labels, confidences = build_bookmap_arrays(
        detections,
        lut_regions,
        confidence_threshold=0.6,
    )

    assert labels[0] == R2_LABEL  # cell 1
    assert labels[9] == "R1"  # cell 10
    assert confidences[0] == pytest.approx(0.90)
    assert confidences[9] == pytest.approx(0.95)


def test_below_threshold_becomes_unknown(lut_regions):
    detections = [
        DetectionObservation(cx=110.0, cy=120.0, class_id="R2", score=0.59),
    ]

    labels, confidences = build_bookmap_arrays(
        detections,
        lut_regions,
        confidence_threshold=0.6,
    )

    assert labels[0] == UNKNOWN_LABEL
    assert confidences[0] == pytest.approx(0.59)


def test_unknown_label_becomes_unknown(lut_regions):
    detections = [
        DetectionObservation(cx=100.0, cy=100.0, class_id="alien", score=0.95),
    ]

    labels, _ = build_bookmap_arrays(
        detections,
        lut_regions,
        confidence_threshold=0.6,
    )

    assert labels[0] == UNKNOWN_LABEL


def test_out_of_region_detection_is_ignored(lut_regions):
    detections = [
        DetectionObservation(cx=1500.0, cy=1500.0, class_id="R2", score=0.95),
    ]

    labels, confidences = build_bookmap_arrays(
        detections,
        lut_regions,
        confidence_threshold=0.6,
        default_empty_confidence=1.0,
    )

    assert labels[0] == EMPTY_LABEL
    assert all(c == pytest.approx(1.0) for c in confidences)


def test_higher_confidence_wins_same_cell(lut_regions):
    detections = [
        DetectionObservation(cx=100.0, cy=100.0, class_id="R2", score=0.65),
        DetectionObservation(cx=110.0, cy=120.0, class_id="R1", score=0.80),
    ]

    labels, confidences = build_bookmap_arrays(
        detections,
        lut_regions,
        confidence_threshold=0.6,
    )

    assert labels[0] == "R1"
    assert confidences[0] == pytest.approx(0.80)


def test_lut_validation_requires_all_cells(tmp_path):
    bad_lut = tmp_path / "bad.yaml"
    bad_lut.write_text(
        "cells:\n"
        "  - {cell_id: 1, x_min: 0, x_max: 10, y_min: 0, y_max: 10}\n",
        encoding="utf-8",
    )

    with pytest.raises(ValueError):
        load_lut_regions(str(bad_lut))
