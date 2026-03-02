from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node


def generate_launch_description() -> LaunchDescription:
    return LaunchDescription([
        DeclareLaunchArgument("left_topic", default_value="/scan_left"),
        DeclareLaunchArgument("right_topic", default_value="/scan_right"),
        DeclareLaunchArgument("output_topic", default_value="/scan_fused"),
        DeclareLaunchArgument("target_frame", default_value="base_link"),
        DeclareLaunchArgument("sync_tolerance_sec", default_value="0.15"),
        DeclareLaunchArgument("publish_rate_hz", default_value="10.0"),
        DeclareLaunchArgument("angle_min", default_value="-3.141592653589793"),
        DeclareLaunchArgument("angle_max", default_value="3.141592653589793"),
        DeclareLaunchArgument("angle_increment", default_value="0.004363323"),
        DeclareLaunchArgument("range_min", default_value="0.05"),
        DeclareLaunchArgument("range_max", default_value="30.0"),
        DeclareLaunchArgument("use_inf", default_value="true"),
        DeclareLaunchArgument("inf_epsilon", default_value="1.0"),
        Node(
            package="robocon_localization",
            executable="scan_fuser",
            name="scan_fuser",
            output="screen",
            parameters=[{
                "left_topic": LaunchConfiguration("left_topic"),
                "right_topic": LaunchConfiguration("right_topic"),
                "output_topic": LaunchConfiguration("output_topic"),
                "target_frame": LaunchConfiguration("target_frame"),
                "sync_tolerance_sec": LaunchConfiguration("sync_tolerance_sec"),
                "publish_rate_hz": LaunchConfiguration("publish_rate_hz"),
                "angle_min": LaunchConfiguration("angle_min"),
                "angle_max": LaunchConfiguration("angle_max"),
                "angle_increment": LaunchConfiguration("angle_increment"),
                "range_min": LaunchConfiguration("range_min"),
                "range_max": LaunchConfiguration("range_max"),
                "use_inf": LaunchConfiguration("use_inf"),
                "inf_epsilon": LaunchConfiguration("inf_epsilon"),
            }],
        ),
    ])
