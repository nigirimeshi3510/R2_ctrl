import math

import pytest

from robocon_localization.scan_fuser_core import (
    FuserConfig,
    PolarScan,
    Pose2D,
    compute_bin_count,
    fuse_scans,
)


def _cfg() -> FuserConfig:
    return FuserConfig(
        angle_min=-math.pi / 2.0,
        angle_max=math.pi / 2.0,
        angle_increment=math.pi / 4.0,
        range_min=0.05,
        range_max=10.0,
        use_inf=True,
        inf_epsilon=1.0,
    )


def test_compute_bin_count_inclusive_range():
    assert compute_bin_count(-1.0, 1.0, 0.5) == 5


def test_fuse_scans_chooses_nearest_range_per_bin():
    cfg = _cfg()
    scan1 = PolarScan(
        angle_min=0.0,
        angle_increment=math.pi / 4.0,
        ranges=[2.0],
        range_min=0.05,
        range_max=10.0,
    )
    scan2 = PolarScan(
        angle_min=0.0,
        angle_increment=math.pi / 4.0,
        ranges=[1.0],
        range_min=0.05,
        range_max=10.0,
    )

    out = fuse_scans([(scan1, Pose2D(0.0, 0.0, 0.0)), (scan2, Pose2D(0.0, 0.0, 0.0))], cfg)

    center_idx = 2
    assert out[center_idx] == pytest.approx(1.0)


def test_fuse_scans_applies_pose_rotation_to_binning():
    cfg = _cfg()
    scan = PolarScan(
        angle_min=0.0,
        angle_increment=math.pi / 4.0,
        ranges=[1.0],
        range_min=0.05,
        range_max=10.0,
    )

    out = fuse_scans([(scan, Pose2D(0.0, 0.0, math.pi / 2.0))], cfg)

    plus_90_idx = 4
    assert out[plus_90_idx] == pytest.approx(1.0)


def test_fuse_scans_applies_pose_translation_to_range():
    cfg = _cfg()
    scan = PolarScan(
        angle_min=0.0,
        angle_increment=1.0,
        ranges=[1.0],
        range_min=0.05,
        range_max=10.0,
    )

    out = fuse_scans([(scan, Pose2D(1.0, 0.0, 0.0))], cfg)

    center_idx = 2
    assert out[center_idx] == pytest.approx(2.0)


def test_fuse_scans_angle_range_health_is_reasonable():
    cfg = FuserConfig(
        angle_min=-math.pi,
        angle_max=math.pi,
        angle_increment=math.pi / 180.0,
        range_min=0.05,
        range_max=30.0,
        use_inf=False,
        inf_epsilon=1.0,
    )
    scan = PolarScan(
        angle_min=0.0,
        angle_increment=1.0,
        ranges=[1.0],
        range_min=0.05,
        range_max=10.0,
    )

    out = fuse_scans([(scan, Pose2D(0.0, 0.0, 0.0))], cfg)

    expected_bins = compute_bin_count(cfg.angle_min, cfg.angle_max, cfg.angle_increment)
    assert len(out) == expected_bins
    assert all((math.isfinite(v) and 0.0 < v <= cfg.range_max + cfg.inf_epsilon) for v in out)
