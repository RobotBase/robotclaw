"""Motion data models — Keyframe and MotionClip with JSON serialization."""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path


@dataclass
class Keyframe:
    """A single recorded frame capturing all joint positions at a moment.

    Attributes:
        timestamp_ms: Time in milliseconds since recording started.
        positions: Dict of ``{joint_name: position_value}``.
    """

    timestamp_ms: int
    positions: dict[str, int] = field(default_factory=dict)


@dataclass
class MotionClip:
    """A recorded motion sequence consisting of multiple keyframes.

    Attributes:
        name: Motion name (e.g. ``"walk_cycle_v1"``).
        description: Human-readable description.
        created_at: ISO-8601 creation timestamp.
        keyframes: Ordered list of keyframes.
    """

    name: str
    description: str = ""
    created_at: str = ""
    keyframes: list[Keyframe] = field(default_factory=list)

    def __post_init__(self) -> None:
        if not self.created_at:
            self.created_at = datetime.now(timezone.utc).isoformat()

    @property
    def frame_count(self) -> int:
        """Number of keyframes in this clip."""
        return len(self.keyframes)

    @property
    def total_duration_ms(self) -> int:
        """Total duration in milliseconds."""
        if not self.keyframes:
            return 0
        return self.keyframes[-1].timestamp_ms - self.keyframes[0].timestamp_ms

    def to_dict(self) -> dict:
        """Serialize to dictionary."""
        data = asdict(self)
        data["frame_count"] = self.frame_count
        data["total_duration_ms"] = self.total_duration_ms
        return data

    @classmethod
    def from_dict(cls, data: dict) -> MotionClip:
        """Deserialize from dictionary."""
        keyframes = [
            Keyframe(
                timestamp_ms=kf["timestamp_ms"],
                positions=kf["positions"],
            )
            for kf in data.get("keyframes", [])
        ]
        return cls(
            name=data.get("name", "unnamed"),
            description=data.get("description", ""),
            created_at=data.get("created_at", ""),
            keyframes=keyframes,
        )

    def save(self, filepath: str | Path) -> None:
        """Save motion clip to a JSON file."""
        path = Path(filepath)
        path.parent.mkdir(parents=True, exist_ok=True)
        with open(path, "w", encoding="utf-8") as f:
            json.dump(self.to_dict(), f, indent=2, ensure_ascii=False)

    @classmethod
    def load(cls, filepath: str | Path) -> MotionClip:
        """Load motion clip from a JSON file."""
        with open(filepath, encoding="utf-8") as f:
            data = json.load(f)
        return cls.from_dict(data)
