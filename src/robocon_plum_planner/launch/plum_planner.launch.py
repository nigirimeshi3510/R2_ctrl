from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node


def generate_launch_description() -> LaunchDescription:
    return LaunchDescription([
        DeclareLaunchArgument("book_map_topic", default_value="/book_map"),
        DeclareLaunchArgument("cell_state_topic", default_value="/cell_state"),
        DeclareLaunchArgument("output_topic", default_value="/plum_plan"),
        DeclareLaunchArgument("team_color", default_value="red"),
        DeclareLaunchArgument("step_move_cost_sec", default_value="5.0"),
        DeclareLaunchArgument("pick_cost_sec", default_value="4.0"),
        DeclareLaunchArgument("exit_cost_sec", default_value="0.0"),
        DeclareLaunchArgument("allow_fallback_to_one", default_value="true"),
        Node(
            package="robocon_plum_planner",
            executable="plum_planner",
            name="plum_planner",
            output="screen",
            parameters=[{
                "book_map_topic": LaunchConfiguration("book_map_topic"),
                "cell_state_topic": LaunchConfiguration("cell_state_topic"),
                "output_topic": LaunchConfiguration("output_topic"),
                "team_color": LaunchConfiguration("team_color"),
                "step_move_cost_sec": LaunchConfiguration("step_move_cost_sec"),
                "pick_cost_sec": LaunchConfiguration("pick_cost_sec"),
                "exit_cost_sec": LaunchConfiguration("exit_cost_sec"),
                "allow_fallback_to_one": LaunchConfiguration("allow_fallback_to_one"),
            }],
        ),
    ])

