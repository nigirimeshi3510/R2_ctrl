# TASKS.md — Implementation Plan (Codex-friendly)

## Conventions
- 1 task = 1 PR-sized change
- Always run:
  - `colcon build`
  - `colcon test`
  - `colcon test-result --verbose`
- Keep commits small and reviewable

---

## Task 0: Repo Bootstrap
### Goal
Create ROS 2 workspace structure with minimal packages and build passing.

### Deliverables
- `src/robocon_interfaces/` (empty msg/action scaffolding)
- `src/robocon_bringup/` (basic launch)
- `.gitignore` for ROS2 build artifacts
- `AGENT.md`, `SPEC_R2_CONTROL.md`, `TASKS.md` included at repo root

### Acceptance Criteria
- `colcon build` passes
- `ros2 pkg list | grep robocon_` shows packages

---

## Task 1: robocon_interfaces (msgs/actions)
### Goal
Define all required messages/actions used by the stack.

### Deliverables
- `msg/BookMap.msg`
- `msg/CellState.msg`
- `msg/PlumPlan.msg` (or use Action result)
- `action/MoveCell.action`
- `action/ClimbStep.action`
- `action/PickAdjacentBook.action`
- `action/DockToAruco.action`

### Acceptance Criteria
- Build passes
- Message/action generation works
- Minimal sample publisher/subscriber compiles

---

## Task 2: Perception BookMap (robocon_perception)
### Goal
Convert YOLO detections into a 12-cell BookMap.

### Deliverables
- Node: `bookmap_node`
  - Sub: `/yolo_detections` (define internal msg or use vision_msgs)
  - Pub: `/book_map` (robocon_interfaces/BookMap)
- Calibration config:
  - homography matrix OR pixel->cell LUT in YAML

### Acceptance Criteria
- Unit test: fixed detections -> expected cell_id mapping
- conf<threshold -> UNKNOWN
- `ros2 run ...` publishes /book_map correctly

---

## Task 3: Scan Fusion (robocon_localization)
### Goal
Fuse left/right LaserScan into /scan_fused for AMCL.

### Deliverables
- Node: `scan_fuser`
  - Sub: `/scan_left`, `/scan_right`
  - Pub: `/scan_fused`
- Parameters:
  - frame mapping policy
  - angular binning strategy

### Acceptance Criteria
- Node runs and outputs valid LaserScan
- Basic sanity: /scan_fused angle range reasonable

---

## Task 4: Localization Mode Switching (robocon_localization)
### Goal
Implement FLAT/CLIMB switching for odometry and scan gating.

### Deliverables
- `ekf_flat.yaml`, `ekf_climb.yaml` for robot_localization
- Node: `odom_mux`
  - Sub: `ekf_flat/odometry`, `ekf_climb/odometry`, `/loc_mode`
  - Pub: `/odometry/filtered`
- Node: `scan_gate`
  - Sub: `/scan_fused`, `/loc_mode`
  - Pub: `/scan_for_amcl` (or passthrough to AMCL input)

### Acceptance Criteria
- Switching /loc_mode toggles odom source
- CLIMB blocks scan input to AMCL

---

## Task 5: Plum Planner (robocon_plum_planner)
### Goal
Generate safe discrete plan from BookMap.

### Deliverables
- Node: `plum_planner_node`
  - Sub: `/book_map`, `/cell_state`
  - Pub: `/plum_plan`
- Planner core library:
  - DP / uniform-cost search over (pos, cleared_mask, carry)
  - Constraints implemented exactly per spec

### Acceptance Criteria (Unit Tests REQUIRED)
- Never MOVE onto forbidden (uncleared book) cells
- PICK only adjacent
- EXIT only at 10/11/12 with carry>=1
- Special first-pick rule when R2 exists in 1–3
- UNKNOWN treated as forbidden
- Provides fallback 1-book plan if 2-book plan impossible

---

## Task 6: Motion Primitives (robocon_motion_primitives)
### Goal
Create Action servers for MoveCell/Climb/Pick.

### Deliverables
- Action servers:
  - /move_cell
  - /climb_step
  - /pick_adjacent_book
- Internal state machine for climb procedure (README.md)
- Publish /loc_mode transitions:
  - CLIMB during climb, FLAT after completion

### Acceptance Criteria
- Mock mode: actions return success and log transitions
- Real mode hooks prepared (topics/services to STM32)
- Failures return meaningful error codes

---

## Task 7: Mission BT (robocon_bt_mission)
### Goal
Implement PlumPhase BT pipeline end-to-end.

### Deliverables
- BT nodes:
  - ObserveAllBooksFromCorridor
  - ComputePlumPlan
  - ExecutePlumPlan (dispatch actions sequentially)
  - ExitPlumForest
- Blackboard variables:
  - book_map, cell_state, plan, carry, loc_mode

### Acceptance Criteria
- With mocked actions, BT completes:
  - Observe -> Plan -> Execute -> Exit
- On any action failure:
  - triggers replan and retry (bounded retries)

---

## Task 8 (Optional but Recommended): CI
### Goal
Ensure main branch always builds/tests.

### Deliverables
- GitHub Actions workflow:
  - build + test on Ubuntu 22.04, ROS 2 Humble
- Caching for faster iteration

### Acceptance Criteria
- PR must pass CI before merge