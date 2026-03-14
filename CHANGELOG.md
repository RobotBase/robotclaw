# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/),
and this project adheres to [Semantic Versioning](https://semver.org/).

## [0.2.0] - 2026-03-15

### Changed

- Migrated all project URLs to new GitHub organization: `https://github.com/RobotBase/robotclaw`

---

## [0.1.0] - 2026-03-15

### Added

- `ServoBus` — LOBOT LX serial bus servo protocol driver
  - Frame building, checksum, thread-safe read/write
  - Commands: move, read position/voltage/temperature, load/unload, scan
- `RobotConfig` — Hardware configuration data classes
  - `JointConfig`, `LegConfig`, `RobotConfig` with JSON serialization
  - `DEFAULT_CONFIG` — 10 servos, dual-leg biped layout
- `Robot` — High-level robot controller
  - Joint-level control with automatic direction/offset mapping
  - Context manager support
  - Batch operations: go_home, get_positions, set_joints
- **Motion Recorder** subsystem
  - `MotionRecorder` — Keyframe-based motion teaching
  - `MotionPlayer` — Playback with variable speed control
  - `MotionClip` / `Keyframe` — JSON-serializable data model
- **CLI tools**
  - `robotclaw-scan` — Servo bus diagnostic scanner
  - `robotclaw-teach` — Interactive motion teaching terminal
- **OpenClaw integration**
  - `OpenClawSkill` — Skill adapter for OpenClaw AI agent platform
  - `SKILL.md` — OpenClaw skill descriptor file
