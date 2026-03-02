import pytest

from robocon_interfaces.msg import BookMap

from robocon_perception.bookmap_core import EMPTY_LABEL, UNKNOWN_LABEL
from robocon_perception.bookmap_viz_core import (
    color_for_label,
    grid_pose_for_cell,
    label_from_book_type,
    marker_text,
)


def test_front_row_is_10_11_12():
    pose10 = grid_pose_for_cell(10, 0.0, 0.0, 1.0, 1.0)
    pose11 = grid_pose_for_cell(11, 0.0, 0.0, 1.0, 1.0)
    pose12 = grid_pose_for_cell(12, 0.0, 0.0, 1.0, 1.0)
    pose7 = grid_pose_for_cell(7, 0.0, 0.0, 1.0, 1.0)

    assert pose10.y == pytest.approx(0.0)
    assert pose11.y == pytest.approx(0.0)
    assert pose12.y == pytest.approx(0.0)
    assert pose7.y > pose10.y


def test_color_mapping_has_expected_categories():
    empty = color_for_label(EMPTY_LABEL, 0.5)
    unknown = color_for_label(UNKNOWN_LABEL, 0.8)

    assert empty.a == pytest.approx(0.5)
    assert unknown.a == pytest.approx(0.8)
    assert unknown.r > 0.9


def test_label_from_book_type_unknown_fallback():
    enum_mapping = {
        EMPTY_LABEL: BookMap.EMPTY,
        "R2": BookMap.R2,
        "R1": BookMap.R1,
        "FAKE": BookMap.FAKE,
        UNKNOWN_LABEL: BookMap.UNKNOWN,
    }

    assert label_from_book_type(BookMap.EMPTY, enum_mapping) == EMPTY_LABEL
    assert label_from_book_type(255, enum_mapping) == UNKNOWN_LABEL


def test_marker_text_contains_cell_label_confidence():
    text = marker_text(10, "R2", 0.9123)
    assert "cell=10" in text
    assert "R2" in text
    assert "conf=0.91" in text
