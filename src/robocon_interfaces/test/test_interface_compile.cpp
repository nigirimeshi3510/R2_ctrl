#include <gtest/gtest.h>

#include <memory>
#include <type_traits>

#include "rclcpp/rclcpp.hpp"
#include "robocon_interfaces/action/climb_step.hpp"
#include "robocon_interfaces/action/dock_to_aruco.hpp"
#include "robocon_interfaces/action/move_cell.hpp"
#include "robocon_interfaces/action/pick_adjacent_book.hpp"
#include "robocon_interfaces/msg/book_map.hpp"
#include "robocon_interfaces/msg/cell_state.hpp"
#include "robocon_interfaces/msg/plum_plan.hpp"

TEST(RoboconInterfaces, MinimalPubSubCompiles)
{
  using PubT = rclcpp::Publisher<robocon_interfaces::msg::BookMap>;
  using SubT = rclcpp::Subscription<robocon_interfaces::msg::CellState>;
  static_assert(std::is_class_v<PubT>, "Publisher type must be defined");
  static_assert(std::is_class_v<SubT>, "Subscription type must be defined");

  robocon_interfaces::msg::BookMap msg;
  msg.book_type[0] = robocon_interfaces::msg::BookMap::UNKNOWN;
  msg.confidence[0] = 0.0F;

  EXPECT_EQ(msg.book_type[0], robocon_interfaces::msg::BookMap::UNKNOWN);
}

TEST(RoboconInterfaces, ActionTypesCompile)
{
  robocon_interfaces::action::MoveCell::Goal move_goal;
  move_goal.from_cell_id = 1;
  move_goal.to_cell_id = 2;

  robocon_interfaces::action::ClimbStep::Goal climb_goal;
  climb_goal.direction = robocon_interfaces::action::ClimbStep::Goal::UP;
  climb_goal.expected_to_cell_id = 3;

  robocon_interfaces::action::PickAdjacentBook::Goal pick_goal;
  pick_goal.target_cell_id = 4;

  robocon_interfaces::action::DockToAruco::Goal dock_goal;
  dock_goal.marker_id = 1;
  dock_goal.pos_tol = 0.05F;
  dock_goal.yaw_tol = 0.10F;

  EXPECT_EQ(move_goal.to_cell_id, 2);
  EXPECT_EQ(climb_goal.direction, robocon_interfaces::action::ClimbStep::Goal::UP);
  EXPECT_EQ(pick_goal.target_cell_id, 4);
  EXPECT_EQ(dock_goal.marker_id, 1);
}
