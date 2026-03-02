"""Core LaserScan fusion utilities used by scan_fuser node."""

from __future__ import annotations

from dataclasses import dataclass
import math


@dataclass(frozen=True)
class PolarScan:
    """Scan represented in polar coordinates in its local frame."""

    angle_min: float
    angle_increment: float
    ranges: list[float]
    range_min: float
    range_max: float


@dataclass(frozen=True)
class Pose2D:
    """Rigid transform from scan frame to target frame."""

    x: float
    y: float
    yaw: float


@dataclass(frozen=True)
class FuserConfig:
    """Configuration for angle binning and output range handling."""

    angle_min: float
    angle_max: float
    angle_increment: float
    range_min: float
    range_max: float
    use_inf: bool = True
    inf_epsilon: float = 1.0


def compute_bin_count(angle_min: float, angle_max: float, angle_increment: float) -> int:
    """Return number of bins for inclusive [angle_min, angle_max]."""
    if angle_increment <= 0.0:
        raise ValueError("angle_increment must be > 0")
    if angle_max <= angle_min:
        raise ValueError("angle_max must be > angle_min")

    span = angle_max - angle_min
    steps = int(round(span / angle_increment))
    if steps <= 0:
        raise ValueError("angle range too small for selected increment")
    return steps + 1


def _point_to_bin(angle: float, cfg: FuserConfig, bin_count: int) -> int | None:
    if angle < cfg.angle_min or angle > cfg.angle_max:
        return None
    idx = int(round((angle - cfg.angle_min) / cfg.angle_increment))
    if idx < 0 or idx >= bin_count:
        return None
    return idx


def fuse_scans(
    scan_inputs: list[tuple[PolarScan, Pose2D]],
    cfg: FuserConfig,
) -> list[float]:
    """Fuse transformed scans into one angularly-binned range array.

    For each output bin, the closest valid point from all inputs is selected.
    """
    if cfg.range_min <= 0.0 or cfg.range_max <= cfg.range_min:
        raise ValueError("invalid output range limits")
    if cfg.use_inf:
        default_val = math.inf
    else:
        default_val = cfg.range_max + abs(cfg.inf_epsilon)

    bin_count = compute_bin_count(cfg.angle_min, cfg.angle_max, cfg.angle_increment)
    out_ranges = [default_val] * bin_count

    for scan, pose in scan_inputs:
        cos_yaw = math.cos(pose.yaw)
        sin_yaw = math.sin(pose.yaw)

        for i, rng in enumerate(scan.ranges):
            if not math.isfinite(rng):
                continue
            if rng < scan.range_min or rng > scan.range_max:
                continue

            angle_local = scan.angle_min + (i * scan.angle_increment)
            x_local = rng * math.cos(angle_local)
            y_local = rng * math.sin(angle_local)

            x_target = pose.x + (cos_yaw * x_local) - (sin_yaw * y_local)
            y_target = pose.y + (sin_yaw * x_local) + (cos_yaw * y_local)

            range_target = math.hypot(x_target, y_target)
            if range_target < cfg.range_min or range_target > cfg.range_max:
                continue

            angle_target = math.atan2(y_target, x_target)
            idx = _point_to_bin(angle_target, cfg, bin_count)
            if idx is None:
                continue

            current = out_ranges[idx]
            if not math.isfinite(current) or range_target < current:
                out_ranges[idx] = range_target

    return out_ranges
