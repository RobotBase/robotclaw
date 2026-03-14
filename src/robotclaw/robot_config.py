"""Robot hardware configuration data classes.

Defines the joint, leg, and full robot configuration using simple
dataclasses. Supports JSON serialization for easy config file management.
"""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field
from pathlib import Path


@dataclass
class JointConfig:
    """Configuration for a single servo joint.

    Attributes:
        servo_id: Servo bus ID (0-253).
        name: Human-readable joint name, e.g. ``"left_hip_pitch"``.
        min_pos: Minimum allowed position (0-1000).
        max_pos: Maximum allowed position (0-1000).
        home_pos: Home/neutral position.
        direction: Direction multiplier (1 = normal, -1 = reversed).
        offset: Calibration offset value.
    """

    servo_id: int
    name: str
    min_pos: int = 0
    max_pos: int = 1000
    home_pos: int = 500
    direction: int = 1
    offset: int = 0

    def apply_direction(self, position: int) -> int:
        """Apply direction and offset mapping to a logical position.

        Converts a logical position (where higher = forward for all joints)
        to the actual servo position value.
        """
        if self.direction == -1:
            actual = self.max_pos - (position - self.min_pos) + self.offset
        else:
            actual = position + self.offset
        return max(self.min_pos, min(self.max_pos, actual))

    def unapply_direction(self, actual_position: int) -> int:
        """Reverse direction and offset mapping from actual servo position.

        Converts the raw servo position value back to logical position.
        """
        if self.direction == -1:
            logical = self.max_pos - (actual_position - self.offset - self.min_pos)
        else:
            logical = actual_position - self.offset
        return max(self.min_pos, min(self.max_pos, logical))


@dataclass
class LegConfig:
    """Configuration for one robot leg.

    Attributes:
        name: Leg name, e.g. ``"left"`` or ``"right"``.
        joints: List of joint configurations for this leg.
    """

    name: str
    joints: list[JointConfig] = field(default_factory=list)

    def get_joint(self, joint_name: str) -> JointConfig | None:
        """Find a joint by name (searches with or without leg prefix)."""
        for j in self.joints:
            if j.name == joint_name or j.name == f"{self.name}_{joint_name}":
                return j
        return None


@dataclass
class RobotConfig:
    """Complete robot hardware configuration.

    Attributes:
        name: Robot configuration name.
        left_leg: Left leg configuration.
        right_leg: Right leg configuration.
    """

    name: str = "default_biped"
    left_leg: LegConfig = field(default_factory=lambda: LegConfig("left"))
    right_leg: LegConfig = field(default_factory=lambda: LegConfig("right"))

    @property
    def all_joints(self) -> list[JointConfig]:
        """Return all joints from both legs."""
        return self.left_leg.joints + self.right_leg.joints

    @property
    def all_servo_ids(self) -> list[int]:
        """Return all servo IDs."""
        return [j.servo_id for j in self.all_joints]

    def get_joint(self, name: str) -> JointConfig | None:
        """Find a joint by name across all legs."""
        for leg in [self.left_leg, self.right_leg]:
            joint = leg.get_joint(name)
            if joint is not None:
                return joint
        return None

    def to_dict(self) -> dict:
        """Serialize config to a dictionary."""
        return asdict(self)

    def save(self, filepath: str | Path) -> None:
        """Save configuration to a JSON file."""
        path = Path(filepath)
        path.parent.mkdir(parents=True, exist_ok=True)
        with open(path, "w", encoding="utf-8") as f:
            json.dump(self.to_dict(), f, indent=2, ensure_ascii=False)

    @classmethod
    def from_dict(cls, data: dict) -> RobotConfig:
        """Deserialize config from a dictionary."""
        left_joints = [JointConfig(**j) for j in data.get("left_leg", {}).get("joints", [])]
        right_joints = [JointConfig(**j) for j in data.get("right_leg", {}).get("joints", [])]
        return cls(
            name=data.get("name", "custom"),
            left_leg=LegConfig(
                name=data.get("left_leg", {}).get("name", "left"),
                joints=left_joints,
            ),
            right_leg=LegConfig(
                name=data.get("right_leg", {}).get("name", "right"),
                joints=right_joints,
            ),
        )

    @classmethod
    def load(cls, filepath: str | Path) -> RobotConfig:
        """Load configuration from a JSON file."""
        with open(filepath, encoding="utf-8") as f:
            data = json.load(f)
        return cls.from_dict(data)


# ─── Default Configuration ───────────────────────────────────────────
# 10 servos, 5 per leg (biped robot lower body)
# Left leg: IDs 1-5, Right leg: IDs 6-10
DEFAULT_CONFIG = RobotConfig(
    name="default_biped_10s",
    left_leg=LegConfig(
        name="left",
        joints=[
            JointConfig(servo_id=1, name="left_hip_yaw",     home_pos=500),  # 髋侧摆
            JointConfig(servo_id=2, name="left_hip_pitch",    home_pos=500),  # 髋前摆
            JointConfig(servo_id=3, name="left_knee",         home_pos=500),  # 膝关节
            JointConfig(servo_id=4, name="left_ankle_pitch",  home_pos=500),  # 踝前摆
            JointConfig(servo_id=5, name="left_ankle_roll",   home_pos=500),  # 踝侧摆
        ],
    ),
    right_leg=LegConfig(
        name="right",
        joints=[
            JointConfig(servo_id=6,  name="right_hip_yaw",    home_pos=500),
            JointConfig(servo_id=7,  name="right_hip_pitch",   home_pos=500),
            JointConfig(servo_id=8,  name="right_knee",        home_pos=500),
            JointConfig(servo_id=9,  name="right_ankle_pitch", home_pos=500),
            JointConfig(servo_id=10, name="right_ankle_roll",  home_pos=500),
        ],
    ),
)
