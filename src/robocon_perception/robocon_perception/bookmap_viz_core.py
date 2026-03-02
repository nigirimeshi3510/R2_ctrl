"""Core helpers for visualizing BookMap as RViz markers."""

from __future__ import annotations

from dataclasses import dataclass

from std_msgs.msg import ColorRGBA

from robocon_perception.bookmap_core import (
    EMPTY_LABEL,
    FAKE_LABEL,
    R1_LABEL,
    R2_LABEL,
    UNKNOWN_LABEL,
)


CELL_ID_TO_GRID_FRONT = {
    10: (0, 0),
    11: (0, 1),
    12: (0, 2),
    7: (1, 0),
    8: (1, 1),
    9: (1, 2),
    4: (2, 0),
    5: (2, 1),
    6: (2, 2),
    1: (3, 0),
    2: (3, 1),
    3: (3, 2),
}


@dataclass(frozen=True)
class GridPose:
    x: float
    y: float


def label_from_book_type(book_type: int, enum_mapping: dict[str, int]) -> str:
    if book_type == enum_mapping[EMPTY_LABEL]:
        return EMPTY_LABEL
    if book_type == enum_mapping[R2_LABEL]:
        return R2_LABEL
    if book_type == enum_mapping[R1_LABEL]:
        return R1_LABEL
    if book_type == enum_mapping[FAKE_LABEL]:
        return FAKE_LABEL
    return UNKNOWN_LABEL


def color_for_label(label: str, alpha: float) -> ColorRGBA:
    color = ColorRGBA()
    color.a = float(alpha)

    if label == R2_LABEL:
        color.r, color.g, color.b = 0.1, 0.8, 0.1
    elif label == R1_LABEL:
        color.r, color.g, color.b = 0.2, 0.4, 0.95
    elif label == FAKE_LABEL:
        color.r, color.g, color.b = 0.95, 0.2, 0.2
    elif label == UNKNOWN_LABEL:
        color.r, color.g, color.b = 0.95, 0.85, 0.2
    else:
        color.r, color.g, color.b = 0.7, 0.7, 0.7

    return color


def grid_pose_for_cell(
    cell_id: int,
    origin_x: float,
    origin_y: float,
    cell_size_x: float,
    cell_size_y: float,
) -> GridPose:
    row_from_front, col = CELL_ID_TO_GRID_FRONT[cell_id]
    return GridPose(
        x=origin_x + (col * cell_size_x),
        y=origin_y + (row_from_front * cell_size_y),
    )


def marker_text(cell_id: int, label: str, confidence: float) -> str:
    return f"cell={cell_id} {label} conf={confidence:.2f}"
