# r2_sldasm_description

ROS 2 Humble description package for `r2_sldasm`.

## Run

```bash
ros2 launch r2_sldasm_description display.launch.py
```

```bash
ros2 launch r2_sldasm_description gz_sim.launch.py
```

## Notes

- Coordinate convention follows REP-103 (`base_link`: x forward, y left, z up).
- `urdf/r2_sldasm.urdf.xacro` now references lightweight meshes in `meshes_low/` for RViz responsiveness.
- `fl_lift_jouint` has been normalized to `fl_lift_joint`.
- `r_lift_link` inertia is a temporary copy of `fr_lift_link` values.
- Lift temporary limits and drive values:
  - stroke: `-0.39 .. 0.0` m
  - effort: `300` N
  - velocity: `0.05` m/s
- Wheel and subwheel limits are `-pi .. +pi` with velocity `2pi` rad/s.

## TODO (replace with measured values)

- Exact inertia and COM for `r_lift_link`
- Lift axis confirmation for all lift joints against real hardware
- Wheel/subwheel effort limits from motor + gearbox specs

## Regenerate lightweight meshes

```bash
blender --background --python scripts/simplify_meshes_blender.py -- meshes meshes_low 0.01
```
