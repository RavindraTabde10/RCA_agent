# DLT Logging System - Domain Knowledge

## Overview
DLT (Diagnostic Log and Trace) is the AUTOSAR standard logging protocol used in automotive ECUs. It provides structured, timestamped logs for debugging and diagnostics.

---

## DLT Message Format

```
ECU_ID TIMESTAMP DELTA ECU APP_ID CTX_ID LOG_TYPE MSG_NUM log LEVEL verbose FLAG [TAG] MESSAGE
```

### Example Breakdown
```
ECU1 2026/06/15 10:23:45.123456 +0.055445 ECU1 AUDI FOCS LCAT 2 log info verbose 1 [AUDIO] AudioFocusManager requestFocus app=MediaPlayer
│    │                         │         │    │    │    │    │ │   │    │       │ │       └── Message content
│    │                         │         │    │    │    │    │ │   │    │       │ └── Tag/Module
│    │                         │         │    │    │    │    │ │   │    │       └── Verbose flag
│    │                         │         │    │    │    │    │ │   │    └── Log level
│    │                         │         │    │    │    │    │ │   └── Log type
│    │                         │         │    │    │    │    │ └── Message number
│    │                         │         │    │    │    │    └── Log category
│    │                         │         │    │    │    └── Context ID
│    │                         │         │    │    └── Application ID
│    │                         │         │    └── ECU ID
│    │                         │         └── ECU source
│    │                         └── Delta from previous message
│    └── Absolute timestamp
└── ECU identifier
```

---

## Application IDs (APP_ID)

| APP_ID | Full Name | Description |
|--------|-----------|-------------|
| `MDIA` | MediaService | Media playback, source management |
| `AUDI` | AudioService | Audio routing, focus, mixing |
| `CONN` | Connectivity | Bluetooth, WiFi, cellular |
| `SYST` | System | Boot, memory, services |
| `HMI0` | HMI | User interface, display |
| `COMM` | Communication | CAN, MOST, LIN buses |
| `NAVI` | Navigation | Route guidance, maps |
| `TUNR` | Tuner | FM/AM/DAB radio |

---

## Context IDs (CTX_ID)

### MediaService (MDIA)
| CTX_ID | Description |
|--------|-------------|
| `SRCS` | Source management (USB, BT, etc.) |
| `PLAY` | Playback control |
| `LUM0` | Last User Mode |
| `USB0` | USB media handling |
| `TUNR` | Tuner interface |

### AudioService (AUDI)
| CTX_ID | Description |
|--------|-------------|
| `FOCS` | Audio focus management |
| `MIX0` | Audio mixer |
| `PLAY` | Playback state |
| `VOL0` | Volume control |

### Connectivity (CONN)
| CTX_ID | Description |
|--------|-------------|
| `BT01` | Bluetooth stack |
| `PHON` | Phone service |
| `WIFI` | WiFi management |

### System (SYST)
| CTX_ID | Description |
|--------|-------------|
| `BOOT` | Boot sequence |
| `MEM0` | Memory monitor |
| `SRVC` | Service manager |
| `PERF` | Performance monitor |

### Communication (COMM)
| CTX_ID | Description |
|--------|-------------|
| `CAN0` | CAN bus gateway |
| `MOST` | MOST ring |
| `LIN0` | LIN bus |

---

## Log Levels

| Level | Severity | When to Use |
|-------|----------|-------------|
| `fatal` | 1 | System crash imminent |
| `error` | 2 | Operation failed |
| `warn` | 3 | Unexpected but recoverable |
| `info` | 4 | Normal operation markers |
| `debug` | 5 | Detailed trace info |
| `verbose` | 6 | Maximum detail |

---

## KPI Markers

### STR (Source-To-Render)
```
[MEDIA] MARKER STR source=<SOURCE> duration=<MS> ms
```
- Measures time from source selection to audio output
- Threshold: 200ms
- Failure: `threshold=200ms` + warning

### LUM (Last User Mode)
```
[LUM] MARKER ENTLUM started playing in <MS> ms
```
- Measures time from boot to last source restored
- Threshold: 500ms
- Failure: `MARKER ENTLUM FAILED duration=<MS>ms reason=<REASON>`

### Boot Time
```
[BOOT] phase=HOMESCREEN displayed total_boot_time=<MS>ms
[BOOT] KPI FAILED boot_time=<MS>ms threshold=<MS>ms
```
- Measures ignition-on to home screen
- Threshold: 3000ms

---

## Timing Analysis

### Delta Calculation
The `+X.XXXXXX` field shows seconds since previous message:
```
10:23:45.123456 +0.000000  ← First message (baseline)
10:23:45.178901 +0.055445  ← 55.445ms later
10:23:45.223456 +0.044555  ← 44.555ms after previous
```

### Identifying Delays
1. Look for large deltas (gaps > 100ms often indicate issues)
2. Check timestamps around error messages
3. Calculate total duration between markers

### Example Analysis
```
STR Start: 10:23:45.123456 (source=USB selected)
STR End:   10:23:45.646789 (state=PLAYING)
Duration:  523ms (FAIL - threshold 200ms)
```

---

## Common Log Patterns

### Successful Operations
```
[AUDIO] AudioFocusManager requestFocus app=MediaPlayer type=MEDIA
[AUDIO] AudioFocusManager focus granted app=MediaPlayer
[MEDIA] MediaPlayer opening track path=/usb/Music/track.mp3
[AUDIO] PlaybackStateUpdater state=PLAYING source=USB
```

### Error Patterns

**Focus Stuck:**
```
[AUDIO] AudioFocusManager state stuck state=PHONE_FOCUS duration=1000ms
[AUDIO] AudioFocusManager state stuck state=PHONE_FOCUS duration=2000ms
[AUDIO] AudioFocusManager state stuck state=PHONE_FOCUS duration>2500ms - focus not released
```

**Memory Issues:**
```
[MEM] MemoryMonitor threshold exceeded memory_used=1567MB threshold=1536MB
[MEDIA] MediaPlayer::decodeFrame error code=ENOMEM buffer_pool_exhausted
[MEM] OOM detected process=MediaPlayer triggering service restart
```

**Communication Errors:**
```
[CAN] CANParser checksum validation failed msg_id=0x3E5
[MOST] ring synchronization lost missed_frames=3
```

---

## Filtering Techniques

### By Application
```bash
grep "AUDI" logfile.dlt      # All audio logs
grep "CONN BT01" logfile.dlt  # Bluetooth only
```

### By Severity
```bash
grep "log error" logfile.dlt  # Errors only
grep "log warn\|log error" logfile.dlt  # Warnings and errors
```

### By Time Range
```bash
grep "10:23:4[5-9]" logfile.dlt  # 10:23:45 to 10:23:49
```

### By Marker
```bash
grep "MARKER" logfile.dlt     # All KPI markers
grep "MARKER STR" logfile.dlt  # STR markers only
```

---

## RCA Using DLT Logs

### Step 1: Identify the Failure
- Search for `error`, `FAILED`, `timeout`
- Note timestamp and component

### Step 2: Find Context
- Go back 10-20 lines before error
- Check what operation was in progress

### Step 3: Check State Transitions
- Track state changes (CONNECTING → CONNECTED → etc.)
- Look for missing transitions

### Step 4: Measure Timing
- Calculate deltas between key events
- Compare against thresholds

### Step 5: Identify Root Cause
- Match pattern to known issues
- Check for resource exhaustion (memory, CPU)
- Verify proper cleanup/release

---

## Quick Reference: Issue → Pattern

| Symptom | Search Pattern |
|---------|----------------|
| Slow audio start | `MARKER STR.*duration=[3-9]` |
| No audio after call | `state stuck.*PHONE_FOCUS` |
| BT disconnect | `Connection lost reason=` |
| Boot slow | `KPI FAILED boot_time` |
| Memory crash | `OOM detected\|ENOMEM` |
| Radio preset lost | `preset_id not found` |
| CAN data error | `checksum.*failed` |
| MOST timeout | `ring.*timeout\|sync.*lost` |
