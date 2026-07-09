# RCA Quick Reference Guide

## Overview
This guide provides rapid lookup for common defect patterns and their root causes. Use this during Root Cause Analysis to quickly identify issues from DLT logs.

---

## Pattern → Root Cause Lookup

### Audio Issues

| DLT Pattern | Root Cause | Component | Fix Area |
|-------------|------------|-----------|----------|
| `buffer flush timeout buffer_size=2048` | Buffer too large | AudioMixer | Config: reduce to 512 |
| `state stuck state=PHONE_FOCUS` | Missing state transition | AudioFocusManager | Code: add release handler |
| `MediaPlayer resume blocked` | Focus not released | AudioFocusManager | Integration issue |
| `MOST link down` | Ring sync lost | Communication | Hardware/CPU load |
| `STR.*duration=[3-9][0-9]{2}` | Multiple possible | MediaService | Check sub-timings |

### Bluetooth Issues

| DLT Pattern | Root Cause | Component | Fix Area |
|-------------|------------|-----------|----------|
| `ACK timeout waiting for device` | Protocol timeout | BluetoothStack | Timeout config / RF |
| `Profile A2DP unavailable.*NOT_PAIRED` | Pairing DB issue | BluetoothStack | Re-pair device |
| `Reconnection failed attempts exhausted` | Device unreachable | BluetoothStack | Range / device state |
| `state machine stuck.*CONNECTING` | Missing transition | LUM | Code: add profile_unavailable handler |

### Boot Issues

| DLT Pattern | Root Cause | Component | Fix Area |
|-------------|------------|-----------|----------|
| `[DEBUG]` during boot | Debug logging ON | Build | Build config |
| `boot_time=[4-9][0-9]{3}` | Boot regression | System | Check each phase |
| `phase=SERVICES complete time=[3-9]` | Service init slow | ServiceManager | Optimize init order |

### Memory Issues

| DLT Pattern | Root Cause | Component | Fix Area |
|-------------|------------|-----------|----------|
| `delta=+[2-9][0-9]MB` (consistent) | Memory leak | Various | Identify leaking process |
| `threshold exceeded memory_used=` | OOM approaching | System | Find memory hog |
| `error code=ENOMEM` | Allocation failed | Various | Memory cleanup |
| `OOM detected process=` | Out of memory | System | Process restart |

### Communication Issues

| DLT Pattern | Root Cause | Component | Fix Area |
|-------------|------------|-----------|----------|
| `checksum.*failed msg_id=` | Byte order wrong | CAN Parser | Config: endianness |
| `ring synchronization lost` | CPU overload | MOST | Reduce CPU load |
| `ring timeout node=AMP` | Amplifier timeout | MOST | Hardware check |
| `using stale data` | Message dropped | CAN | Fix checksum issue |

### LUM Issues

| DLT Pattern | Root Cause | Component | Fix Area |
|-------------|------------|-----------|----------|
| `preset_id not found in persisted` | Preset not saved | Persistence | Fix persistence schema |
| `ENTLUM FAILED.*STATE_MACHINE_STUCK` | Missing transition | LUM State Machine | Code fix |
| `restoreState.*timeout` | Source unavailable | LUM | Add fallback logic |

---

## Component Identification

### From APP_ID
| APP_ID | Component |
|--------|-----------|
| MDIA | MediaService |
| AUDI | AudioService |
| CONN | Connectivity (BT/WiFi) |
| SYST | System (boot/memory) |
| COMM | Communication (CAN/MOST) |
| HMI0 | User Interface |

### From CTX_ID
| CTX_ID | Sub-Component |
|--------|---------------|
| FOCS | AudioFocusManager |
| MIX0 | AudioMixer |
| BT01 | BluetoothStack |
| LUM0 | LastUserMode |
| BOOT | BootManager |
| MEM0 | MemoryMonitor |
| CAN0 | CAN Gateway |
| MOST | MOST Ring |

---

## Severity Classification

### Critical (P1)
- System crash / restart
- Complete audio failure
- Boot blocked
- Safety feature affected

### High (P2)
- KPI failure (STR, LUM, Boot)
- Intermittent connectivity loss
- User action required to recover

### Medium (P3)
- Wrong data displayed
- Minor delay
- Workaround available

### Low (P4)
- Cosmetic issues
- Log verbosity
- Non-functional

---

## RCA Template

```
## Defect: IVI-2026-XXX

### Symptom
[What user/tester observed]

### DLT Analysis
1. First relevant log:
   `[timestamp] [message]`
   
2. Error indicator:
   `[timestamp] [error message]`

3. State at failure:
   `[timestamp] [state info]`

### Root Cause
[Component]: [Specific issue]

### Evidence
- Pattern matched: `[DLT pattern]`
- Timing analysis: X ms (threshold Y ms)
- State analysis: [state details]

### Recommended Fix
[Code/Config change needed]

### Verification
After fix, verify:
- No error pattern in logs
- KPI within threshold
- State transitions complete normally
```

---

## Quick Grep Commands

### Find all errors
```bash
grep "error\|fail\|timeout\|stuck" logfile.dlt
```

### Find KPI failures
```bash
grep "MARKER.*FAILED\|KPI FAILED" logfile.dlt
```

### Find specific component issues
```bash
grep "AUDI FOCS" logfile.dlt  # Audio focus
grep "CONN BT01" logfile.dlt  # Bluetooth
grep "SYST MEM0" logfile.dlt  # Memory
grep "COMM MOST" logfile.dlt  # MOST bus
```

### Timing analysis
```bash
grep "duration=\|time=\|delay=" logfile.dlt
```

---

## Decision Flow

```
1. READ error message
       │
       ▼
2. IDENTIFY component (APP_ID + CTX_ID)
       │
       ▼
3. MATCH pattern from tables above
       │
       ▼
4. VERIFY by checking context (10-20 lines before)
       │
       ▼
5. DOCUMENT root cause and fix
```
