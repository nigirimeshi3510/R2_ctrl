from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument
from launch.conditions import IfCondition
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node


def generate_launch_description() -> LaunchDescription:
    """Return the minimal bringup launch description for Task 0."""
    use_bookmap = LaunchConfiguration("use_bookmap")
    use_plum_planner = LaunchConfiguration("use_plum_planner")
    team_color = LaunchConfiguration("team_color")
    return LaunchDescription([
        DeclareLaunchArgument(
            "use_bookmap",
            default_value="false",
            description="If true, start robocon_perception bookmap_node.",
        ),
        DeclareLaunchArgument(
            "use_plum_planner",
            default_value="false",
            description="If true, start robocon_plum_planner plum_planner node.",
        ),
        DeclareLaunchArgument(
            "team_color",
            default_value="red",
            description="Team color used for cell-id normalization: red|blue.",
        ),
        Node(
            package="robocon_perception",
            executable="bookmap_node",
            name="bookmap_node",
            output="screen",
            condition=IfCondition(use_bookmap),
        ),
        Node(
            package="robocon_plum_planner",
            executable="plum_planner",
            name="plum_planner",
            output="screen",
            parameters=[{"team_color": team_color}],
            condition=IfCondition(use_plum_planner),
        ),
    ])
