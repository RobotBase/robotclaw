---
name: robotclaw
description: Control LOBOT LX bus servo robots — move joints, record/play motions, scan diagnostics
---

# RobotClaw — Robot Control Skill

Control physical LOBOT LX bus servo robots through this skill.
Bridges the digital AI world with the physical robot world.

## Capabilities

### Movement
- **go_home** — Move all joints to neutral home position
- **set_joint** — Set a single joint to a target position (0-1000)
- **set_joints** — Set multiple joints simultaneously
- **unload_all** — Disable torque on all servos (free movement)
- **load_all** — Enable torque on all servos

### Status
- **scan_status** — Scan all servos and report: online/offline, position, voltage, temperature
- **get_positions** — Read current positions of all joints

### Motion Recording & Playback
- **record_start** — Begin recording a motion sequence
- **record_capture** — Capture current joint positions as a keyframe
- **record_finish** — Finish recording and save to file
- **play_motion** — Play a recorded motion file at variable speed
- **list_motions** — List all saved motion files

## Available Joints

| Joint Name | Servo ID | Description |
|------------|----------|-------------|
| left_hip_yaw | 1 | Left hip side swing |
| left_hip_pitch | 2 | Left hip forward/back |
| left_knee | 3 | Left knee bend |
| left_ankle_pitch | 4 | Left ankle forward/back |
| left_ankle_roll | 5 | Left ankle side roll |
| right_hip_yaw | 6 | Right hip side swing |
| right_hip_pitch | 7 | Right hip forward/back |
| right_knee | 8 | Right knee bend |
| right_ankle_pitch | 9 | Right ankle forward/back |
| right_ankle_roll | 10 | Right ankle side roll |

## Usage Examples

```python
from robotclaw.openclaw_skill import OpenClawSkill

skill = OpenClawSkill(port="COM3")
skill.connect()

# Move to home
skill.execute("go_home", time_ms=2000)

# Check servo status
result = skill.execute("scan_status")

# Move a single joint
skill.execute("set_joint", name="left_knee", position=300, time_ms=500)

# Play a recorded motion
skill.execute("play_motion", motion_name="walk_cycle", speed=1.5)

skill.disconnect()
```

## Safety Notes

- Always scan servos before commanding movements
- Use `unload_all` before manually posing the robot
- Monitor voltage — below 6000mV indicates low battery
- Monitor temperature — above 65°C indicates overheating
