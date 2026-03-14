"""CLI entry points for robotclaw commands.

Registered as console_scripts in pyproject.toml:
  - robotclaw-scan  → scan_main()
  - robotclaw-teach → teach_main()
"""

from __future__ import annotations

import argparse
import sys
import time


def _find_serial_ports() -> list[str]:
    """List available serial ports."""
    try:
        from serial.tools.list_ports import comports

        return [p.device for p in comports()]
    except ImportError:
        return []


# ═════════════════════════════════════════════════════════════════════
# robotclaw-scan
# ═════════════════════════════════════════════════════════════════════


def scan_main(argv: list[str] | None = None) -> None:
    """Servo bus diagnostic scanner.

    Scans for connected LOBOT LX servos and displays their status.
    """
    parser = argparse.ArgumentParser(
        prog="robotclaw-scan",
        description="Scan for connected LOBOT LX bus servos and display status.",
    )
    parser.add_argument(
        "--port", "-p",
        type=str,
        default="",
        help="Serial port (e.g. COM3, /dev/ttyUSB0). Auto-detects if omitted.",
    )
    parser.add_argument(
        "--baudrate", "-b",
        type=int,
        default=115200,
        help="Serial baudrate (default: 115200).",
    )
    parser.add_argument(
        "--range", "-r",
        type=str,
        default="0-20",
        help="Servo ID scan range (default: 0-20).",
    )

    args = parser.parse_args(argv)

    # Parse range
    try:
        parts = args.range.split("-")
        id_range = range(int(parts[0]), int(parts[1]) + 1)
    except (ValueError, IndexError):
        print(f"Error: Invalid range '{args.range}'. Use format like '0-20'.")
        sys.exit(1)

    # Auto-detect port
    port = args.port
    if not port:
        ports = _find_serial_ports()
        if not ports:
            print("Error: No serial ports found. Specify with --port.")
            sys.exit(1)
        port = ports[0]
        print(f"Auto-detected port: {port}")

    # Import here to avoid import errors when just checking --help
    from .servo_bus import ServoBus

    bus = ServoBus()
    try:
        bus.connect(port, args.baudrate)
        print(f"Connected to {port} @ {args.baudrate} baud")
        print(f"Scanning IDs {id_range.start}-{id_range.stop - 1}...\n")

        found = bus.scan(id_range)

        if not found:
            print("No servos found.")
        else:
            print(f"{'ID':>4}  {'Position':>8}  {'Voltage':>8}  {'Temp':>5}")
            print("-" * 34)
            for s in found:
                voltage_str = f"{s.voltage_mv}mV" if s.voltage_mv else "N/A"
                temp_str = f"{s.temperature_c}°C" if s.temperature_c else "N/A"
                print(f"{s.servo_id:>4}  {s.position:>8}  {voltage_str:>8}  {temp_str:>5}")
            print(f"\nFound {len(found)} servo(s).")
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)
    finally:
        bus.disconnect()


# ═════════════════════════════════════════════════════════════════════
# robotclaw-teach
# ═════════════════════════════════════════════════════════════════════


def teach_main(argv: list[str] | None = None) -> None:
    """Interactive motion teaching terminal.

    Provides a REPL for recording and playing back robot motions.
    """
    parser = argparse.ArgumentParser(
        prog="robotclaw-teach",
        description="Interactive motion teaching for LOBOT servo robots.",
    )
    parser.add_argument(
        "--port", "-p",
        type=str,
        default="",
        help="Serial port (e.g. COM3, /dev/ttyUSB0).",
    )
    parser.add_argument(
        "--baudrate", "-b",
        type=int,
        default=115200,
        help="Serial baudrate (default: 115200).",
    )
    parser.add_argument(
        "--motions-dir", "-d",
        type=str,
        default="motions",
        help="Directory for motion files (default: motions/).",
    )

    args = parser.parse_args(argv)

    port = args.port
    if not port:
        ports = _find_serial_ports()
        if not ports:
            print("Error: No serial ports found. Specify with --port.")
            sys.exit(1)
        port = ports[0]
        print(f"Auto-detected port: {port}")

    from pathlib import Path

    from .robot import Robot
    from .robot_config import DEFAULT_CONFIG
    from .recorder import MotionClip, MotionPlayer, MotionRecorder

    motions_dir = Path(args.motions_dir)
    motions_dir.mkdir(parents=True, exist_ok=True)

    robot = Robot(config=DEFAULT_CONFIG, port=port, baudrate=args.baudrate)
    robot.connect()
    recorder = MotionRecorder(robot)
    player = MotionPlayer(robot)

    print(f"Connected to {port}")
    print("\n🦾 RobotClaw Motion Teaching")
    print("=" * 40)
    print("Commands:")
    print("  record <name>     Start recording")
    print("  capture / c       Capture a frame")
    print("  undo              Undo last frame")
    print("  finish            Finish and save")
    print("  play <file> [spd] Play a motion file")
    print("  list              List saved motions")
    print("  home              Go to home position")
    print("  unload            Unload all servos")
    print("  load              Load all servos")
    print("  scan              Scan servo status")
    print("  quit / q          Exit")
    print("=" * 40)

    try:
        while True:
            try:
                prompt = "(rec) " if recorder.is_recording else ""
                line = input(f"\n{prompt}robotclaw> ").strip()
            except (EOFError, KeyboardInterrupt):
                print()
                break

            if not line:
                continue

            parts = line.split()
            cmd = parts[0].lower()

            if cmd in ("quit", "q", "exit"):
                break
            elif cmd == "record":
                if len(parts) < 2:
                    print("Usage: record <name>")
                    continue
                name = parts[1]
                recorder.start_recording(name)
                robot.unload_all()
                print(f"Recording '{name}'. Servos unloaded — pose the robot freely.")
                print("Use 'capture' to save a frame, 'finish' to complete.")
            elif cmd in ("capture", "c"):
                if not recorder.is_recording:
                    print("Not recording. Use 'record <name>' first.")
                    continue
                frame = recorder.capture_frame()
                print(f"Frame {recorder.frame_count} captured (t={frame.timestamp_ms}ms)")
            elif cmd == "undo":
                removed = recorder.undo_last_frame()
                if removed:
                    print(f"Undid frame (t={removed.timestamp_ms}ms). {recorder.frame_count} frames remain.")
                else:
                    print("No frames to undo.")
            elif cmd == "finish":
                if not recorder.is_recording:
                    print("Not recording.")
                    continue
                clip = recorder.finish_recording()
                filepath = motions_dir / f"{clip.name}.json"
                clip.save(filepath)
                robot.load_all()
                print(f"Saved {clip.frame_count} frames → {filepath}")
            elif cmd == "play":
                if len(parts) < 2:
                    print("Usage: play <file> [speed]")
                    continue
                filepath = Path(parts[1])
                if not filepath.exists():
                    filepath = motions_dir / parts[1]
                if not filepath.exists():
                    filepath = motions_dir / f"{parts[1]}.json"
                if not filepath.exists():
                    print(f"File not found: {parts[1]}")
                    continue
                speed = float(parts[2]) if len(parts) > 2 else 1.0
                clip = MotionClip.load(filepath)
                print(f"Playing '{clip.name}' ({clip.frame_count} frames) at {speed}x...")
                robot.load_all()
                player.play(clip, speed=speed)
                print("Playback complete.")
            elif cmd == "list":
                files = sorted(motions_dir.glob("*.json"))
                if not files:
                    print("No motion files found.")
                else:
                    for f in files:
                        print(f"  {f.name}")
            elif cmd == "home":
                robot.go_home(2000)
                print("Going home (2s)...")
                time.sleep(2)
            elif cmd == "unload":
                robot.unload_all()
                print("All servos unloaded.")
            elif cmd == "load":
                robot.load_all()
                print("All servos loaded.")
            elif cmd == "scan":
                statuses = robot.scan()
                for s in statuses:
                    status = "✅ online" if s["online"] else "❌ offline"
                    extra = ""
                    if s["online"]:
                        extra = f" pos={s['position']} V={s.get('voltage_mv', '?')}mV T={s.get('temperature_c', '?')}°C"
                    print(f"  [{s['servo_id']:>2}] {s['joint_name']:<22} {status}{extra}")
            else:
                print(f"Unknown command: {cmd}")

    finally:
        robot.disconnect()
        print("Disconnected. Goodbye!")
