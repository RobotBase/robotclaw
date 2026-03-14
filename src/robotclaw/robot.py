"""High-level robot controller.

Provides a user-friendly API for controlling a biped servo robot,
with automatic direction/offset mapping and context manager support.
"""

from __future__ import annotations

from typing import Any

from .robot_config import RobotConfig, DEFAULT_CONFIG
from .servo_bus import ServoBus


class Robot:
    """High-level robot controller built on :class:`ServoBus`.

    Supports the context manager protocol for clean resource management::

        with Robot(config=DEFAULT_CONFIG, port="COM3") as robot:
            robot.go_home(2000)
            print(robot.get_positions())

    Args:
        config: Robot hardware configuration.
        port: Serial port name (e.g. ``"COM3"``).
        baudrate: Serial baud rate (default 115200).
    """

    def __init__(
        self,
        config: RobotConfig = DEFAULT_CONFIG,
        port: str = "",
        baudrate: int = 115200,
    ) -> None:
        self.config = config
        self.port = port
        self.baudrate = baudrate
        self.bus = ServoBus()

    # ─── Context Manager ─────────────────────────────────────────

    def __enter__(self) -> Robot:
        self.connect()
        return self

    def __exit__(self, *args: Any) -> None:
        self.disconnect()

    # ─── Connection ──────────────────────────────────────────────

    def connect(self, port: str | None = None, baudrate: int | None = None) -> None:
        """Connect to the servo bus.

        Args:
            port: Override the port set in constructor.
            baudrate: Override the baudrate set in constructor.
        """
        self.bus.connect(
            port=port or self.port,
            baudrate=baudrate or self.baudrate,
        )

    def disconnect(self) -> None:
        """Disconnect from the servo bus."""
        self.bus.disconnect()

    @property
    def is_connected(self) -> bool:
        """Whether currently connected to the servo bus."""
        return self.bus.is_connected

    # ─── Joint Control ───────────────────────────────────────────

    def go_home(self, time_ms: int = 2000) -> None:
        """Move all joints to their home (neutral) position.

        Args:
            time_ms: Duration of the movement in milliseconds.
        """
        moves = [
            (joint.servo_id, joint.home_pos)
            for joint in self.config.all_joints
        ]
        self.bus.move_multiple(moves, time_ms)

    def set_joint(self, name: str, position: int, time_ms: int = 500) -> None:
        """Set a single joint to a target position.

        Automatically applies direction and offset mapping from the config.

        Args:
            name: Joint name (e.g. ``"left_hip_pitch"``).
            position: Logical position value (0-1000).
            time_ms: Duration of the movement in milliseconds.

        Raises:
            ValueError: If the joint name is not found.
        """
        joint = self.config.get_joint(name)
        if joint is None:
            raise ValueError(
                f"Joint '{name}' not found. Available: "
                f"{[j.name for j in self.config.all_joints]}"
            )
        actual_pos = joint.apply_direction(position)
        self.bus.move(joint.servo_id, actual_pos, time_ms)

    def set_joints(self, positions: dict[str, int], time_ms: int = 500) -> None:
        """Set multiple joints simultaneously.

        Args:
            positions: Dict of ``{joint_name: position}``.
            time_ms: Duration of the movement in milliseconds.

        Raises:
            ValueError: If any joint name is not found.
        """
        moves: list[tuple[int, int]] = []
        for name, pos in positions.items():
            joint = self.config.get_joint(name)
            if joint is None:
                raise ValueError(
                    f"Joint '{name}' not found. Available: "
                    f"{[j.name for j in self.config.all_joints]}"
                )
            actual_pos = joint.apply_direction(pos)
            moves.append((joint.servo_id, actual_pos))
        self.bus.move_multiple(moves, time_ms)

    # ─── Position Reading ────────────────────────────────────────

    def get_positions(self) -> dict[str, int | None]:
        """Read current positions of all joints.

        Returns:
            Dict of ``{joint_name: logical_position}``.
            Position is ``None`` if a servo did not respond.
        """
        result: dict[str, int | None] = {}
        for joint in self.config.all_joints:
            raw_pos = self.bus.read_position(joint.servo_id)
            if raw_pos is not None:
                result[joint.name] = joint.unapply_direction(raw_pos)
            else:
                result[joint.name] = None
        return result

    # ─── Load / Unload ───────────────────────────────────────────

    def unload_all(self) -> None:
        """Unload (disable torque) on all servos.

        This allows the user to freely move the robot's joints by hand,
        which is useful for motion teaching/recording.
        """
        for joint in self.config.all_joints:
            self.bus.unload(joint.servo_id)

    def load_all(self) -> None:
        """Load (enable torque) on all servos."""
        for joint in self.config.all_joints:
            self.bus.load(joint.servo_id)

    # ─── Diagnostics ─────────────────────────────────────────────

    def scan(self) -> list[dict[str, Any]]:
        """Scan all configured servos and return their status.

        Returns:
            List of dicts with servo status information including
            joint name, ID, position, voltage, temperature, and online status.
        """
        results: list[dict[str, Any]] = []
        for joint in self.config.all_joints:
            pos = self.bus.read_position(joint.servo_id)
            online = pos is not None
            status: dict[str, Any] = {
                "joint_name": joint.name,
                "servo_id": joint.servo_id,
                "online": online,
                "position": pos,
            }
            if online:
                status["voltage_mv"] = self.bus.read_voltage(joint.servo_id)
                status["temperature_c"] = self.bus.read_temperature(joint.servo_id)
            results.append(status)
        return results
