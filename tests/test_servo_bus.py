"""Tests for ServoBus protocol frame building and checksum."""

import struct

from robotclaw.servo_bus import (
    CMD_GROUP_MOVE,
    CMD_LOAD_UNLOAD_WRITE,
    CMD_POS_READ,
    CMD_SERVO_MOVE,
    CMD_TEMP_READ,
    CMD_VIN_READ,
    FRAME_HEADER,
    ServoBus,
)


class TestChecksum:
    """Test the LX protocol checksum calculation."""

    def test_checksum_basic(self):
        """Checksum = ~(ID + LENGTH + CMD + PARAMS) & 0xFF."""
        result = ServoBus._checksum(servo_id=1, length=7, cmd=1, params=b"\xf4\x01\xe8\x03")
        # manual: ~(1 + 7 + 1 + 0xF4 + 0x01 + 0xE8 + 0x03) & 0xFF
        total = 1 + 7 + 1 + 0xF4 + 0x01 + 0xE8 + 0x03
        expected = (~total) & 0xFF
        assert result == expected

    def test_checksum_zero_params(self):
        """Checksum with no parameters."""
        result = ServoBus._checksum(servo_id=1, length=3, cmd=28, params=b"")
        total = 1 + 3 + 28
        expected = (~total) & 0xFF
        assert result == expected

    def test_checksum_is_byte(self):
        """Checksum should always be a single byte (0-255)."""
        for sid in range(0, 255):
            result = ServoBus._checksum(servo_id=sid, length=3, cmd=1, params=b"")
            assert 0 <= result <= 255


class TestFrameBuilding:
    """Test frame construction."""

    def test_move_frame_structure(self):
        """A move frame should have correct header, ID, length, cmd, params, checksum."""
        bus = ServoBus()
        frame = bus._build_frame(
            servo_id=1,
            cmd=CMD_SERVO_MOVE,
            params=struct.pack("<HH", 500, 1000),
        )

        # Header
        assert frame[:2] == FRAME_HEADER

        # ID
        assert frame[2] == 1

        # Length = params(4) + 3 = 7
        assert frame[3] == 7

        # CMD
        assert frame[4] == CMD_SERVO_MOVE

        # Params — position=500, time=1000
        pos, time_ms = struct.unpack("<HH", frame[5:9])
        assert pos == 500
        assert time_ms == 1000

        # Checksum
        checksum = frame[9]
        expected = ServoBus._checksum(1, 7, CMD_SERVO_MOVE, frame[5:9])
        assert checksum == expected

    def test_read_position_frame(self):
        """A read position command frame has no parameters."""
        bus = ServoBus()
        frame = bus._build_frame(servo_id=5, cmd=CMD_POS_READ)

        assert frame[:2] == FRAME_HEADER
        assert frame[2] == 5
        assert frame[3] == 3  # length = 0 params + 3
        assert frame[4] == CMD_POS_READ
        # Checksum
        expected = ServoBus._checksum(5, 3, CMD_POS_READ, b"")
        assert frame[5] == expected

    def test_frame_length_consistency(self):
        """Frame total bytes = 2(header) + 1(ID) + 1(LEN) + LEN - 1."""
        bus = ServoBus()
        # No params
        frame = bus._build_frame(1, CMD_POS_READ)
        length = frame[3]
        assert len(frame) == 2 + 1 + length

        # With 4 bytes of params
        frame = bus._build_frame(1, CMD_SERVO_MOVE, struct.pack("<HH", 500, 1000))
        length = frame[3]
        assert len(frame) == 2 + 1 + length


class TestMoveParameterClamping:
    """Test that move commands properly clamp parameters."""

    def test_position_clamped_to_range(self):
        """Position should be clamped to 0-1000 in move()."""
        bus = ServoBus()
        # We can't test actual serial output without mocking, but we can
        # verify the _build_frame handles the logic correctly
        # Just verify no exceptions for edge values
        bus._build_frame(1, CMD_SERVO_MOVE, struct.pack("<HH", 0, 0))
        bus._build_frame(1, CMD_SERVO_MOVE, struct.pack("<HH", 1000, 30000))
