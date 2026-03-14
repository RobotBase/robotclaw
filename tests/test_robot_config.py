"""Tests for robot hardware configuration."""

import json
import tempfile
from pathlib import Path

from robotclaw.robot_config import (
    DEFAULT_CONFIG,
    JointConfig,
    LegConfig,
    RobotConfig,
)


class TestJointConfig:
    """Test JointConfig direction and offset mapping."""

    def test_forward_direction(self):
        """Direction=1 should pass through position + offset."""
        joint = JointConfig(servo_id=1, name="test", direction=1, offset=0)
        assert joint.apply_direction(500) == 500

    def test_forward_with_offset(self):
        """Direction=1 with offset should add offset."""
        joint = JointConfig(servo_id=1, name="test", direction=1, offset=10)
        assert joint.apply_direction(500) == 510

    def test_reverse_direction(self):
        """Direction=-1 should reverse the position."""
        joint = JointConfig(
            servo_id=1, name="test",
            min_pos=0, max_pos=1000,
            direction=-1, offset=0,
        )
        result = joint.apply_direction(300)
        assert result == 700  # 1000 - (300 - 0) + 0

    def test_clamping(self):
        """Positions should be clamped to min/max range."""
        joint = JointConfig(
            servo_id=1, name="test",
            min_pos=100, max_pos=900,
            direction=1, offset=200,
        )
        result = joint.apply_direction(800)
        assert result == 900  # 800+200=1000, clamped to 900

    def test_unapply_direction(self):
        """unapply should reverse apply for round-trip."""
        joint = JointConfig(
            servo_id=1, name="test",
            min_pos=0, max_pos=1000,
            direction=1, offset=0,
        )
        pos = 500
        actual = joint.apply_direction(pos)
        restored = joint.unapply_direction(actual)
        assert restored == pos


class TestLegConfig:
    """Test LegConfig joint lookup."""

    def test_get_joint_by_full_name(self):
        """Should find joint by full name."""
        leg = LegConfig(
            name="left",
            joints=[JointConfig(servo_id=1, name="left_knee")],
        )
        assert leg.get_joint("left_knee") is not None

    def test_get_joint_by_short_name(self):
        """Should find joint by name without leg prefix."""
        leg = LegConfig(
            name="left",
            joints=[JointConfig(servo_id=1, name="left_knee")],
        )
        assert leg.get_joint("knee") is not None

    def test_get_joint_not_found(self):
        """Should return None for unknown joint."""
        leg = LegConfig(name="left", joints=[])
        assert leg.get_joint("nonexistent") is None


class TestDefaultConfig:
    """Test the DEFAULT_CONFIG global instance."""

    def test_has_10_joints(self):
        """Default config should have 10 joints total."""
        assert len(DEFAULT_CONFIG.all_joints) == 10

    def test_left_leg_has_5_joints(self):
        assert len(DEFAULT_CONFIG.left_leg.joints) == 5

    def test_right_leg_has_5_joints(self):
        assert len(DEFAULT_CONFIG.right_leg.joints) == 5

    def test_no_duplicate_ids(self):
        """All servo IDs should be unique."""
        ids = DEFAULT_CONFIG.all_servo_ids
        assert len(ids) == len(set(ids))

    def test_ids_are_1_to_10(self):
        """Default IDs should be 1 through 10."""
        ids = sorted(DEFAULT_CONFIG.all_servo_ids)
        assert ids == list(range(1, 11))

    def test_all_joints_have_names(self):
        """Every joint should have a non-empty name."""
        for joint in DEFAULT_CONFIG.all_joints:
            assert joint.name, f"Servo {joint.servo_id} has no name"


class TestConfigSerialization:
    """Test JSON serialization and deserialization."""

    def test_round_trip_dict(self):
        """Config should survive dict round-trip."""
        d = DEFAULT_CONFIG.to_dict()
        restored = RobotConfig.from_dict(d)
        assert len(restored.all_joints) == 10
        assert restored.name == DEFAULT_CONFIG.name

    def test_round_trip_json_file(self):
        """Config should survive JSON file round-trip."""
        with tempfile.TemporaryDirectory() as tmpdir:
            filepath = Path(tmpdir) / "test_config.json"
            DEFAULT_CONFIG.save(filepath)

            assert filepath.exists()
            restored = RobotConfig.load(filepath)
            assert len(restored.all_joints) == 10

    def test_json_valid(self):
        """to_dict output should be valid JSON."""
        d = DEFAULT_CONFIG.to_dict()
        json_str = json.dumps(d)
        parsed = json.loads(json_str)
        assert "left_leg" in parsed
        assert "right_leg" in parsed
