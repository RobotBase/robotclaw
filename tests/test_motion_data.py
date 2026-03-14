"""Tests for motion data models."""

import json
import tempfile
from pathlib import Path

from robotclaw.recorder.motion_data import Keyframe, MotionClip


class TestKeyframe:
    """Test Keyframe data class."""

    def test_creation(self):
        kf = Keyframe(timestamp_ms=0, positions={"left_knee": 500})
        assert kf.timestamp_ms == 0
        assert kf.positions["left_knee"] == 500

    def test_default_positions(self):
        kf = Keyframe(timestamp_ms=100)
        assert kf.positions == {}


class TestMotionClip:
    """Test MotionClip data model."""

    def _sample_clip(self) -> MotionClip:
        return MotionClip(
            name="test_motion",
            description="A test motion",
            keyframes=[
                Keyframe(timestamp_ms=0, positions={"left_knee": 500, "right_knee": 500}),
                Keyframe(timestamp_ms=500, positions={"left_knee": 300, "right_knee": 700}),
                Keyframe(timestamp_ms=1000, positions={"left_knee": 500, "right_knee": 500}),
            ],
        )

    def test_frame_count(self):
        clip = self._sample_clip()
        assert clip.frame_count == 3

    def test_total_duration(self):
        clip = self._sample_clip()
        assert clip.total_duration_ms == 1000

    def test_empty_clip_duration(self):
        clip = MotionClip(name="empty")
        assert clip.total_duration_ms == 0
        assert clip.frame_count == 0

    def test_created_at_auto_set(self):
        clip = MotionClip(name="auto")
        assert clip.created_at != ""

    def test_to_dict(self):
        clip = self._sample_clip()
        d = clip.to_dict()
        assert d["name"] == "test_motion"
        assert d["frame_count"] == 3
        assert d["total_duration_ms"] == 1000
        assert len(d["keyframes"]) == 3

    def test_round_trip_dict(self):
        clip = self._sample_clip()
        d = clip.to_dict()
        restored = MotionClip.from_dict(d)
        assert restored.name == clip.name
        assert restored.frame_count == clip.frame_count
        assert restored.keyframes[1].positions["left_knee"] == 300

    def test_round_trip_json_file(self):
        clip = self._sample_clip()
        with tempfile.TemporaryDirectory() as tmpdir:
            filepath = Path(tmpdir) / "test.json"
            clip.save(filepath)

            assert filepath.exists()
            loaded = MotionClip.load(filepath)
            assert loaded.name == "test_motion"
            assert loaded.frame_count == 3

    def test_json_valid(self):
        clip = self._sample_clip()
        d = clip.to_dict()
        json_str = json.dumps(d)
        parsed = json.loads(json_str)
        assert parsed["name"] == "test_motion"


class TestSpeedScaling:
    """Test motion playback speed calculations."""

    def test_interval_at_normal_speed(self):
        """At speed=1.0, intervals should be unchanged."""
        clip = MotionClip(
            name="test",
            keyframes=[
                Keyframe(timestamp_ms=0, positions={}),
                Keyframe(timestamp_ms=1000, positions={}),
            ],
        )
        interval_ms = clip.keyframes[1].timestamp_ms - clip.keyframes[0].timestamp_ms
        speed = 1.0
        actual_ms = int(interval_ms / speed)
        assert actual_ms == 1000

    def test_interval_at_double_speed(self):
        """At speed=2.0, intervals should be halved."""
        interval_ms = 1000
        speed = 2.0
        actual_ms = int(interval_ms / speed)
        assert actual_ms == 500

    def test_interval_at_half_speed(self):
        """At speed=0.5, intervals should be doubled."""
        interval_ms = 1000
        speed = 0.5
        actual_ms = int(interval_ms / speed)
        assert actual_ms == 2000
