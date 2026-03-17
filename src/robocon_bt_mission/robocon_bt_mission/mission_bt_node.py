"""ROS 2 node for the simple plum mission BT."""

from __future__ import annotations

import rclpy
from rclpy.action import ActionClient
from rclpy.node import Node

from robocon_interfaces.action import MoveCell, PickAdjacentBook
from robocon_interfaces.msg import BookMap, CellState, PlumPlan

from robocon_bt_mission.mission_bt_core import (
    ACTION_MOVE,
    ACTION_PICK,
    MissionTickResult,
    NodeStatus,
    PlanSnapshot,
    PlanStepSnapshot,
    SimplePlumMissionBt,
)


class MissionBtNode(Node):
    """Simple plum mission BT with one-shot recovery."""

    def __init__(self) -> None:
        super().__init__("mission_bt")
        self.declare_parameter("book_map_topic", "/book_map")
        self.declare_parameter("cell_state_topic", "/cell_state")
        self.declare_parameter("plan_topic", "/plum_plan")
        self.declare_parameter("move_action_name", "/move_cell")
        self.declare_parameter("pick_action_name", "/pick_adjacent_book")
        self.declare_parameter("tick_period_sec", 0.2)
        self.declare_parameter("max_retries", 1)

        self._tick_period_sec = float(self.get_parameter("tick_period_sec").value)
        self._tree = SimplePlumMissionBt(max_retries=int(self.get_parameter("max_retries").value))
        self._move_client = ActionClient(
            self,
            MoveCell,
            str(self.get_parameter("move_action_name").value),
        )
        self._pick_client = ActionClient(
            self,
            PickAdjacentBook,
            str(self.get_parameter("pick_action_name").value),
        )

        self._sub_book_map = self.create_subscription(
            BookMap,
            str(self.get_parameter("book_map_topic").value),
            self._on_book_map,
            10,
        )
        self._sub_cell_state = self.create_subscription(
            CellState,
            str(self.get_parameter("cell_state_topic").value),
            self._on_cell_state,
            10,
        )
        self._sub_plan = self.create_subscription(
            PlumPlan,
            str(self.get_parameter("plan_topic").value),
            self._on_plan,
            10,
        )
        self._tick_timer = self.create_timer(self._tick_period_sec, self._on_tick)

        self._inflight_result_future = None
        self._last_logged_phase = ""
        self._action_ready_logged = False

        self.get_logger().info("mission_bt started")

    def _on_book_map(self, msg: BookMap) -> None:
        self._tree.update_book_map(tuple(int(v) for v in msg.book_type))

    def _on_cell_state(self, msg: CellState) -> None:
        self._tree.update_cell_state(
            current_cell_id=int(msg.current_cell_id),
            carry_r2=int(msg.carry_r2),
            cleared_mask=int(msg.cleared_mask),
            loc_mode=str(msg.loc_mode),
        )

    def _on_plan(self, msg: PlumPlan) -> None:
        plan = PlanSnapshot(
            steps=tuple(
                PlanStepSnapshot(
                    action_type=int(step.action_type),
                    target_cell_id=int(step.target_cell_id),
                )
                for step in msg.steps
            ),
            is_fallback_plan=bool(msg.is_fallback_plan),
            estimated_cost_sec=float(msg.estimated_cost_sec),
        )
        self._tree.update_plan(plan)

    def _on_tick(self) -> None:
        if not self._action_servers_ready():
            return

        result = self._tree.tick()
        self._log_transition(result)
        if result.command is None:
            return

        if self._inflight_result_future is not None:
            return

        self._dispatch_command(result)

    def _action_servers_ready(self) -> bool:
        ready = self._move_client.wait_for_server(timeout_sec=0.0) and self._pick_client.wait_for_server(timeout_sec=0.0)
        if ready:
            if not self._action_ready_logged:
                self.get_logger().info("action servers are ready")
                self._action_ready_logged = True
            return True
        self._action_ready_logged = False
        self.get_logger().debug("waiting for action servers")
        return False

    def _dispatch_command(self, result: MissionTickResult) -> None:
        command = result.command
        if command is None:
            return

        if command.action_type == ACTION_MOVE:
            goal = MoveCell.Goal()
            goal.from_cell_id = int(command.from_cell_id)
            goal.to_cell_id = int(command.target_cell_id)
            client = self._move_client
        elif command.action_type == ACTION_PICK:
            goal = PickAdjacentBook.Goal()
            goal.target_cell_id = int(command.target_cell_id)
            client = self._pick_client
        else:
            self.get_logger().error(f"unsupported command type: {command.action_type}")
            self._tree.complete_action(False, f"unsupported action type {command.action_type}")
            return

        send_future = client.send_goal_async(goal)
        send_future.add_done_callback(self._on_goal_response)
        self._inflight_result_future = send_future
        self.get_logger().info(
            f"dispatch {result.active_node}: action={command.action_type} "
            f"from={command.from_cell_id} target={command.target_cell_id}"
        )

    def _on_goal_response(self, future) -> None:
        try:
            goal_handle = future.result()
        except Exception as exc:  # pragma: no cover - rclpy future error path
            self._inflight_result_future = None
            self._tree.complete_action(False, f"goal send failed: {exc}")
            return

        if not goal_handle.accepted:
            self._inflight_result_future = None
            self._tree.complete_action(False, "goal rejected")
            return

        result_future = goal_handle.get_result_async()
        result_future.add_done_callback(self._on_action_result)
        self._inflight_result_future = result_future

    def _on_action_result(self, future) -> None:
        self._inflight_result_future = None
        try:
            wrapped_result = future.result()
        except Exception as exc:  # pragma: no cover - rclpy future error path
            self._tree.complete_action(False, f"result wait failed: {exc}")
            return

        result = wrapped_result.result
        if bool(result.success):
            self._tree.complete_action(True, str(result.debug))
            self.get_logger().info(f"action success: {result.debug}")
            return

        self._tree.complete_action(False, str(result.debug))
        self.get_logger().warn(f"action failed: {result.debug}")

    def _log_transition(self, result: MissionTickResult) -> None:
        if result.active_node != self._last_logged_phase:
            self._last_logged_phase = result.active_node
            self.get_logger().info(f"phase={result.active_node} retry={self._tree.blackboard.retry_count}")
        if result.status == NodeStatus.FAILURE:
            self.get_logger().error(result.message or self._tree.blackboard.last_error)
        elif result.status == NodeStatus.SUCCESS and result.active_node == "ExitPlumForest":
            self.get_logger().info("mission succeeded")


def main(args: list[str] | None = None) -> None:
    rclpy.init(args=args)
    node = MissionBtNode()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == "__main__":
    main()
