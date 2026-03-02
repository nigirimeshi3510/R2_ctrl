from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, IncludeLaunchDescription
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import LaunchConfiguration, PathJoinSubstitution
from launch_ros.substitutions import FindPackageShare


def generate_launch_description() -> LaunchDescription:
    dual_lidar_launch = PathJoinSubstitution(
        [FindPackageShare("robocon_bringup"), "launch", "dual_lidar.launch.py"]
    )
    scan_fuser_launch = PathJoinSubstitution(
        [FindPackageShare("robocon_localization"), "launch", "scan_fuser.launch.py"]
    )

    return LaunchDescription([
        DeclareLaunchArgument("left_ip", default_value="192.168.0.20"),
        DeclareLaunchArgument("right_ip", default_value="192.168.0.10"),
        DeclareLaunchArgument("left_scan_topic", default_value="/scan_left"),
        DeclareLaunchArgument("right_scan_topic", default_value="/scan_right"),
        DeclareLaunchArgument("output_topic", default_value="/scan_fused"),
        IncludeLaunchDescription(
            PythonLaunchDescriptionSource(dual_lidar_launch),
            launch_arguments={
                "left_ip": LaunchConfiguration("left_ip"),
                "right_ip": LaunchConfiguration("right_ip"),
                "left_scan_topic": LaunchConfiguration("left_scan_topic"),
                "right_scan_topic": LaunchConfiguration("right_scan_topic"),
                "use_rviz": "true",
            }.items(),
        ),
        IncludeLaunchDescription(
            PythonLaunchDescriptionSource(scan_fuser_launch),
            launch_arguments={
                "left_topic": LaunchConfiguration("left_scan_topic"),
                "right_topic": LaunchConfiguration("right_scan_topic"),
                "output_topic": LaunchConfiguration("output_topic"),
                "target_frame": "base_link",
            }.items(),
        ),
    ])
