# AGENT.md — Repository Agent Guide (R2 Control)

## 0. Mission
This repository implements the autonomous control stack for Robocon 2026 R2
(ROS 2 Humble on Jetson Orin NX + STM32F446RE micro-ROS).

Primary goals:
- Mission Behavior Tree (BT)
- Plum forest (梅花林) discrete planner with strict safety constraints
- Localization with FLAT/CLIMB mode switching
- Motion primitives (MoveCell / ClimbStep / PickAdjacentBook)

## 1. Hard Rules (MUST NOT VIOLATE)
- R1 and R2 must not communicate during the match (no Wi-Fi, ROS topic sharing, wired link, etc.).
- In plum forest:
  - Never generate motion that drives onto a block where a book is placed (unless that block is cleared after picking).
  - Never move a fake book; never move books from non-adjacent blocks.
  - Picking is only allowed from adjacent blocks.

If any ambiguity exists, implement the safer behavior (treat as forbidden).

## 2. Source of Truth
Read these files before making changes:
- SPEC_R2_CONTROL.md (system-level requirements and interfaces)
- TASKS.md (implementation plan and acceptance criteria)
- README.md (mechanical procedures like step climbing sequence)

## 3. Workflow
- 1 task = 1 PR-sized change.
- Always run:
  - `colcon build`
  - `colcon test`
- Paste the command outputs in your final summary.
- Prefer small, reviewable commits.

## 4. Repository Layout
- `src/robocon_interfaces/` : custom msg/srv/action definitions
- `src/robocon_plum_planner/` : planner package
- `src/robocon_localization/` : localization + mux/gating
- `src/robocon_motion_primitives/` : action servers for primitives
- `src/robocon_bt_mission/` : BT nodes / bt_navigator integration
- `src/robocon_bringup/` : launch and params

## 5. Definition of Done
A change is done when:
- `colcon build && colcon test` pass
- Code is formatted and warnings are addressed when reasonable
- Planner has unit tests for:
  - "never step onto uncleared book blocks"
  - "pick only from adjacent blocks"
  - "exit condition (10/11/12 and carry>=1)"
  - "special rule for first pick when R2 book is in blocks 1-3"
- Public APIs (msgs/actions) are documented in SPEC_R2_CONTROL.md

## 6. Communication Style
When proposing a plan, provide:
- Files to change
- Commands to run
- Risks/assumptions
Keep outputs concise and actionable.