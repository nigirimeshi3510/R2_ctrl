"""Team-specific cell-number mapping helpers."""

from __future__ import annotations

RED = "red"
BLUE = "blue"

# Blue side numbering is a left-right mirrored view of red side numbering.
BLUE_TO_RED_CELL_ID = {
    1: 3,
    2: 2,
    3: 1,
    4: 6,
    5: 5,
    6: 4,
    7: 9,
    8: 8,
    9: 7,
    10: 12,
    11: 11,
    12: 10,
}


def normalize_team_color(team_color: str) -> str:
    value = team_color.strip().lower()
    if value not in {RED, BLUE}:
        raise ValueError(f"team_color must be 'red' or 'blue', got: {team_color}")
    return value


def to_canonical_cell_id(cell_id: int, team_color: str) -> int:
    team = normalize_team_color(team_color)
    if cell_id == 0:
        return 0
    if cell_id < 1 or cell_id > 12:
        raise ValueError(f"cell_id must be in [0, 12], got: {cell_id}")
    if team == RED:
        return cell_id
    return BLUE_TO_RED_CELL_ID[cell_id]


def from_canonical_cell_id(cell_id: int, team_color: str) -> int:
    # Mapping is self-inverse for this left-right mirror transform.
    return to_canonical_cell_id(cell_id, team_color)


def to_canonical_book_types(book_types: list[int], team_color: str) -> list[int]:
    if len(book_types) != 12:
        raise ValueError(f"book_types must be len 12, got: {len(book_types)}")
    team = normalize_team_color(team_color)
    if team == RED:
        return list(book_types)

    out = [0] * 12
    for local_idx, book_type in enumerate(book_types, start=1):
        canonical_id = BLUE_TO_RED_CELL_ID[local_idx]
        out[canonical_id - 1] = int(book_type)
    return out


def to_canonical_cleared_mask(cleared_mask: int, team_color: str) -> int:
    team = normalize_team_color(team_color)
    if team == RED:
        return int(cleared_mask)

    out = 0
    for local_cell in range(1, 13):
        local_bit = 1 << (local_cell - 1)
        if int(cleared_mask) & local_bit:
            canonical_cell = BLUE_TO_RED_CELL_ID[local_cell]
            out |= 1 << (canonical_cell - 1)
    return out


def from_canonical_plan_target(target_cell_id: int, team_color: str) -> int:
    if target_cell_id <= 0:
        return target_cell_id
    return from_canonical_cell_id(target_cell_id, team_color)

