"""Motion player — playback recorded MotionClips with variable speed."""

from __future__ import annotations

import threading
import time

from ..robot import Robot
from .motion_data import MotionClip


class MotionPlayer:
    """Play back recorded :class:`MotionClip` sequences.

    Supports variable speed playback and loop control::

        player = MotionPlayer(robot)
        player.play(clip, speed=1.5)       # 1.5x speed
        player.play_loop(clip, count=3)    # Loop 3 times
        player.stop()                       # Stop playback

    Args:
        robot: The :class:`Robot` instance to control.
    """

    def __init__(self, robot: Robot) -> None:
        self._robot = robot
        self._playing = False
        self._stop_event = threading.Event()

    @property
    def is_playing(self) -> bool:
        """Whether playback is currently active."""
        return self._playing

    def play(self, clip: MotionClip, speed: float = 1.0) -> None:
        """Play a motion clip at the given speed.

        Blocks until playback completes or :meth:`stop` is called.

        Args:
            clip: The motion clip to play.
            speed: Speed multiplier (1.0 = normal, 2.0 = double, 0.5 = half).

        Raises:
            ValueError: If the clip has fewer than 2 keyframes or speed <= 0.
        """
        if speed <= 0:
            raise ValueError("Speed must be positive.")
        if clip.frame_count < 2:
            raise ValueError("Motion clip must have at least 2 keyframes.")

        self._stop_event.clear()
        self._playing = True

        try:
            self._execute_clip(clip, speed)
        finally:
            self._playing = False

    def play_loop(
        self,
        clip: MotionClip,
        speed: float = 1.0,
        count: int = 0,
    ) -> None:
        """Play a motion clip in a loop.

        Args:
            clip: The motion clip to play.
            speed: Speed multiplier.
            count: Number of loops (0 = infinite until :meth:`stop` is called).
        """
        self._stop_event.clear()
        self._playing = True

        try:
            iteration = 0
            while not self._stop_event.is_set():
                self._execute_clip(clip, speed)
                iteration += 1
                if count > 0 and iteration >= count:
                    break
        finally:
            self._playing = False

    def stop(self) -> None:
        """Stop the current playback."""
        self._stop_event.set()

    def play_async(self, clip: MotionClip, speed: float = 1.0) -> threading.Thread:
        """Play a motion clip on a background thread.

        Returns:
            The background thread running the playback.
        """
        thread = threading.Thread(
            target=self.play, args=(clip, speed), daemon=True
        )
        thread.start()
        return thread

    def _execute_clip(self, clip: MotionClip, speed: float) -> None:
        """Internal: execute a single pass through the clip keyframes."""
        keyframes = clip.keyframes

        for i in range(len(keyframes)):
            if self._stop_event.is_set():
                return

            frame = keyframes[i]

            # Calculate movement time to next frame
            if i < len(keyframes) - 1:
                next_frame = keyframes[i + 1]
                interval_ms = next_frame.timestamp_ms - frame.timestamp_ms
                move_time_ms = max(1, int(interval_ms / speed))
            else:
                move_time_ms = 500  # Default for last frame

            # Send joint positions
            if frame.positions:
                self._robot.set_joints(frame.positions, time_ms=move_time_ms)

            # Wait for movement to complete before next frame
            if i < len(keyframes) - 1:
                sleep_time = move_time_ms / 1000.0
                wait_end = time.monotonic() + sleep_time
                while time.monotonic() < wait_end:
                    if self._stop_event.is_set():
                        return
                    time.sleep(min(0.05, wait_end - time.monotonic()))
