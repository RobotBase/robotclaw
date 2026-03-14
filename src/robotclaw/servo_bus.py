"""LOBOT LX series serial bus servo protocol driver.

Implements the full LOBOT LX protocol for communicating with LX-16A,
LX-224, LX-225 and compatible bus servos over a half-duplex serial link.

Frame format:
    0x55 0x55 ID LENGTH CMD [PARAMS...] CHECKSUM

Where CHECKSUM = ~(ID + LENGTH + CMD + PARAMS...) & 0xFF
"""

from __future__ import annotations

import struct
import threading
import time
from typing import NamedTuple

import serial


# ─── Protocol Constants ─────────────────────────────────────────────
FRAME_HEADER = bytes([0x55, 0x55])

# Command IDs
CMD_SERVO_MOVE = 1
CMD_GROUP_MOVE = 3
CMD_ID_READ = 14
CMD_ID_WRITE = 13
CMD_ANGLE_OFFSET_ADJUST = 17
CMD_ANGLE_OFFSET_WRITE = 18
CMD_ANGLE_OFFSET_READ = 19
CMD_ANGLE_LIMIT_WRITE = 20
CMD_ANGLE_LIMIT_READ = 21
CMD_VIN_LIMIT_WRITE = 22
CMD_VIN_LIMIT_READ = 23
CMD_TEMP_MAX_LIMIT_WRITE = 24
CMD_TEMP_MAX_LIMIT_READ = 25
CMD_TEMP_READ = 26
CMD_VIN_READ = 27
CMD_POS_READ = 28
CMD_SERVO_MODE_WRITE = 29
CMD_SERVO_MODE_READ = 30
CMD_LOAD_UNLOAD_WRITE = 31
CMD_LOAD_UNLOAD_READ = 32
CMD_LED_CTRL_WRITE = 33
CMD_LED_CTRL_READ = 34
CMD_LED_ERROR_WRITE = 35
CMD_LED_ERROR_READ = 36

# Broadcast ID — all servos respond
BROADCAST_ID = 254

# Default serial settings
DEFAULT_BAUDRATE = 115200
DEFAULT_TIMEOUT = 0.1  # seconds


class ServoStatus(NamedTuple):
    """Status snapshot of a single servo."""

    servo_id: int
    position: int
    voltage_mv: int
    temperature_c: int


class ServoBus:
    """Low-level driver for LOBOT LX serial bus servos.

    Thread-safe — all serial operations are protected by a mutex lock.

    Usage::

        bus = ServoBus()
        bus.connect("COM3")
        bus.move(1, 500, 1000)
        pos = bus.read_position(1)
        bus.disconnect()
    """

    def __init__(self) -> None:
        self._serial: serial.Serial | None = None
        self._lock = threading.Lock()

    @property
    def is_connected(self) -> bool:
        """Whether the serial port is currently open."""
        return self._serial is not None and self._serial.is_open

    # ─── Connection ──────────────────────────────────────────────

    def connect(
        self,
        port: str,
        baudrate: int = DEFAULT_BAUDRATE,
        timeout: float = DEFAULT_TIMEOUT,
    ) -> None:
        """Open the serial port and connect to the servo bus.

        Args:
            port: Serial port name, e.g. ``"COM3"`` or ``"/dev/ttyUSB0"``.
            baudrate: Baud rate (default 115200 for direct LX connection).
            timeout: Read timeout in seconds.

        Raises:
            serial.SerialException: If the port cannot be opened.
        """
        with self._lock:
            if self._serial and self._serial.is_open:
                self._serial.close()
            self._serial = serial.Serial(
                port=port,
                baudrate=baudrate,
                timeout=timeout,
                bytesize=serial.EIGHTBITS,
                parity=serial.PARITY_NONE,
                stopbits=serial.STOPBITS_ONE,
            )

    def disconnect(self) -> None:
        """Close the serial port."""
        with self._lock:
            if self._serial and self._serial.is_open:
                self._serial.close()
            self._serial = None

    # ─── Checksum ────────────────────────────────────────────────

    @staticmethod
    def _checksum(servo_id: int, length: int, cmd: int, params: bytes) -> int:
        """Calculate LX protocol checksum.

        checksum = ~(ID + LENGTH + CMD + PARAMS...) & 0xFF
        """
        total = servo_id + length + cmd + sum(params)
        return (~total) & 0xFF

    # ─── Frame Building ──────────────────────────────────────────

    def _build_frame(self, servo_id: int, cmd: int, params: bytes = b"") -> bytes:
        """Build a complete LX protocol frame.

        Returns:
            Complete frame bytes ready to send.
        """
        length = len(params) + 3  # length includes ID, LEN, CMD bytes
        checksum = self._checksum(servo_id, length, cmd, params)
        return FRAME_HEADER + bytes([servo_id, length, cmd]) + params + bytes([checksum])

    # ─── Low-Level I/O ───────────────────────────────────────────

    def _send(self, frame: bytes) -> None:
        """Send a frame over the serial port.

        Raises:
            ConnectionError: If not connected.
        """
        if not self._serial or not self._serial.is_open:
            raise ConnectionError("ServoBus is not connected. Call connect() first.")
        self._serial.flushInput()
        self._serial.write(frame)
        self._serial.flush()

    def _recv(self, servo_id: int, cmd: int) -> bytes | None:
        """Receive a response frame from a servo.

        Returns:
            Parameter bytes from the response, or None on timeout.
        """
        if not self._serial or not self._serial.is_open:
            raise ConnectionError("ServoBus is not connected. Call connect() first.")

        # Read header (2 bytes: 0x55 0x55)
        header = self._serial.read(2)
        if len(header) < 2 or header != FRAME_HEADER:
            return None

        # Read ID + LENGTH
        id_len = self._serial.read(2)
        if len(id_len) < 2:
            return None

        resp_id = id_len[0]
        resp_len = id_len[1]

        # Read remaining bytes (CMD + PARAMS + CHECKSUM)
        remaining = self._serial.read(resp_len - 1)  # -1 because length includes itself
        if len(remaining) < resp_len - 1:
            return None

        resp_cmd = remaining[0]
        params = remaining[1:-1]
        resp_checksum = remaining[-1]

        # Validate checksum
        expected = self._checksum(resp_id, resp_len, resp_cmd, params)
        if resp_checksum != expected:
            return None

        return params

    # ─── Movement Commands ───────────────────────────────────────

    def move(self, servo_id: int, position: int, time_ms: int = 0) -> None:
        """Move a single servo to a target position.

        Args:
            servo_id: Servo ID (0-253).
            position: Target position (0-1000).
            time_ms: Movement duration in milliseconds (0-30000).
        """
        position = max(0, min(1000, position))
        time_ms = max(0, min(30000, time_ms))
        params = struct.pack("<HH", position, time_ms)
        frame = self._build_frame(servo_id, CMD_SERVO_MOVE, params)
        with self._lock:
            self._send(frame)

    def move_multiple(
        self, moves: list[tuple[int, int]], time_ms: int = 0
    ) -> None:
        """Move multiple servos simultaneously.

        Args:
            moves: List of (servo_id, position) tuples.
            time_ms: Movement duration in milliseconds (shared).
        """
        count = len(moves)
        time_ms = max(0, min(30000, time_ms))

        # Build params: count, time(2), [id, pos_low, pos_high] * count
        params = struct.pack("<BH", count, time_ms)
        for sid, pos in moves:
            pos = max(0, min(1000, pos))
            params += struct.pack("<BH", sid, pos)

        frame = self._build_frame(BROADCAST_ID, CMD_GROUP_MOVE, params)
        with self._lock:
            self._send(frame)

    # ─── Read Commands ───────────────────────────────────────────

    def read_position(self, servo_id: int) -> int | None:
        """Read the current position of a servo.

        Args:
            servo_id: Servo ID.

        Returns:
            Position value (0-1000), or None on timeout.
        """
        frame = self._build_frame(servo_id, CMD_POS_READ)
        with self._lock:
            self._send(frame)
            time.sleep(0.005)
            params = self._recv(servo_id, CMD_POS_READ)

        if params is None or len(params) < 2:
            return None
        return struct.unpack("<h", params[:2])[0]

    def read_voltage(self, servo_id: int) -> int | None:
        """Read the input voltage of a servo.

        Args:
            servo_id: Servo ID.

        Returns:
            Voltage in millivolts, or None on timeout.
        """
        frame = self._build_frame(servo_id, CMD_VIN_READ)
        with self._lock:
            self._send(frame)
            time.sleep(0.005)
            params = self._recv(servo_id, CMD_VIN_READ)

        if params is None or len(params) < 2:
            return None
        return struct.unpack("<H", params[:2])[0]

    def read_temperature(self, servo_id: int) -> int | None:
        """Read the internal temperature of a servo.

        Args:
            servo_id: Servo ID.

        Returns:
            Temperature in degrees Celsius, or None on timeout.
        """
        frame = self._build_frame(servo_id, CMD_TEMP_READ)
        with self._lock:
            self._send(frame)
            time.sleep(0.005)
            params = self._recv(servo_id, CMD_TEMP_READ)

        if params is None or len(params) < 1:
            return None
        return params[0]

    # ─── Load / Unload ───────────────────────────────────────────

    def unload(self, servo_id: int) -> None:
        """Unload (disable torque) on a servo, allowing free movement.

        Args:
            servo_id: Servo ID.
        """
        params = bytes([0])  # 0 = unload
        frame = self._build_frame(servo_id, CMD_LOAD_UNLOAD_WRITE, params)
        with self._lock:
            self._send(frame)

    def load(self, servo_id: int) -> None:
        """Load (enable torque) on a servo.

        Args:
            servo_id: Servo ID.
        """
        params = bytes([1])  # 1 = load
        frame = self._build_frame(servo_id, CMD_LOAD_UNLOAD_WRITE, params)
        with self._lock:
            self._send(frame)

    # ─── Scanning ────────────────────────────────────────────────

    def scan(self, id_range: range | None = None) -> list[ServoStatus]:
        """Scan for online servos and read their status.

        Args:
            id_range: Range of IDs to scan (default: 0-20).

        Returns:
            List of :class:`ServoStatus` for each responding servo.
        """
        if id_range is None:
            id_range = range(0, 21)

        found: list[ServoStatus] = []

        for sid in id_range:
            pos = self.read_position(sid)
            if pos is not None:
                voltage = self.read_voltage(sid) or 0
                temp = self.read_temperature(sid) or 0
                found.append(ServoStatus(
                    servo_id=sid,
                    position=pos,
                    voltage_mv=voltage,
                    temperature_c=temp,
                ))

        return found
