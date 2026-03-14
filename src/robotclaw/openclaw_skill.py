"""OpenClaw skill adapter for robotclaw.

Exposes robot control capabilities as an OpenClaw-compatible skill,
allowing AI agents to control physical robots through natural language.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from .robot import Robot
from .robot_config import DEFAULT_CONFIG, RobotConfig
from .recorder import MotionClip, MotionPlayer, MotionRecorder


@dataclass
class SkillResult:
    """Result of a skill action."""

    success: bool
    message: str
    data: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict:
        return {"success": self.success, "message": self.message, "data": self.data}


class OpenClawSkill:
    """OpenClaw skill adapter for robot control.

    Maps AI agent commands to robot actions. This class can be used
    directly or through the OpenClaw skill framework via SKILL.md.

    Example::

        skill = OpenClawSkill(port="COM3")
        skill.connect()
        result = skill.execute("go_home")
        result = skill.execute("play_motion", motion_name="walk")
        result = skill.execute("scan_status")
        skill.disconnect()
    """

    SUPPORTED_ACTIONS = [
        "go_home",
        "scan_status",
        "set_joint",
        "set_joints",
        "unload_all",
        "load_all",
        "get_positions",
        "play_motion",
        "list_motions",
        "record_start",
        "record_capture",
        "record_finish",
    ]

    def __init__(
        self,
        port: str = "",
        config: RobotConfig = DEFAULT_CONFIG,
        motions_dir: str = "motions",
    ) -> None:
        self.robot = Robot(config=config, port=port)
        self.player = MotionPlayer(self.robot)
        self.recorder = MotionRecorder(self.robot)
        self.motions_dir = Path(motions_dir)

    def connect(self, port: str | None = None) -> SkillResult:
        """Connect to the robot."""
        try:
            self.robot.connect(port=port)
            return SkillResult(True, "Connected to robot.")
        except Exception as e:
            return SkillResult(False, f"Connection failed: {e}")

    def disconnect(self) -> SkillResult:
        """Disconnect from the robot."""
        self.robot.disconnect()
        return SkillResult(True, "Disconnected.")

    def execute(self, action: str, **kwargs: Any) -> SkillResult:
        """Execute a robot action by name.

        Args:
            action: Action name (see :attr:`SUPPORTED_ACTIONS`).
            **kwargs: Action-specific parameters.

        Returns:
            :class:`SkillResult` with success status and data.
        """
        handler = getattr(self, f"_action_{action}", None)
        if handler is None:
            return SkillResult(
                False,
                f"Unknown action: '{action}'. Supported: {self.SUPPORTED_ACTIONS}",
            )
        try:
            return handler(**kwargs)
        except Exception as e:
            return SkillResult(False, f"Action '{action}' failed: {e}")

    # ─── Actions ─────────────────────────────────────────────────

    def _action_go_home(self, time_ms: int = 2000, **_: Any) -> SkillResult:
        self.robot.go_home(time_ms)
        return SkillResult(True, f"All joints moving to home position ({time_ms}ms).")

    def _action_scan_status(self, **_: Any) -> SkillResult:
        statuses = self.robot.scan()
        online = sum(1 for s in statuses if s["online"])
        return SkillResult(
            True,
            f"Scan complete: {online}/{len(statuses)} servos online.",
            data={"statuses": statuses},
        )

    def _action_set_joint(
        self, name: str = "", position: int = 500, time_ms: int = 500, **_: Any
    ) -> SkillResult:
        if not name:
            return SkillResult(False, "Joint name is required.")
        self.robot.set_joint(name, position, time_ms)
        return SkillResult(True, f"Set {name} to {position} ({time_ms}ms).")

    def _action_set_joints(
        self, positions: dict[str, int] | None = None, time_ms: int = 500, **_: Any
    ) -> SkillResult:
        if not positions:
            return SkillResult(False, "Positions dict is required.")
        self.robot.set_joints(positions, time_ms)
        return SkillResult(True, f"Set {len(positions)} joints ({time_ms}ms).")

    def _action_unload_all(self, **_: Any) -> SkillResult:
        self.robot.unload_all()
        return SkillResult(True, "All servos unloaded (torque disabled).")

    def _action_load_all(self, **_: Any) -> SkillResult:
        self.robot.load_all()
        return SkillResult(True, "All servos loaded (torque enabled).")

    def _action_get_positions(self, **_: Any) -> SkillResult:
        positions = self.robot.get_positions()
        return SkillResult(True, "Positions read.", data={"positions": positions})

    def _action_play_motion(
        self, motion_name: str = "", speed: float = 1.0, **_: Any
    ) -> SkillResult:
        if not motion_name:
            return SkillResult(False, "Motion name is required.")

        filepath = self.motions_dir / f"{motion_name}.json"
        if not filepath.exists():
            return SkillResult(False, f"Motion file not found: {filepath}")

        clip = MotionClip.load(filepath)
        self.robot.load_all()
        self.player.play(clip, speed=speed)
        return SkillResult(
            True,
            f"Played '{motion_name}' ({clip.frame_count} frames) at {speed}x speed.",
        )

    def _action_list_motions(self, **_: Any) -> SkillResult:
        if not self.motions_dir.exists():
            return SkillResult(True, "No motions directory.", data={"motions": []})
        files = sorted(self.motions_dir.glob("*.json"))
        names = [f.stem for f in files]
        return SkillResult(True, f"Found {len(names)} motion(s).", data={"motions": names})

    def _action_record_start(self, name: str = "", **_: Any) -> SkillResult:
        if not name:
            return SkillResult(False, "Motion name is required.")
        self.recorder.start_recording(name)
        self.robot.unload_all()
        return SkillResult(True, f"Recording '{name}'. Servos unloaded.")

    def _action_record_capture(self, **_: Any) -> SkillResult:
        frame = self.recorder.capture_frame()
        return SkillResult(
            True,
            f"Frame {self.recorder.frame_count} captured at t={frame.timestamp_ms}ms.",
        )

    def _action_record_finish(self, **_: Any) -> SkillResult:
        clip = self.recorder.finish_recording()
        self.motions_dir.mkdir(parents=True, exist_ok=True)
        filepath = self.motions_dir / f"{clip.name}.json"
        clip.save(filepath)
        self.robot.load_all()
        return SkillResult(
            True,
            f"Saved '{clip.name}' ({clip.frame_count} frames) → {filepath}",
        )

    # ─── Skill Metadata ─────────────────────────────────────────

    @staticmethod
    def get_skill_info() -> dict[str, Any]:
        """Return OpenClaw skill metadata."""
        return {
            "name": "robotclaw",
            "description": "Control LOBOT LX bus servo robots — move joints, record/play motions, scan diagnostics.",
            "version": "0.1.0",
            "actions": OpenClawSkill.SUPPORTED_ACTIONS,
        }
