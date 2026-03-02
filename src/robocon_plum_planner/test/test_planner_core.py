import pytest

from robocon_plum_planner.planner_core import (
    ACTION_EXIT,
    ACTION_MOVE,
    ACTION_PICK,
    PlannerConfig,
    PlannerInput,
    plan_with_fallback,
)


def _cfg() -> PlannerConfig:
    return PlannerConfig(step_move_cost_sec=5.0, pick_cost_sec=4.0, exit_cost_sec=0.0)


def _empty_map() -> list[int]:
    return [0] * 12


def test_pick_is_adjacent_only():
    book = _empty_map()
    book[8 - 1] = 1  # R2 at cell 8 (adjacent from cell 5)
    planner_input = PlannerInput(
        book_types=tuple(book),
        current_cell_id=5,
        carry_r2=0,
        cleared_mask=0,
    )

    result = plan_with_fallback(planner_input, _cfg(), allow_fallback_to_one=True)
    assert result is not None
    pick_targets = [s.target_cell_id for s in result.steps if s.action_type == ACTION_PICK]
    assert all(t in {2, 4, 6, 8} for t in pick_targets)


def test_does_not_move_into_uncleared_book_cells():
    # R1/R2/FAKE/UNKNOWN cells must not be traversed unless cleared.
    book = _empty_map()
    book[8 - 1] = 2
    book[7 - 1] = 3
    book[6 - 1] = 4
    book[5 - 1] = 1
    planner_input = PlannerInput(
        book_types=tuple(book),
        current_cell_id=10,
        carry_r2=1,
        cleared_mask=0,
    )

    result = plan_with_fallback(planner_input, _cfg(), allow_fallback_to_one=True)
    assert result is not None
    move_targets = [s.target_cell_id for s in result.steps if s.action_type == ACTION_MOVE]
    assert 6 not in move_targets
    assert 7 not in move_targets
    assert 8 not in move_targets
    assert 5 not in move_targets


def test_exit_only_from_10_11_12_and_carry_at_least_one():
    planner_input = PlannerInput(
        book_types=tuple(_empty_map()),
        current_cell_id=9,
        carry_r2=0,
        cleared_mask=0,
    )
    result = plan_with_fallback(planner_input, _cfg(), allow_fallback_to_one=True)
    assert result is None


def test_first_pick_from_corridor_when_front_row_has_r2():
    book = _empty_map()
    book[1 - 1] = 1
    planner_input = PlannerInput(
        book_types=tuple(book),
        current_cell_id=2,
        carry_r2=0,
        cleared_mask=0,
    )
    result = plan_with_fallback(planner_input, _cfg(), allow_fallback_to_one=True)
    assert result is None


def test_fallback_to_one_when_two_books_unreachable():
    book = _empty_map()
    book[2 - 1] = 1
    planner_input = PlannerInput(
        book_types=tuple(book),
        current_cell_id=0,
        carry_r2=0,
        cleared_mask=0,
    )
    result = plan_with_fallback(planner_input, _cfg(), allow_fallback_to_one=True)
    assert result is not None
    assert result.is_fallback_plan is True
    assert any(s.action_type == ACTION_PICK for s in result.steps)
    assert result.steps[-1].action_type == ACTION_EXIT


def test_two_book_plan_preferred_when_available():
    book = _empty_map()
    book[2 - 1] = 1
    book[1 - 1] = 1
    planner_input = PlannerInput(
        book_types=tuple(book),
        current_cell_id=0,
        carry_r2=0,
        cleared_mask=0,
    )
    result = plan_with_fallback(planner_input, _cfg(), allow_fallback_to_one=True)
    assert result is not None
    assert result.is_fallback_plan is False
    pick_count = len([s for s in result.steps if s.action_type == ACTION_PICK])
    assert pick_count >= 2
    assert result.steps[-1].action_type == ACTION_EXIT


def test_deterministic_plan_on_same_input():
    book = _empty_map()
    book[1 - 1] = 1
    book[2 - 1] = 1
    planner_input = PlannerInput(
        book_types=tuple(book),
        current_cell_id=0,
        carry_r2=0,
        cleared_mask=0,
    )

    a = plan_with_fallback(planner_input, _cfg(), allow_fallback_to_one=True)
    b = plan_with_fallback(planner_input, _cfg(), allow_fallback_to_one=True)
    assert a == b


def test_invalid_book_map_length_raises():
    planner_input = PlannerInput(
        book_types=(0, 1),
        current_cell_id=0,
        carry_r2=0,
        cleared_mask=0,
    )
    with pytest.raises(ValueError):
        plan_with_fallback(planner_input, _cfg(), allow_fallback_to_one=True)
