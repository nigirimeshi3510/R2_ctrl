"""Mock world node for simple plum BT end-to-end tests."""

from __future__ import annotations

from dataclasses import dataclass

import rclpy
from rclpy.action import ActionServer
from rclpy.node import Node

from robocon_interfaces.action import MoveCell, PickAdjacentBook
from robocon_interfaces.msg import BookMap, CellState


@dataclass
class MockWorldState:
    current_cell_id: int
    carry_r2: int
    cleared_mask: int
    loc_mode: str


def _build_adjacency() -> dict[int, tuple[int, ...]]:
    adjacency: dict[int, tuple[int, ...]] = {0: (1, 2, 3)}
    for cell_id in range(1, 13):
        row = (cell_id - 1) // 3
        col = (cell_id - 1) % 3
        candidates: list[int] = []
        for dr, dc in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
            rr = row + dr
            cc = col + dc
            if rr < 0 or rr > 3 or cc < 0 or cc > 2:
                continue
            candidates.append((rr * 3) + cc + 1)
        adjacency[cell_id] = tuple(sorted(candidates))
    return adjacency


ADJACENCY = _build_adjacency()


class MockPlumWorldNode(Node):
    """Publishes a fixed BookMap and simulates Move/Pick actions."""

    def __init__(self) -> None:
        super().__init__("mock_plum_world")

        self.declare_parameter("book_types", [1, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0])
        self.declare_parameter("publish_period_sec", 0.2)
        self.declare_parameter("current_cell_id", 0)
        self.declare_parameter("carry_r2", 0)
        self.declare_parameter("cleared_mask", 0)
        self.declare_parameter("loc_mode", "FLAT")
        self.declare_parameter("fail_action_type", "")
        self.declare_parameter("fail_step_index", -1)
        self.declare_parameter("fail_once", True)

        self._book_types = [int(v) for v in self.get_parameter("book_types").value]
        self._state = MockWorldState(
            current_cell_id=int(self.get_parameter("current_cell_id").value),
            carry_r2=int(self.get_parameter("carry_r2").value),
            cleared_mask=int(self.get_parameter("cleared_mask").value),
            loc_mode=str(self.get_parameter("loc_mode").value),
        )
        self._fail_action_type = str(self.get_parameter("fail_action_type").value).strip().lower()
        self._fail_step_index = int(self.get_parameter("fail_step_index").value)
        self._fail_once = bool(self.get_parameter("fail_once").value)
        self._action_counter = 0
        self._failure_consumed = False

        self._book_pub = self.create_publisher(BookMap, "/book_map", 10)
        self._cell_pub = self.create_publisher(CellState, "/cell_state", 10)
        self._timer = self.create_timer(float(self.get_parameter("publish_period_sec").value), self._publish_state)

        self._move_server = ActionServer(self, MoveCell, "/move_cell", execute_callback=self._execute_move)
        self._pick_server = ActionServer(
            self,
            PickAdjacentBook,
            "/pick_adjacent_book",
            execute_callback=self._execute_pick,
        )

        self.get_logger().info(
            "mock_plum_world started "
            f"cell={self._state.current_cell_id} fail_action_type={self._fail_action_type!r} "
            f"fail_step_index={self._fail_step_index}"
        )

    def _publish_state(self) -> None:
        book_msg = BookMap()
        book_msg.header.stamp = self.get_clock().now().to_msg()
        book_msg.header.frame_id = "map"
        book_msg.book_type = list(self._book_types)
        book_msg.confidence = [1.0] * 12
        self._book_pub.publish(book_msg)

        cell_msg = CellState()
        cell_msg.header.stamp = self.get_clock().now().to_msg()
        cell_msg.header.frame_id = "map"
        cell_msg.current_cell_id = int(self._state.current_cell_id)
        cell_msg.carry_r2 = int(self._state.carry_r2)
        cell_msg.cleared_mask = int(self._state.cleared_mask)
        cell_msg.loc_mode = str(self._state.loc_mode)
        self._cell_pub.publish(cell_msg)

    def _execute_move(self, goal_handle) -> MoveCell.Result:
        result = MoveCell.Result()
        step_index = self._next_step_index()

        if self._should_fail("move", step_index):
            goal_handle.abort()
            result.success = False
            result.error_code = 1
            result.debug = "Injected move failure"
            return result

        goal = goal_handle.request
        if int(goal.from_cell_id) != self._state.current_cell_id:
            goal_handle.abort()
            result.success = False
            result.error_code = 2
            result.debug = (
                f"Current cell mismatch: expected {self._state.current_cell_id}, got {int(goal.from_cell_id)}"
            )
            return result

        if int(goal.to_cell_id) not in ADJACENCY.get(self._state.current_cell_id, ()):
            goal_handle.abort()
            result.success = False
            result.error_code = 3
            result.debug = f"Cell {int(goal.to_cell_id)} is not adjacent to {self._state.current_cell_id}"
            return result

        feedback = MoveCell.Feedback()
        feedback.state = "MOVING"
        feedback.progress = 1.0
        goal_handle.publish_feedback(feedback)

        self._state.current_cell_id = int(goal.to_cell_id)
        goal_handle.succeed()
        result.success = True
        result.error_code = 0
        result.debug = f"Moved to cell {self._state.current_cell_id}"
        self._publish_state()
        return result

    def _execute_pick(self, goal_handle) -> PickAdjacentBook.Result:
        result = PickAdjacentBook.Result()
        step_index = self._next_step_index()

        if self._should_fail("pick", step_index):
            goal_handle.abort()
            result.success = False
            result.error_code = 1
            result.debug = "Injected pick failure"
            return result

        target_cell_id = int(goal_handle.request.target_cell_id)
        if target_cell_id not in ADJACENCY.get(self._state.current_cell_id, ()):
            goal_handle.abort()
            result.success = False
            result.error_code = 2
            result.debug = f"Cell {target_cell_id} is not adjacent to {self._state.current_cell_id}"
            return result

        target_index = target_cell_id - 1
        if target_index < 0 or target_index >= len(self._book_types):
            goal_handle.abort()
            result.success = False
            result.error_code = 3
            result.debug = f"Invalid target cell {target_cell_id}"
            return result

        if self._book_types[target_index] != BookMap.R2:
            goal_handle.abort()
            result.success = False
            result.error_code = 4
            result.debug = f"Cell {target_cell_id} does not contain an R2 book"
            return result

        feedback = PickAdjacentBook.Feedback()
        feedback.state = "PICKING"
        feedback.progress = 1.0
        goal_handle.publish_feedback(feedback)

        self._book_types[target_index] = int(BookMap.EMPTY)
        self._state.cleared_mask |= 1 << target_index
        self._state.carry_r2 = min(2, self._state.carry_r2 + 1)
        goal_handle.succeed()
        result.success = True
        result.error_code = 0
        result.debug = f"Picked book at cell {target_cell_id}"
        self._publish_state()
        return result

    def _should_fail(self, action_type: str, step_index: int) -> bool:
        if not self._fail_action_type or self._fail_action_type != action_type:
            return False
        if self._fail_step_index >= 0 and self._fail_step_index != step_index:
            return False
        if self._fail_once and self._failure_consumed:
            return False
        self._failure_consumed = True
        return True

    def _next_step_index(self) -> int:
        current = self._action_counter
        self._action_counter += 1
        return current


def main(args: list[str] | None = None) -> None:
    rclpy.init(args=args)
    node = MockPlumWorldNode()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == "__main__":
    main()
