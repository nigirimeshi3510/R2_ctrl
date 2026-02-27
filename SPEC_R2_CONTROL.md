# SPEC_R2_CONTROL.md — R2 Control Stack Specification (Robocon 2026)

## 0. Purpose
This repository implements the autonomous control stack for NHK Student Robocon 2026 “Kung-Fu Quest” Robot R2.

Primary deliverables:
- Mission Behavior Tree (BT) for R2
- Plum Forest (梅花林) perception → discrete planning → execution pipeline
- Localization with mode switching (FLAT / CLIMB)
- Motion primitives as ROS 2 Actions (MoveCell / ClimbStep / PickAdjacentBook / DockToAruco)

Target platform:
- ROS 2 Humble on Jetson Orin NX
- STM32F446RE via micro-ROS (low-level IO & actuators)

---

## 1. Hardware Assumptions
### 1.1 Robot
- Base: 4-wheel mecanum
- Footprint: 600mm x 400mm

### 1.2 Sensors
- IMU: BNO055
  - Data path: UART -> STM32F446RE -> /imu (sensor_msgs/Imu)
- Ground odometry: small omni-wheel ground encoders (x,y)
  - IMPORTANT: If any lift mechanism is raised, ground encoder is ALWAYS floating -> invalid
- LiDAR: Hokuyo URG-30LX-EW x2
  - 270 deg, left & right outward-facing
  - Can detect step blocks
- Camera: YOLOv8
  - Book print classification: R1 / R2 / FAKE
  - From corridor short-side (just before entering plum forest), all books are identifiable (assumed true for this spec)

### 1.3 Actuation / Mechanism
- Suction pick for books
- Step traversal requires mechanical lift + sub-wheels (procedure defined in README.md)
- R1 will lift R2 for upper-tier placement (details TBD)

---

## 2. Hard Rules (Must Not Violate)
### 2.1 Inter-robot communication
- R1 and R2 must not communicate during the match (no Wi-Fi, no shared ROS graph, no wired link, etc.).
- Cooperation must rely on vision (Aruco), physical docking, and timing.

### 2.2 Plum Forest constraints
- Entry must be from R2 corridor.
- R2 can collect only R2 books.
- R2 may collect a book only from a block adjacent to the block where R2 currently stands.
- If R2 book exists in blocks 1–3, the first collected book must be collected from the corridor.
- R2 cannot exit the plum forest unless carrying >= 1 book.
- Exit is allowed only from blocks 10–12.

### 2.3 Forced retry / violations (critical)
- Do not move fake books.
- Do not step onto a block where a book is placed (unless that block is cleared after picking).
- Do not move books from non-adjacent blocks.
If any ambiguity exists, default to the safer behavior: treat as forbidden.

---

## 3. System Architecture (ROS 2 packages)
Suggested package layout:
- robocon_interfaces
  - msg / srv / action definitions
- robocon_perception
  - YOLOv8 inference pipeline
  - BookMap generation (12-cell classification)
- robocon_plum_planner
  - Discrete planner for plum forest with strict safety constraints
- robocon_localization
  - LaserScan fusion (left+right -> fused)
  - robot_localization EKFs (flat/climb)
  - AMCL localization (map->odom)
  - Mode switching (odom mux / scan gate)
- robocon_motion_primitives
  - Action servers: MoveCell, ClimbStep, PickAdjacentBook, DockToAruco
- robocon_bt_mission
  - Mission BT
  - Integration with Nav2 BT Navigator (optional; plum forest can be custom BT)
- robocon_bringup
  - Launch / params for the whole stack

---

## 4. Coordinate Frames & TF
- map: fixed field frame
- odom: continuous local frame from EKF
- base_link: robot base
- imu_link: IMU mounting
- laser_left, laser_right: LiDAR frames
- camera_link: camera frame

Required TF:
- base_link -> imu_link
- base_link -> laser_left / laser_right
- base_link -> camera_link

---

## 5. ROS Interfaces
### 5.1 Topics
- /imu : sensor_msgs/Imu
- /ground_odom : nav_msgs/Odometry
- /scan_left : sensor_msgs/LaserScan
- /scan_right : sensor_msgs/LaserScan
- /scan_fused : sensor_msgs/LaserScan (produced by scan_fuser)
- /loc_mode : std_msgs/String  ("FLAT" | "CLIMB")
- /cell_state : robocon_interfaces/msg/CellState
- /book_map : robocon_interfaces/msg/BookMap
- /plum_plan : robocon_interfaces/msg/PlumPlan (or action result)

### 5.2 Actions
- /move_cell : robocon_interfaces/action/MoveCell
  - goal: from_cell_id, to_cell_id
  - result: success, error_code, debug
- /climb_step : robocon_interfaces/action/ClimbStep
  - goal: direction (UP/DOWN), expected_to_cell_id
  - result: success, error_code, debug
- /pick_adjacent_book : robocon_interfaces/action/PickAdjacentBook
  - goal: target_cell_id
  - result: success, error_code, debug
- /dock_to_aruco : robocon_interfaces/action/DockToAruco
  - goal: marker_id, pos_tol, yaw_tol
  - result: success, error_code, debug

---

## 6. Localization Specification
### 6.1 Motivation
- Ground odom is invalid whenever lift is raised.
- During step traversal, 2D LiDAR scans may be distorted.

### 6.2 Mode Definitions
- FLAT:
  - Inputs: IMU + ground_odom (+ optional wheel odom)
  - Outputs: /odometry/filtered (odom->base_link)
  - AMCL enabled using /scan_fused
- CLIMB:
  - Inputs: IMU only (or IMU + extremely weak other sources)
  - ground_odom ignored
  - AMCL scan updates gated/disabled (or reduced)
  - Discrete cell tracking used by BT/planner (cell_id follows intended actions)

### 6.3 Implementation Requirements
- robot_localization EKF #1: ekf_flat.yaml
- robot_localization EKF #2: ekf_climb.yaml
- odom_mux:
  - selects /odometry/filtered from ekf_flat or ekf_climb based on /loc_mode
- scan_gate:
  - blocks /scan_fused into AMCL while in CLIMB

### 6.4 Post-climb relocalization sequence
After ClimbStep completes:
1) Stabilize 0.3–0.5s (stop motion)
2) Optional short spin (+/- 90 deg) to enrich scan
3) Wait for AMCL convergence (covariance threshold or stable pose)
4) Snap-to-cell-center (optional):
   - correct pose toward expected cell center to keep discrete/continuous consistent

---

## 7. Plum Forest Perception (BookMap)
### 7.1 BookMap definition
- 12 cells (blocks): cell_id = 1..12
- book_type per cell: EMPTY | R2 | R1 | FAKE | UNKNOWN
- confidence per cell: float [0..1]
- timestamp

### 7.2 Mapping detections to cells
Since corridor observation viewpoint is fixed:
- Use pre-calibrated homography or a static pixel->cell lookup.
- For each detection:
  - compute center point
  - map to cell_id
  - vote/overwrite by higher confidence

Safety rule:
- If confidence < threshold, set UNKNOWN.
- Planner must treat UNKNOWN as forbidden to step on.

---

## 8. Plum Forest Discrete Planner
### 8.1 State
- pos: current cell_id (or special "CORRIDOR" state)
- cleared_mask: bitmask of cells already cleared (picked) -> walkable
- carry_r2: 0..2
- book_map: fixed at start (assumed fully observed)

### 8.2 Walkability
- walkable(cell) = (book_type == EMPTY) OR (cleared_mask has cell bit)
- forbidden(cell) = (book_type in {R2,R1,FAKE,UNKNOWN}) AND not cleared

Fake is never cleared.

### 8.3 Actions
- MOVE(to_cell):
  - precondition: to_cell is adjacent to current cell
  - precondition: walkable(to_cell) == true
  - cost: step_move_cost_sec (parameter; target 5s)
- PICK(target_cell):
  - precondition: target_cell is adjacent to current cell
  - precondition: book_type[target_cell] == R2
  - effect: cleared_mask[target_cell]=true, carry_r2 += 1
  - cost: pick_cost_sec (parameter)
- EXIT:
  - precondition: current cell in {10,11,12}
  - precondition: carry_r2 >= 1

Special rule:
- If there is any R2 book in cells {1,2,3}, then the FIRST pick must be executed from CORRIDOR state (corridor-pick), not after entering blocks.

### 8.4 Objective
Primary: obtain 2 R2 books AND exit (reach 10/11/12 with carry>=1).
Fallback: obtain 1 R2 book AND exit.
Optimization: minimize total time cost; tie-break by higher safety margin (fewer risky steps).

### 8.5 Algorithm
Because the state space is small:
- Prefer DP / uniform-cost search over (pos, cleared_mask, carry).
- Output: a plan sequence of actions: [MOVE, PICK, MOVE, ..., EXIT]
- Also output: fallback plan (1-book) if 2-book is impossible.

---

## 9. Motion Primitives
### 9.1 MoveCell
- Implements a reliable traversal from current cell to adjacent cell:
  - alignment to edge/step start
  - execute step crossing procedure
  - stop and report success/failure

### 9.2 ClimbStep
- Implements the mechanical step procedure as defined in README.md
- Must set /loc_mode="CLIMB" at start and revert to "FLAT" after completion
- Must provide internal state logs for debugging

### 9.3 PickAdjacentBook
- Must only execute when target cell is adjacent and book type is R2
- Must include success verification:
  - Preferred: vacuum pressure sensor threshold + hold time
  - Alternative: pump current increase + vision confirmation (book disappeared from target cell)
- If verification fails: abort and let BT retry or replan

### 9.4 DockToAruco
- Visual servoing to reach relative pose tolerance to a marker
- Must be robust without inter-robot communication

---

## 10. Mission Behavior Tree (BT)
### 10.1 High-level phases
1) Init (bringup checks, TF, sensors)
2) Dojo:
   - wait for safe conditions
   - get spear head
3) Assembly:
   - dock to Aruco / wait pose
   - confirm dock success
4) Plum:
   - ObserveAllBooksFromCorridor -> BuildSafetyGrid -> ComputePlan(2, fallback=1) -> ExecutePlan -> Exit
5) Arena:
   - place 1st R2 book on mid tier
   - if lifted by R1: place 2nd book on upper tier
6) End

### 10.2 Core guards
- Never issue MOVE into forbidden cell
- Never issue PICK unless adjacency holds
- Never attempt EXIT unless carry>=1 and at 10/11/12
- If action fails: re-localize (if possible), then replan, then retry

---

## 11. Testing Requirements (must be implemented)
### 11.1 Planner unit tests
- never steps onto uncleared book blocks
- pick only from adjacent blocks
- exit only from 10/11/12 and carry>=1
- special rule for first pick if R2 is in 1–3
- handles UNKNOWN as forbidden

### 11.2 Integration tests (minimum)
- publish dummy /book_map -> planner outputs /plum_plan
- mock action servers consume plan and complete (success path)

---

## 12. Build & CI
- Must build with ROS 2 Humble
- Commands:
  - colcon build
  - colcon test
  - colcon test-result --verbose