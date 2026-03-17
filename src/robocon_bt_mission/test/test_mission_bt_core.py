from robocon_bt_mission.mission_bt_core import (
    ACTION_EXIT,
    ACTION_MOVE,
    ACTION_PICK,
    NodeStatus,
    PlanSnapshot,
    PlanStepSnapshot,
    SimplePlumMissionBt,
)


def _make_tree() -> SimplePlumMissionBt:
    tree = SimplePlumMissionBt(max_retries=1)
    tree.update_book_map((1, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0))
    tree.update_cell_state(current_cell_id=0, carry_r2=0, cleared_mask=0, loc_mode="FLAT")
    return tree


def test_observe_waits_for_topics():
    tree = SimplePlumMissionBt(max_retries=1)
    result = tree.tick()
    assert result.status == NodeStatus.RUNNING
    assert result.active_node == "ObserveAllBooksFromCorridor"


def test_execute_emits_command_and_updates_state():
    tree = _make_tree()
    tree.update_plan(
        PlanSnapshot(
            steps=(
                PlanStepSnapshot(action_type=ACTION_PICK, target_cell_id=1),
                PlanStepSnapshot(action_type=ACTION_MOVE, target_cell_id=1),
                PlanStepSnapshot(action_type=ACTION_MOVE, target_cell_id=4),
                PlanStepSnapshot(action_type=ACTION_MOVE, target_cell_id=7),
                PlanStepSnapshot(action_type=ACTION_MOVE, target_cell_id=10),
                PlanStepSnapshot(action_type=ACTION_EXIT, target_cell_id=-1),
            )
        )
    )

    tree.tick()
    tree.tick()

    first = tree.tick()
    assert first.command is not None
    assert first.command.action_type == ACTION_PICK
    tree.complete_action(True, "")
    assert tree.blackboard.cell_state is not None
    assert tree.blackboard.cell_state.carry_r2 == 1

    while True:
        result = tree.tick()
        if result.command is not None:
            tree.complete_action(True, "")
            continue
        if result.status == NodeStatus.SUCCESS:
            break

    assert tree.blackboard.cell_state is not None
    assert tree.blackboard.cell_state.current_cell_id == 10


def test_empty_plan_fails_in_compute():
    tree = _make_tree()
    tree.tick()
    tree.update_plan(PlanSnapshot(steps=()))
    result = tree.tick()
    assert result.status == NodeStatus.FAILURE
    assert "empty plan" in result.message


def test_action_failure_retries_once_then_recovers():
    tree = _make_tree()
    plan = PlanSnapshot(
        steps=(
            PlanStepSnapshot(action_type=ACTION_PICK, target_cell_id=1),
            PlanStepSnapshot(action_type=ACTION_MOVE, target_cell_id=1),
            PlanStepSnapshot(action_type=ACTION_MOVE, target_cell_id=4),
            PlanStepSnapshot(action_type=ACTION_MOVE, target_cell_id=7),
            PlanStepSnapshot(action_type=ACTION_MOVE, target_cell_id=10),
            PlanStepSnapshot(action_type=ACTION_EXIT, target_cell_id=-1),
        )
    )
    tree.update_plan(plan)

    tree.tick()
    tree.tick()
    result = tree.tick()
    assert result.command is not None
    tree.complete_action(False, "simulated failure")
    assert tree.phase == "observe"
    assert tree.blackboard.retry_count == 1

    tree.update_plan(plan)
    while True:
        result = tree.tick()
        if result.command is not None:
            tree.complete_action(True, "")
            continue
        if result.status == NodeStatus.SUCCESS:
            break

    assert tree.blackboard.last_error == ""


def test_second_action_failure_is_terminal():
    tree = _make_tree()
    tree.update_plan(
        PlanSnapshot(
            steps=(
                PlanStepSnapshot(action_type=ACTION_PICK, target_cell_id=1),
                PlanStepSnapshot(action_type=ACTION_MOVE, target_cell_id=1),
            )
        )
    )

    tree.tick()
    tree.tick()
    first = tree.tick()
    assert first.command is not None
    tree.complete_action(False, "first failure")
    tree.update_plan(
        PlanSnapshot(
            steps=(
                PlanStepSnapshot(action_type=ACTION_PICK, target_cell_id=1),
                PlanStepSnapshot(action_type=ACTION_MOVE, target_cell_id=1),
            )
        )
    )
    tree.tick()
    tree.tick()
    second = tree.tick()
    assert second.command is not None
    tree.complete_action(False, "second failure")

    final = tree.tick()
    assert final.status == NodeStatus.FAILURE
    assert tree.blackboard.retry_count == 1
