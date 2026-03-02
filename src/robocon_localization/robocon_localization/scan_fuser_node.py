"""ROS 2 node fusing /scan_left and /scan_right into /scan_fused."""

from __future__ import annotations

import math

import rclpy
from rclpy.node import Node
from rclpy.duration import Duration
from rclpy.time import Time
from sensor_msgs.msg import LaserScan
from tf2_ros import Buffer, TransformException, TransformListener

from robocon_localization.scan_fuser_core import FuserConfig, PolarScan, Pose2D, fuse_scans


class ScanFuserNode(Node):
    """Fuse two LaserScan streams for AMCL input."""

    def __init__(self) -> None:
        super().__init__("scan_fuser")

        self.declare_parameter("left_topic", "/scan_left")
        self.declare_parameter("right_topic", "/scan_right")
        self.declare_parameter("output_topic", "/scan_fused")
        self.declare_parameter("target_frame", "base_link")
        self.declare_parameter("sync_tolerance_sec", 0.15)
        self.declare_parameter("publish_rate_hz", 10.0)

        self.declare_parameter("angle_min", -3.141592653589793)
        self.declare_parameter("angle_max", 3.141592653589793)
        self.declare_parameter("angle_increment", 0.004363323)
        self.declare_parameter("range_min", 0.05)
        self.declare_parameter("range_max", 30.0)
        self.declare_parameter("use_inf", True)
        self.declare_parameter("inf_epsilon", 1.0)

        left_topic = self.get_parameter("left_topic").value
        right_topic = self.get_parameter("right_topic").value
        output_topic = self.get_parameter("output_topic").value
        self._target_frame = self.get_parameter("target_frame").value
        self._sync_tolerance = float(self.get_parameter("sync_tolerance_sec").value)
        rate_hz = float(self.get_parameter("publish_rate_hz").value)

        self._cfg = FuserConfig(
            angle_min=float(self.get_parameter("angle_min").value),
            angle_max=float(self.get_parameter("angle_max").value),
            angle_increment=float(self.get_parameter("angle_increment").value),
            range_min=float(self.get_parameter("range_min").value),
            range_max=float(self.get_parameter("range_max").value),
            use_inf=bool(self.get_parameter("use_inf").value),
            inf_epsilon=float(self.get_parameter("inf_epsilon").value),
        )

        self._tf_buffer = Buffer(cache_time=Duration(seconds=5.0))
        self._tf_listener = TransformListener(self._tf_buffer, self)

        self._left_scan: LaserScan | None = None
        self._right_scan: LaserScan | None = None

        self._sub_left = self.create_subscription(LaserScan, left_topic, self._on_left, 10)
        self._sub_right = self.create_subscription(LaserScan, right_topic, self._on_right, 10)
        self._pub = self.create_publisher(LaserScan, output_topic, 10)
        self._timer = self.create_timer(1.0 / max(rate_hz, 1.0), self._try_publish)

        self.get_logger().info(
            "scan_fuser started: "
            f"left={left_topic} right={right_topic} out={output_topic} frame={self._target_frame}"
        )

    def _on_left(self, msg: LaserScan) -> None:
        self._left_scan = msg

    def _on_right(self, msg: LaserScan) -> None:
        self._right_scan = msg

    def _stamp_sec(self, msg: LaserScan) -> float:
        return float(msg.header.stamp.sec) + (float(msg.header.stamp.nanosec) * 1e-9)

    def _transform_pose(self, from_frame: str, stamp: Time) -> Pose2D | None:
        try:
            tf = self._tf_buffer.lookup_transform(
                self._target_frame,
                from_frame,
                stamp,
                timeout=Duration(seconds=0.05),
            )
        except TransformException as exc:
            self.get_logger().warn(
                f"TF lookup failed from '{from_frame}' to '{self._target_frame}': {exc}",
                throttle_duration_sec=2.0,
            )
            return None

        q = tf.transform.rotation
        # Yaw extraction from quaternion; scan fusion is planar.
        yaw = math.atan2(
            2.0 * (q.w * q.z + q.x * q.y),
            1.0 - 2.0 * (q.y * q.y + q.z * q.z),
        )
        return Pose2D(
            x=float(tf.transform.translation.x),
            y=float(tf.transform.translation.y),
            yaw=yaw,
        )

    def _to_polar_scan(self, msg: LaserScan) -> PolarScan:
        return PolarScan(
            angle_min=float(msg.angle_min),
            angle_increment=float(msg.angle_increment),
            ranges=[float(r) for r in msg.ranges],
            range_min=float(msg.range_min),
            range_max=float(msg.range_max),
        )

    def _try_publish(self) -> None:
        if self._left_scan is None or self._right_scan is None:
            return

        dt = abs(self._stamp_sec(self._left_scan) - self._stamp_sec(self._right_scan))
        if dt > self._sync_tolerance:
            self.get_logger().warn(
                f"scan timestamp mismatch too large: {dt:.3f}s > {self._sync_tolerance:.3f}s",
                throttle_duration_sec=2.0,
            )
            return

        left_stamp = Time.from_msg(self._left_scan.header.stamp)
        right_stamp = Time.from_msg(self._right_scan.header.stamp)

        left_pose = self._transform_pose(self._left_scan.header.frame_id, left_stamp)
        right_pose = self._transform_pose(self._right_scan.header.frame_id, right_stamp)
        if left_pose is None or right_pose is None:
            return

        fused_ranges = fuse_scans(
            [
                (self._to_polar_scan(self._left_scan), left_pose),
                (self._to_polar_scan(self._right_scan), right_pose),
            ],
            self._cfg,
        )

        out = LaserScan()
        out.header.stamp = self.get_clock().now().to_msg()
        out.header.frame_id = self._target_frame
        out.angle_min = self._cfg.angle_min
        out.angle_max = self._cfg.angle_max
        out.angle_increment = self._cfg.angle_increment
        out.time_increment = 0.0
        out.scan_time = 0.0
        out.range_min = self._cfg.range_min
        out.range_max = self._cfg.range_max
        out.ranges = fused_ranges
        out.intensities = []

        self._pub.publish(out)


def main(args: list[str] | None = None) -> None:
    rclpy.init(args=args)
    node = ScanFuserNode()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == "__main__":
    main()
