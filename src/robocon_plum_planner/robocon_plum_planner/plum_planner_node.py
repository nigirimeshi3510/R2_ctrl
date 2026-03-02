"""ROS 2 node for plum forest discrete planning."""

from __future__ import annotations

import math

import rclpy
from rclpy.node import Node

from robocon_interfaces.msg import BookMap, CellState, PlanStep as PlanStepMsg, PlumPlan

from robocon_plum_planner.planner_core import PlannerConfig, PlannerInput, plan_with_fallback
from robocon_plum_planner.team_mapping import (
    from_canonical_plan_target,
    normalize_team_color,
    to_canonical_book_types,
    to_canonical_cell_id,
    to_canonical_cleared_mask,
)


class PlumPlannerNode(Node):
    """Plans safe discrete actions from BookMap and CellState."""

    def __init__(self) -> None:
        super().__init__("plum_planner")

        self.declare_parameter("book_map_topic", "/book_map")
        self.declare_parameter("cell_state_topic", "/cell_state")
        self.declare_parameter("output_topic", "/plum_plan")
        self.declare_parameter("team_color", "red")
        self.declare_parameter("step_move_cost_sec", 5.0)
        self.declare_parameter("pick_cost_sec", 4.0)
        self.declare_parameter("exit_cost_sec", 0.0)
        self.declare_parameter("allow_fallback_to_one", True)

        self._book_map_topic = str(self.get_parameter("book_map_topic").value)
        self._cell_state_topic = str(self.get_parameter("cell_state_topic").value)
        self._output_topic = str(self.get_parameter("output_topic").value)
        self._team_color = normalize_team_color(str(self.get_parameter("team_color").value))
        self._cfg = PlannerConfig(
            step_move_cost_sec=float(self.get_parameter("step_move_cost_sec").value),
            pick_cost_sec=float(self.get_parameter("pick_cost_sec").value),
            exit_cost_sec=float(self.get_parameter("exit_cost_sec").value),
        )
        self._allow_fallback_to_one = bool(self.get_parameter("allow_fallback_to_one").value)

        self._last_book_map: BookMap | None = None
        self._last_cell_state: CellState | None = None

        self._sub_book_map = self.create_subscription(BookMap, self._book_map_topic, self._on_book_map, 10)
        self._sub_cell_state = self.create_subscription(
            CellState,
            self._cell_state_topic,
            self._on_cell_state,
            10,
        )
        self._pub_plan = self.create_publisher(PlumPlan, self._output_topic, 10)

        self.get_logger().info(
            "plum_planner started: "
            f"book_map={self._book_map_topic} cell_state={self._cell_state_topic} "
            f"out={self._output_topic} team_color={self._team_color}"
        )

    def _on_book_map(self, msg: BookMap) -> None:
        self._last_book_map = msg
        self._replan_and_publish()

    def _on_cell_state(self, msg: CellState) -> None:
        self._last_cell_state = msg
        self._replan_and_publish()

    def _replan_and_publish(self) -> None:
        if self._last_book_map is None or self._last_cell_state is None:
            return

        try:
            planner_input = PlannerInput(
                book_types=tuple(
                    to_canonical_book_types(
                        [int(v) for v in self._last_book_map.book_type],
                        self._team_color,
                    )
                ),
                current_cell_id=to_canonical_cell_id(
                    int(self._last_cell_state.current_cell_id),
                    self._team_color,
                ),
                carry_r2=int(self._last_cell_state.carry_r2),
                cleared_mask=to_canonical_cleared_mask(
                    int(self._last_cell_state.cleared_mask),
                    self._team_color,
                ),
            )
        except ValueError as exc:
            self.get_logger().error(f"invalid planning input: {exc}")
            return

        result = plan_with_fallback(
            planner_input,
            self._cfg,
            allow_fallback_to_one=self._allow_fallback_to_one,
        )

        out = PlumPlan()
        out.header.stamp = self.get_clock().now().to_msg()
        out.header.frame_id = self._last_book_map.header.frame_id

        if result is None:
            out.steps = []
            out.is_fallback_plan = False
            out.estimated_cost_sec = math.inf
            self.get_logger().warn("no feasible plan found for current BookMap/CellState")
        else:
            out_steps: list[PlanStepMsg] = []
            for step in result.steps:
                msg = PlanStepMsg()
                msg.action_type = int(step.action_type)
                msg.target_cell_id = int(from_canonical_plan_target(step.target_cell_id, self._team_color))
                out_steps.append(msg)
            out.steps = out_steps
            out.is_fallback_plan = bool(result.is_fallback_plan)
            out.estimated_cost_sec = float(result.estimated_cost_sec)

        self._pub_plan.publish(out)


def main(args: list[str] | None = None) -> None:
    rclpy.init(args=args)
    node = PlumPlannerNode()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == "__main__":
    main()

