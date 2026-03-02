from robocon_plum_planner.team_mapping import (
    from_canonical_cell_id,
    to_canonical_book_types,
    to_canonical_cell_id,
    to_canonical_cleared_mask,
)


def test_blue_cell_mapping_is_mirror():
    assert to_canonical_cell_id(1, "blue") == 3
    assert to_canonical_cell_id(4, "blue") == 6
    assert to_canonical_cell_id(10, "blue") == 12
    assert from_canonical_cell_id(12, "blue") == 10


def test_blue_book_types_mapping_moves_values_to_canonical_cells():
    book_types_blue_local = [0] * 12
    book_types_blue_local[0] = 1
    out = to_canonical_book_types(book_types_blue_local, "blue")
    assert out[2] == 1  # canonical cell 3


def test_blue_cleared_mask_mapping():
    mask_local = 1 << (10 - 1)  # local cell 10
    out = to_canonical_cleared_mask(mask_local, "blue")
    expected = 1 << (12 - 1)  # canonical cell 12
    assert out == expected

