"""Core logic for converting detections into a 12-cell BookMap."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml

EMPTY_LABEL = "EMPTY"
R2_LABEL = "R2"
R1_LABEL = "R1"
FAKE_LABEL = "FAKE"
UNKNOWN_LABEL = "UNKNOWN"

KNOWN_BOOK_LABELS = {R2_LABEL, R1_LABEL, FAKE_LABEL}


@dataclass(frozen=True)
class CellRegion:
    """Axis-aligned pixel region mapped to one cell."""

    cell_id: int
    x_min: float
    x_max: float
    y_min: float
    y_max: float

    def contains(self, x: float, y: float) -> bool:
        return self.x_min <= x <= self.x_max and self.y_min <= y <= self.y_max


@dataclass(frozen=True)
class DetectionObservation:
    """Minimal detection data used by the mapping logic."""

    cx: float
    cy: float
    class_id: str
    score: float


def _normalize_label(class_id: str) -> str:
    normalized = class_id.strip().upper()
    if normalized in KNOWN_BOOK_LABELS:
        return normalized
    return UNKNOWN_LABEL


def load_lut_regions(yaml_path: str) -> list[CellRegion]:
    """Load and validate cell LUT regions from YAML file."""
    data = yaml.safe_load(Path(yaml_path).read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ValueError("LUT YAML must be a mapping")

    cells = data.get("cells")
    if not isinstance(cells, list):
        raise ValueError("LUT YAML must have a list field: cells")
    if len(cells) != 12:
        raise ValueError("LUT YAML must define exactly 12 cells")

    regions: list[CellRegion] = []
    cell_ids: set[int] = set()
    required_keys = {"cell_id", "x_min", "x_max", "y_min", "y_max"}

    for idx, cell in enumerate(cells):
        if not isinstance(cell, dict):
            raise ValueError(f"cells[{idx}] must be a mapping")
        missing = required_keys - set(cell.keys())
        if missing:
            raise ValueError(f"cells[{idx}] missing keys: {sorted(missing)}")

        cell_id = int(cell["cell_id"])
        if cell_id < 1 or cell_id > 12:
            raise ValueError(f"cell_id must be in [1, 12], got {cell_id}")
        if cell_id in cell_ids:
            raise ValueError(f"duplicate cell_id: {cell_id}")

        x_min = float(cell["x_min"])
        x_max = float(cell["x_max"])
        y_min = float(cell["y_min"])
        y_max = float(cell["y_max"])
        if x_min > x_max or y_min > y_max:
            raise ValueError(f"invalid bounds for cell_id {cell_id}")

        regions.append(
            CellRegion(
                cell_id=cell_id,
                x_min=x_min,
                x_max=x_max,
                y_min=y_min,
                y_max=y_max,
            )
        )
        cell_ids.add(cell_id)

    if cell_ids != set(range(1, 13)):
        raise ValueError("cell_id set must be exactly {1..12}")

    return regions


def map_point_to_cell_id(cx: float, cy: float, regions: list[CellRegion]) -> int | None:
    """Map a center point to the first matching cell ID."""
    for region in regions:
        if region.contains(cx, cy):
            return region.cell_id
    return None


def build_bookmap_arrays(
    detections: list[DetectionObservation],
    regions: list[CellRegion],
    confidence_threshold: float,
    default_empty_confidence: float = 1.0,
) -> tuple[list[str], list[float]]:
    """Return per-cell labels/confidences for a BookMap.

    Output arrays are index-based for cells 1..12 (i.e., index 0 is cell 1).
    """
    if confidence_threshold < 0.0 or confidence_threshold > 1.0:
        raise ValueError("confidence_threshold must be in [0, 1]")

    best_label: list[str | None] = [None] * 12
    best_score: list[float] = [-1.0] * 12

    for det in detections:
        cell_id = map_point_to_cell_id(det.cx, det.cy, regions)
        if cell_id is None:
            continue

        label = _normalize_label(det.class_id)
        score = float(det.score)
        if score < confidence_threshold:
            label = UNKNOWN_LABEL

        idx = cell_id - 1
        if score > best_score[idx]:
            best_score[idx] = score
            best_label[idx] = label

    labels: list[str] = []
    confidences: list[float] = []
    for i in range(12):
        if best_label[i] is None:
            labels.append(EMPTY_LABEL)
            confidences.append(default_empty_confidence)
            continue

        labels.append(best_label[i])
        confidences.append(best_score[i])

    return labels, confidences


def to_book_type_values(
    labels: list[str],
    enum_mapping: dict[str, int],
) -> list[int]:
    """Convert normalized labels to BookMap enum values."""
    values: list[int] = []
    for label in labels:
        values.append(enum_mapping.get(label, enum_mapping[UNKNOWN_LABEL]))
    return values


def detection_from_vision_msg(det: Any) -> DetectionObservation | None:
    """Extract class/score/center from a vision_msgs Detection2D-like object."""
    if not det.results:
        return None

    top_result = max(det.results, key=lambda r: r.hypothesis.score)
    return DetectionObservation(
        cx=float(det.bbox.center.position.x),
        cy=float(det.bbox.center.position.y),
        class_id=top_result.hypothesis.class_id,
        score=float(top_result.hypothesis.score),
    )
