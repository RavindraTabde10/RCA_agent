# Vehicle Bus Communication - Domain Knowledge

## Overview
The infotainment system communicates with other vehicle ECUs via multiple bus systems for data exchange (climate, vehicle status) and audio streaming (amplifier).

---

## Bus Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    Infotainment Unit                         │
│  ┌─────────────────────────────────────────────────────┐    │
│  │              Communication Gateway                   │    │
│  │    ┌────────┐  ┌────────┐  ┌────────┐              │    │
│  │    │  CAN   │  │  MOST  │  │  LIN   │              │    │
│  │    │Gateway │  │ Master │  │Gateway │              │    │
│  │    └───┬────┘  └───┬────┘  └───┬────┘              │    │
│  └────────┼───────────┼───────────┼─────────────────────┘   │
└───────────┼───────────┼───────────┼─────────────────────────┘
            │           │           │
    ┌───────▼───┐   ┌───▼────┐  ┌───▼────┐
    │  CAN Bus  │   │MOST Ring│  │LIN Bus │
    │           │   │         │  │        │
    │ • Climate │   │• Amp    │  │• Seat  │
    │ • Cluster │   │• DSP    │  │• Mirror│
    │ • Gateway │   │• Tuner  │  │• Light │
    └───────────┘   └─────────┘  └────────┘
```

---

## CAN Bus (Controller Area Network)

### Purpose
- Vehicle data exchange (climate, speed, RPM)
- Control messages (volume sync, display brightness)
- NOT used for audio streaming

### Message Structure
```
┌──────────┬──────────┬──────────┬──────────┐
│  MSG_ID  │  DATA    │ CHECKSUM │  CRC     │
│  (11/29b)│ (0-8 B)  │  (opt)   │  (15b)   │
└──────────┴──────────┴──────────┴──────────┘
```

### Key Message IDs
| MSG_ID | Description | Sender | Data |
|--------|-------------|--------|------|
| 0x3E5 | Climate status | HVAC ECU | Temp, fan, mode |
| 0x1A0 | Vehicle speed | Cluster | Speed, RPM |
| 0x2B8 | Media control | Steering wheel | Button press |
| 0x4D2 | Display brightness | Body ECU | Ambient light |

### CAN Parser
- Decodes raw CAN bytes to signal values
- Validates checksum for data integrity
- Updates HMI with parsed values

### Common Issues

1. **Checksum Validation Failed**
   - Symptom: Climate display shows stale/wrong data
   - Root Cause: Byte order mismatch (LITTLE_ENDIAN vs BIG_ENDIAN)
   - DLT Pattern: `checksum.*failed msg_id=0x3E5`
   - Impact: ~15% of messages dropped

2. **Message Timeout**
   - Symptom: Data goes stale
   - Root Cause: ECU not transmitting, bus error
   - DLT Pattern: `CAN timeout msg_id=`

### DLT Identifiers
- APP_ID: `COMM`
- CTX_ID: `CAN0`
- Key logs:
  - `CANGateway receiving.*msg_id=`
  - `CANParser parsing`
  - `checksum validation failed`
  - `message dropped - using stale data`

---

## MOST Bus (Media Oriented Systems Transport)

### Purpose
- High-bandwidth audio streaming
- Premium audio systems (surround sound)
- Connects IVI ↔ Amplifier ↔ DSP

### Ring Topology
```
    ┌───────────┐
    │    IVI    │ (Master)
    └─────┬─────┘
          │
    ┌─────▼─────┐
    │   AMP01   │ (Amplifier)
    └─────┬─────┘
          │
    ┌─────▼─────┐
    │   DSP01   │ (Processor)
    └─────┬─────┘
          │
          └──────► back to IVI
```

### Synchronization
- 25MHz ring clock
- Sync frames every 44.1μs
- Master (IVI) maintains timing
- CPU load affects sync accuracy

### Bandwidth Management
| Load | Status | Action |
|------|--------|--------|
| < 70% | Normal | Full quality |
| 70-80% | Warning | Monitor |
| 80-90% | High | Consider reducing streams |
| > 90% | Critical | Risk of dropout |

### Common Issues

1. **Ring Synchronization Lost**
   - Symptom: Audio stops completely
   - Root Cause: High CPU load causes missed sync frames
   - DLT Pattern: `ring synchronization lost missed_frames=`
   - Trigger: CPU > 80% + bandwidth > 85%

2. **Node Timeout**
   - Symptom: Amplifier stops responding
   - Root Cause: Amplifier ECU busy/crashed
   - DLT Pattern: `ring timeout node=AMP01 no_response=`

3. **Recovery Failed**
   - Symptom: Audio doesn't recover after sync loss
   - Root Cause: Ring communication broken
   - DLT Pattern: `Recovery failed - ring communication broken`
   - Fix: System restart required

### DLT Identifiers
- APP_ID: `COMM`
- CTX_ID: `MOST`
- Key logs:
  - `MOSTRing initialized ring_id=`
  - `ring sync status=OK bandwidth=X% cpu_load=X%`
  - `sync frame delayed expected=0ms actual=Xms`
  - `ring synchronization lost`
  - `ring timeout node=`
  - `MOST link down - audio stopped`

---

## LIN Bus (Local Interconnect Network)

### Purpose
- Low-speed, low-cost communication
- Seat controls, mirrors, interior lighting
- Not critical for audio/media

### Characteristics
- Single master, multiple slaves
- 20 kbit/s (much slower than CAN)
- Used for non-time-critical functions

---

## Integration with Audio System

### Audio Path via MOST
```
MediaPlayer → AudioMixer → MOST → Amplifier → Speakers
                              ↓
                         If MOST fails:
                         AudioOutput reports "link down"
                         All audio stops
```

### CAN for Audio Control
- Volume commands from steering wheel
- Mute on collision warning
- Speed-dependent volume adjustment

---

## RCA Decision Tree: Communication Issues

```
Communication Error
        │
        ▼
┌───────────────────┐
│ Which bus/data?   │
└────────┬──────────┘
    ┌────┼────┐
    ▼    ▼    ▼
  CAN  MOST  LIN
   │     │     │
   ▼     ▼     ▼
┌─────┐ ┌─────┐ (Low priority)
│Check│ │Check│
│msg  │ │sync │
│ID   │ │stat │
└──┬──┘ └──┬──┘
   │       │
   ▼       ▼
Checksum? Timeout?
   │       │
   ▼       ▼
Byte     CPU
order    load
issue    issue
```

---

## Key DLT Patterns for Communication Issues

| Issue | DLT Pattern | Root Cause |
|-------|-------------|------------|
| Climate wrong | `checksum calculated=.*received=` | Byte order mismatch |
| CAN data stale | `using stale data` | Checksum fail or timeout |
| Audio stops | `MOST link down` | Ring sync lost |
| Amp timeout | `ring timeout node=AMP` | Amplifier ECU issue |
| Bandwidth high | `bandwidth=[89][0-9]%` | Too many streams |
| CPU affecting audio | `cpu_load=[89][0-9]%` | System overloaded |

---

## Troubleshooting Commands

### Check Ring Status
Look for periodic sync logs:
```
[MOST] ring sync status=OK bandwidth=72% cpu_load=45%
```

### Check Message Flow
Look for receiving/parsing patterns:
```
[CAN] CANGateway receiving climate message msg_id=0x3E5
[CAN] CANParser parsing climate data temp=22C fan=3
```

### Identify Failures
Search for error keywords:
```
grep "failed\|timeout\|lost\|down" logfile.dlt | grep COMM
```
