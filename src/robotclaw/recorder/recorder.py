"""Motion recorder — capture robot poses into a MotionClip."""

from __future__ import annotations

import time

from ..robot import Robot
from .motion_data import Keyframe, MotionClip


class MotionRecorder:
    """Record robot joint positions into a :class:`MotionClip`.

    Typical workflow::

        recorder = MotionRecorder(robot)
        recorder.start_recording("my_motion")

        robot.unload_all()  # Let user freely pose the robot
        input("Pose the robot, then press Enter...")
        recorder.capture_frame()

        input("Next pose...")
        recorder.capture_frame()

        clip = recorder.finish_recording()
        clip.save("motions/my_motion.json")

    Args:
        robot: The :class:`Robot` instance to record from.
    """

    def __init__(self, robot: Robot) -> None:
        self._robot = robot
        self._recording = False
        self._start_time: float = 0.0
        self._name: str = ""
        self._keyframes: list[Keyframe] = []

    @property
    def is_recording(self) -> bool:
        """Whether a recording session is active."""
        return self._recording

    @property
    def frame_count(self) -> int:
        """Number of frames captured so far."""
        return len(self._keyframes)

    def start_recording(self, name: str, description: str = "") -> None:
        """Start a new recording session.

        Args:
            name: Name for this motion clip.
            description: Optional description.

        Raises:
            RuntimeError: If already recording.
        """
        if self._recording:
            raise RuntimeError("Already recording. Call finish_recording() first.")
        self._name = name
        self._description = description
        self._keyframes = []
        self._start_time = time.monotonic()
        self._recording = True

    def capture_frame(self) -> Keyframe:
        """Capture the current robot joint positions as a keyframe.

        Returns:
            The captured :class:`Keyframe`.

        Raises:
            RuntimeError: If not recording.
        """
        if not self._recording:
            raise RuntimeError("Not recording. Call start_recording() first.")

        elapsed_ms = int((time.monotonic() - self._start_time) * 1000)
        positions = self._robot.get_positions()

        # Filter out None values (offline servos)
        clean_positions = {
            name: pos for name, pos in positions.items() if pos is not None
        }

        keyframe = Keyframe(timestamp_ms=elapsed_ms, positions=clean_positions)
        self._keyframes.append(keyframe)
        return keyframe

    def undo_last_frame(self) -> Keyframe | None:
        """Remove and return the last captured keyframe.

        Returns:
            The removed keyframe, or ``None`` if no frames exist.
        """
        if self._keyframes:
            return self._keyframes.pop()
        return None

    def finish_recording(self) -> MotionClip:
        """Finish the recording and return the completed MotionClip.

        Returns:
            The recorded :class:`MotionClip`.

        Raises:
            RuntimeError: If not recording.
        """
        if not self._recording:
            raise RuntimeError("Not recording.")

        clip = MotionClip(
            name=self._name,
            description=getattr(self, "_description", ""),
            keyframes=list(self._keyframes),
        )

        self._recording = False
        self._keyframes = []
        return clip
