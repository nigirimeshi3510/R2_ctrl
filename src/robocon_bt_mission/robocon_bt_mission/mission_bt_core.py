"""Pure-Python core for the simple plum mission behavior tree."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum


ACTION_MOVE = 0
ACTION_PICK = 1
ACTION_EXIT = 2

EXIT_CELLS = {10, 11, 12}


class NodeStatus(str, Enum):
    """Minimal BT node status."""

    IDLE = "IDLE"
    RUNNING = "RUNNING"
    SUCCESS = "SUCCESS"
    FAILURE = "FAILURE"


@dataclass(frozen=True)
class BookMapSnapshot:
    """Minimal book map view required by the trial BT."""

    book_types: tuple[int, ...]


@dataclass
class CellStateSnapshot:
    """Mutable cell state mirrored on the blackboard."""

    current_cell_id: int
    carry_r2: int
    cleared_mask: int
    loc_mode: str


@dataclass(frozen=True)
class PlanStepSnapshot:
    """Action step consumed by ExecutePlumPlan."""

    action_type: int
    target_cell_id: int


@dataclass(frozen=True)
class PlanSnapshot:
    """Planner result snapshot copied onto the blackboard."""

    steps: tuple[PlanStepSnapshot, ...]
    is_fallback_plan: bool = False
    estimated_cost_sec: float = 0.0


@dataclass(frozen=True)
class ActionCommand:
    """Command emitted by the BT executor."""

    action_type: int
    from_cell_id: int
    target_cell_id: int


@dataclass
class MissionBlackboard:
    """Shared blackboard for the simple plum BT."""

    book_map: BookMapSnapshot | None = None
    cell_state: CellStateSnapshot | None = None
    latest_plan: PlanSnapshot | None = None
    plan: PlanSnapshot | None = None
    carry: int = 0
    loc_mode: str = ""
    retry_count: int = 0
    last_error: str = ""
    mission_phase: str = "ObserveAllBooksFromCorridor"


@dataclass(frozen=True)
class MissionTickResult:
    """Result of a BT tick."""

    status: NodeStatus
    active_node: str
    command: ActionCommand | None = None
    message: str = ""


@dataclass
class _ExecutionState:
    current_step_index: int = 0
    waiting_command: ActionCommand | None = None


class SimplePlumMissionBt:
    """Simple Sequence+Recovery BT for the plum phase."""

    def __init__(self, max_retries: int = 1) -> None:
        self._max_retries = max_retries
        self.blackboard = MissionBlackboard()
        self._phase = "observe"
        self._exec = _ExecutionState()

    @property
    def phase(self) -> str:
        return self._phase

    def update_book_map(self, book_types: tuple[int, ...]) -> None:
        self.blackboard.book_map = BookMapSnapshot(book_types=book_types)

    def update_cell_state(
        self,
        current_cell_id: int,
        carry_r2: int,
        cleared_mask: int,
        loc_mode: str,
    ) -> None:
        self.blackboard.cell_state = CellStateSnapshot(
            current_cell_id=current_cell_id,
            carry_r2=carry_r2,
            cleared_mask=cleared_mask,
            loc_mode=loc_mode,
        )
        self._sync_blackboard_from_state()

    def update_plan(self, plan: PlanSnapshot) -> None:
        self.blackboard.latest_plan = plan

    def tick(self) -> MissionTickResult:
        if self._phase == "success":
            return MissionTickResult(NodeStatus.SUCCESS, "MissionComplete", message="mission completed")

        if self._phase == "failure":
            return MissionTickResult(
                NodeStatus.FAILURE,
                self.blackboard.mission_phase,
                message=self.blackboard.last_error or "mission failed",
            )

        if self._phase == "observe":
            self.blackboard.mission_phase = "ObserveAllBooksFromCorridor"
            if self.blackboard.book_map is None or self.blackboard.cell_state is None:
                return MissionTickResult(
                    NodeStatus.RUNNING,
                    self.blackboard.mission_phase,
                    message="waiting for /book_map and /cell_state",
                )
            self._sync_blackboard_from_state()
            self._phase = "plan"
            return MissionTickResult(NodeStatus.RUNNING, self.blackboard.mission_phase, message="observation ready")

        if self._phase == "plan":
            self.blackboard.mission_phase = "ComputePlumPlan"
            plan = self.blackboard.latest_plan
            if plan is None:
                return MissionTickResult(
                    NodeStatus.RUNNING,
                    self.blackboard.mission_phase,
                    message="waiting for /plum_plan",
                )
            if not plan.steps:
                return self._set_failure("planner returned an empty plan")
            self.blackboard.plan = plan
            self._exec = _ExecutionState()
            self._phase = "execute"
            return MissionTickResult(NodeStatus.RUNNING, self.blackboard.mission_phase, message="plan accepted")

        if self._phase == "execute":
            self.blackboard.mission_phase = "ExecutePlumPlan"
            plan = self.blackboard.plan
            if plan is None:
                return self._set_failure("plan missing before execution")
            if self._exec.waiting_command is not None:
                return MissionTickResult(
                    NodeStatus.RUNNING,
                    self.blackboard.mission_phase,
                    message="waiting for action result",
                )
            if self._exec.current_step_index >= len(plan.steps):
                self._phase = "exit"
                return MissionTickResult(NodeStatus.RUNNING, self.blackboard.mission_phase, message="steps exhausted")

            step = plan.steps[self._exec.current_step_index]
            if step.action_type == ACTION_EXIT:
                self._exec.current_step_index += 1
                self._phase = "exit"
                return MissionTickResult(NodeStatus.RUNNING, self.blackboard.mission_phase, message="exit step reached")

            cell_state = self.blackboard.cell_state
            if cell_state is None:
                return self._set_failure("cell_state missing during execution")

            command = ActionCommand(
                action_type=step.action_type,
                from_cell_id=cell_state.current_cell_id,
                target_cell_id=step.target_cell_id,
            )
            self._exec.waiting_command = command
            return MissionTickResult(
                NodeStatus.RUNNING,
                self.blackboard.mission_phase,
                command=command,
                message="dispatch action",
            )

        if self._phase == "exit":
            self.blackboard.mission_phase = "ExitPlumForest"
            state = self.blackboard.cell_state
            if state is None:
                return self._set_failure("cell_state missing during exit")
            if state.current_cell_id in EXIT_CELLS and state.carry_r2 >= 1:
                self._phase = "success"
                return MissionTickResult(NodeStatus.SUCCESS, self.blackboard.mission_phase, message="exit confirmed")
            return self._set_failure("robot is not ready to exit")

        return self._set_failure(f"unknown phase: {self._phase}")

    def complete_action(self, success: bool, error_message: str = "") -> None:
        """Feed an action completion result back into the tree."""

        command = self._exec.waiting_command
        if command is None:
            raise RuntimeError("complete_action() called without an active command")

        self._exec.waiting_command = None
        if success:
            self._apply_successful_command(command)
            self.blackboard.last_error = ""
            self._exec.current_step_index += 1
            if self.blackboard.plan is not None and self._exec.current_step_index >= len(self.blackboard.plan.steps):
                self._phase = "exit"
            else:
                self._phase = "execute"
            return

        self.blackboard.last_error = error_message or "action failed"
        self.blackboard.plan = None
        self._exec = _ExecutionState()
        if self.blackboard.retry_count < self._max_retries:
            self.blackboard.retry_count += 1
            self._phase = "observe"
            return
        self._phase = "failure"

    def _apply_successful_command(self, command: ActionCommand) -> None:
        state = self.blackboard.cell_state
        if state is None:
            raise RuntimeError("cell_state missing while applying command")

        if command.action_type == ACTION_MOVE:
            state.current_cell_id = command.target_cell_id
        elif command.action_type == ACTION_PICK:
            state.cleared_mask |= 1 << (command.target_cell_id - 1)
            state.carry_r2 = min(2, state.carry_r2 + 1)
        else:
            raise RuntimeError(f"unsupported action type: {command.action_type}")

        self._sync_blackboard_from_state()

    def _set_failure(self, message: str) -> MissionTickResult:
        self.blackboard.last_error = message
        self._phase = "failure"
        return MissionTickResult(NodeStatus.FAILURE, self.blackboard.mission_phase, message=message)

    def _sync_blackboard_from_state(self) -> None:
        state = self.blackboard.cell_state
        if state is None:
            return
        self.blackboard.carry = state.carry_r2
        self.blackboard.loc_mode = state.loc_mode
