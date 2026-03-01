cmake_minimum_required(VERSION 3.8)
project(robocon_interfaces)

if(CMAKE_COMPILER_IS_GNUCXX OR CMAKE_CXX_COMPILER_ID MATCHES "Clang")
  add_compile_options(-Wall -Wextra -Wpedantic)
endif()

find_package(ament_cmake REQUIRED)
find_package(rosidl_default_generators REQUIRED)
find_package(std_msgs REQUIRED)

rosidl_generate_interfaces(${PROJECT_NAME}
  "msg/BookMap.msg"
  "msg/CellState.msg"
  "msg/PlanStep.msg"
  "msg/PlumPlan.msg"
  "action/MoveCell.action"
  "action/ClimbStep.action"
  "action/PickAdjacentBook.action"
  "action/DockToAruco.action"
  DEPENDENCIES std_msgs
)

ament_export_dependencies(rosidl_default_runtime)

if(BUILD_TESTING)
  find_package(ament_cmake_gtest REQUIRED)
  find_package(rclcpp REQUIRED)
  ament_add_gtest(test_interface_compile test/test_interface_compile.cpp)
  if(TARGET test_interface_compile)
    target_compile_features(test_interface_compile PUBLIC cxx_std_17)
    ament_target_dependencies(test_interface_compile rclcpp)
    rosidl_get_typesupport_target(cpp_typesupport_target
      ${PROJECT_NAME} "rosidl_typesupport_cpp")
    target_link_libraries(test_interface_compile "${cpp_typesupport_target}")
  endif()
endif()

ament_package()
