"""ROS 2 node converting BookMap into RViz MarkerArray."""

from __future__ import annotations

import rclpy
from rclpy.node import Node
from robocon_interfaces.msg import BookMap
from visualization_msgs.msg import Marker, MarkerArray

from robocon_perception.bookmap_core import (
    EMPTY_LABEL,
    FAKE_LABEL,
    R1_LABEL,
    R2_LABEL,
    UNKNOWN_LABEL,
)
from robocon_perception.bookmap_viz_core import (
    color_for_label,
    grid_pose_for_cell,
    label_from_book_type,
    marker_text,
)


class BookMapVizNode(Node):
    """Visualizes BookMap in RViz with front row as cells 10,11,12."""

    def __init__(self) -> None:
        super().__init__("bookmap_viz_node")

        self.declare_parameter("input_topic", "/book_map")
        self.declare_parameter("output_topic", "/book_map_markers")
        self.declare_parameter("frame_id", "map")
        self.declare_parameter("grid_origin_x", 0.0)
        self.declare_parameter("grid_origin_y", 0.0)
        self.declare_parameter("cell_size_x", 0.35)
        self.declare_parameter("cell_size_y", 0.35)
        self.declare_parameter("z_plane", 0.0)
        self.declare_parameter("alpha", 0.85)
        self.declare_parameter("show_text", True)
        self.declare_parameter("text_height", 0.10)

        input_topic = self.get_parameter("input_topic").get_parameter_value().string_value
        output_topic = self.get_parameter("output_topic").get_parameter_value().string_value

        self._frame_id = self.get_parameter("frame_id").get_parameter_value().string_value
        self._origin_x = self.get_parameter("grid_origin_x").get_parameter_value().double_value
        self._origin_y = self.get_parameter("grid_origin_y").get_parameter_value().double_value
        self._cell_size_x = self.get_parameter("cell_size_x").get_parameter_value().double_value
        self._cell_size_y = self.get_parameter("cell_size_y").get_parameter_value().double_value
        self._z_plane = self.get_parameter("z_plane").get_parameter_value().double_value
        self._alpha = self.get_parameter("alpha").get_parameter_value().double_value
        self._show_text = self.get_parameter("show_text").get_parameter_value().bool_value
        self._text_height = self.get_parameter("text_height").get_parameter_value().double_value

        self._enum_mapping = {
            EMPTY_LABEL: BookMap.EMPTY,
            R2_LABEL: BookMap.R2,
            R1_LABEL: BookMap.R1,
            FAKE_LABEL: BookMap.FAKE,
            UNKNOWN_LABEL: BookMap.UNKNOWN,
        }

        self._pub = self.create_publisher(MarkerArray, output_topic, 10)
        self._sub = self.create_subscription(BookMap, input_topic, self._on_bookmap, 10)

        self.get_logger().info(
            "bookmap_viz_node started: input=%s output=%s front_row=[10,11,12]"
            % (input_topic, output_topic)
        )

    def _book_type_at(self, msg: BookMap, idx: int) -> int:
        if idx < len(msg.book_type):
            return int(msg.book_type[idx])
        return BookMap.UNKNOWN

    def _confidence_at(self, msg: BookMap, idx: int) -> float:
        if idx < len(msg.confidence):
            return float(msg.confidence[idx])
        return 0.0

    def _on_bookmap(self, msg: BookMap) -> None:
        marker_array = MarkerArray()

        for idx in range(12):
            cell_id = idx + 1
            book_type = self._book_type_at(msg, idx)
            confidence = self._confidence_at(msg, idx)
            label = label_from_book_type(book_type, self._enum_mapping)
            pose = grid_pose_for_cell(
                cell_id=cell_id,
                origin_x=self._origin_x,
                origin_y=self._origin_y,
                cell_size_x=self._cell_size_x,
                cell_size_y=self._cell_size_y,
            )

            cell_marker = Marker()
            cell_marker.header.stamp = msg.header.stamp
            cell_marker.header.frame_id = self._frame_id
            cell_marker.ns = "bookmap_cells"
            cell_marker.id = idx
            cell_marker.type = Marker.CUBE
            cell_marker.action = Marker.ADD
            cell_marker.pose.position.x = pose.x
            cell_marker.pose.position.y = pose.y
            cell_marker.pose.position.z = self._z_plane
            cell_marker.pose.orientation.w = 1.0
            cell_marker.scale.x = self._cell_size_x * 0.95
            cell_marker.scale.y = self._cell_size_y * 0.95
            cell_marker.scale.z = 0.02
            cell_marker.color = color_for_label(label, self._alpha)
            marker_array.markers.append(cell_marker)

            if not self._show_text:
                continue

            text_marker = Marker()
            text_marker.header.stamp = msg.header.stamp
            text_marker.header.frame_id = self._frame_id
            text_marker.ns = "bookmap_labels"
            text_marker.id = 100 + idx
            text_marker.type = Marker.TEXT_VIEW_FACING
            text_marker.action = Marker.ADD
            text_marker.pose.position.x = pose.x
            text_marker.pose.position.y = pose.y
            text_marker.pose.position.z = self._z_plane + 0.08
            text_marker.pose.orientation.w = 1.0
            text_marker.scale.z = self._text_height
            text_marker.color.r = 1.0
            text_marker.color.g = 1.0
            text_marker.color.b = 1.0
            text_marker.color.a = 1.0
            text_marker.text = marker_text(cell_id, label, confidence)
            marker_array.markers.append(text_marker)

        self._pub.publish(marker_array)


def main(args: list[str] | None = None) -> None:
    rclpy.init(args=args)
    node = BookMapVizNode()
    try:
        rclpy.spin(node)
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == "__main__":
    main()
