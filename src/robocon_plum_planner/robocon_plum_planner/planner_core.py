"""Core discrete planner for plum forest."""

from __future__ import annotations

from dataclasses import dataclass
import heapq
import math


ACTION_MOVE = 0
ACTION_PICK = 1
ACTION_EXIT = 2

CORRIDOR_CELL_ID = 0
EXIT_CELLS = {10, 11, 12}
CORRIDOR_NEIGHBORS = (1, 2, 3)

# Height information is recorded for Task 6 climb primitives.
CELL_HEIGHT_MM = {
    1: 200,
    3: 200,
    5: 200,
    7: 200,
    9: 200,
    11: 200,
    6: 400,
    8: 400,
}


@dataclass(frozen=True)
class PlanStep:
    action_type: int
    target_cell_id: int


@dataclass(frozen=True)
class PlannerConfig:
    step_move_cost_sec: float = 5.0
    pick_cost_sec: float = 4.0
    exit_cost_sec: float = 0.0


@dataclass(frozen=True)
class PlannerInput:
    book_types: tuple[int, ...]
    current_cell_id: int
    carry_r2: int
    cleared_mask: int


@dataclass(frozen=True)
class PlannerResult:
    steps: tuple[PlanStep, ...]
    estimated_cost_sec: float
    is_fallback_plan: bool


@dataclass(frozen=True)
class SearchState:
    pos: int
    carry_r2: int
    cleared_mask: int


def _bit_for(cell_id: int) -> int:
    return 1 << (cell_id - 1)


def _is_cleared(cleared_mask: int, cell_id: int) -> bool:
    return (cleared_mask & _bit_for(cell_id)) != 0


def _grid_pos(cell_id: int) -> tuple[int, int]:
    # Canonical red-side numbering: row-major, back row = 1,2,3.
    zero = cell_id - 1
    return (zero // 3, zero % 3)


def build_adjacency() -> dict[int, tuple[int, ...]]:
    adj: dict[int, tuple[int, ...]] = {}
    for cell_id in range(1, 13):
        row, col = _grid_pos(cell_id)
        candidates: list[int] = []
        for dr, dc in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
            rr = row + dr
            cc = col + dc
            if rr < 0 or rr > 3 or cc < 0 or cc > 2:
                continue
            candidates.append((rr * 3) + cc + 1)
        adj[cell_id] = tuple(sorted(candidates))
    adj[CORRIDOR_CELL_ID] = CORRIDOR_NEIGHBORS
    return adj


ADJACENCY = build_adjacency()


def _walkable(book_types: tuple[int, ...], cleared_mask: int, cell_id: int) -> bool:
    book_type = int(book_types[cell_id - 1])
    # BookMap enum: EMPTY=0, R2=1, R1=2, FAKE=3, UNKNOWN=4
    if book_type == 0:
        return True
    if book_type == 3:
        return False
    if book_type == 4:
        return False
    return _is_cleared(cleared_mask, cell_id)


def _can_pick_r2(book_types: tuple[int, ...], cleared_mask: int, target_cell_id: int) -> bool:
    if _is_cleared(cleared_mask, target_cell_id):
        return False
    return int(book_types[target_cell_id - 1]) == 1


def _front_row_has_r2(book_types: tuple[int, ...], cleared_mask: int) -> bool:
    for cell_id in CORRIDOR_NEIGHBORS:
        if _can_pick_r2(book_types, cleared_mask, cell_id):
            return True
    return False


def _action_code(step: PlanStep) -> int:
    if step.action_type == ACTION_MOVE:
        return 100 + step.target_cell_id
    if step.action_type == ACTION_PICK:
        return 200 + step.target_cell_id
    return 300


def _neighbors(
    state: SearchState,
    planner_input: PlannerInput,
    cfg: PlannerConfig,
) -> list[tuple[SearchState, PlanStep, float]]:
    out: list[tuple[SearchState, PlanStep, float]] = []
    book_types = planner_input.book_types
    special_first_pick = state.carry_r2 == 0 and _front_row_has_r2(book_types, state.cleared_mask)

    # MOVE actions
    for to_cell in ADJACENCY[state.pos]:
        if not _walkable(book_types, state.cleared_mask, to_cell):
            continue
        out.append(
            (
                SearchState(pos=to_cell, carry_r2=state.carry_r2, cleared_mask=state.cleared_mask),
                PlanStep(action_type=ACTION_MOVE, target_cell_id=to_cell),
                cfg.step_move_cost_sec,
            )
        )

    # PICK actions
    for target_cell in ADJACENCY[state.pos]:
        if not _can_pick_r2(book_types, state.cleared_mask, target_cell):
            continue
        if special_first_pick and state.pos != CORRIDOR_CELL_ID:
            continue
        next_mask = state.cleared_mask | _bit_for(target_cell)
        out.append(
            (
                SearchState(
                    pos=state.pos,
                    carry_r2=min(2, state.carry_r2 + 1),
                    cleared_mask=next_mask,
                ),
                PlanStep(action_type=ACTION_PICK, target_cell_id=target_cell),
                cfg.pick_cost_sec,
            )
        )

    return out


def _search_for_target_carry(
    planner_input: PlannerInput,
    cfg: PlannerConfig,
    target_carry: int,
) -> tuple[tuple[PlanStep, ...], float] | None:
    start = SearchState(
        pos=planner_input.current_cell_id,
        carry_r2=planner_input.carry_r2,
        cleared_mask=planner_input.cleared_mask,
    )

    if start.pos not in ADJACENCY:
        raise ValueError(f"current_cell_id must be in [0, 12], got: {start.pos}")
    if len(planner_input.book_types) != 12:
        raise ValueError("book_types must have length 12")

    start_sig: tuple[int, ...] = ()
    pq: list[tuple[float, int, tuple[int, ...], SearchState, tuple[PlanStep, ...]]] = [
        (0.0, 0, start_sig, start, ())
    ]
    best: dict[SearchState, tuple[float, int, tuple[int, ...]]] = {start: (0.0, 0, start_sig)}

    while pq:
        cost, move_count, sig, state, path = heapq.heappop(pq)
        if best.get(state) != (cost, move_count, sig):
            continue

        if state.pos in EXIT_CELLS and state.carry_r2 >= max(1, target_carry):
            final_path = path + (PlanStep(action_type=ACTION_EXIT, target_cell_id=-1),)
            return final_path, cost + cfg.exit_cost_sec

        for next_state, step, delta in _neighbors(state, planner_input, cfg):
            next_cost = cost + delta
            next_move_count = move_count + (1 if step.action_type == ACTION_MOVE else 0)
            next_sig = sig + (_action_code(step),)
            next_path = path + (step,)
            key = (next_cost, next_move_count, next_sig)

            current_best = best.get(next_state)
            if current_best is not None and current_best <= key:
                continue

            best[next_state] = key
            heapq.heappush(pq, (next_cost, next_move_count, next_sig, next_state, next_path))

    return None


def plan_with_fallback(
    planner_input: PlannerInput,
    cfg: PlannerConfig,
    allow_fallback_to_one: bool = True,
) -> PlannerResult | None:
    first = _search_for_target_carry(planner_input, cfg, target_carry=2)
    if first is not None:
        steps, cost = first
        return PlannerResult(steps=steps, estimated_cost_sec=cost, is_fallback_plan=False)

    if allow_fallback_to_one:
        second = _search_for_target_carry(planner_input, cfg, target_carry=1)
        if second is not None:
            steps, cost = second
            return PlannerResult(steps=steps, estimated_cost_sec=cost, is_fallback_plan=True)

    return None


def is_finite_cost(cost: float) -> bool:
    return math.isfinite(float(cost))
