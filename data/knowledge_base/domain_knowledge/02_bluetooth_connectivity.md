# Bluetooth Connectivity - Domain Knowledge

## Overview
Bluetooth subsystem handles phone pairing, hands-free calling (HFP), and audio streaming (A2DP) in the infotainment unit.

---

## Bluetooth Stack Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    Application Layer                         │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐    │
│  │PhoneApp  │  │MediaApp  │  │Contacts  │  │Messages  │    │
│  └────┬─────┘  └────┬─────┘  └────┬─────┘  └────┬─────┘    │
└───────┼─────────────┼─────────────┼─────────────┼───────────┘
        │             │             │             │
┌───────▼─────────────▼─────────────▼─────────────▼───────────┐
│                  Bluetooth Service                           │
│           (Connection management, profile routing)           │
└───────────────────────────┬─────────────────────────────────┘
                            │
┌───────────────────────────▼─────────────────────────────────┐
│                    BluetoothStack                            │
│    ┌─────────┐  ┌─────────┐  ┌─────────┐  ┌─────────┐      │
│    │   HFP   │  │  A2DP   │  │  AVRCP  │  │  PBAP   │      │
│    │(Calling)│  │(Audio)  │  │(Control)│  │(Contacts)│     │
│    └─────────┘  └─────────┘  └─────────┘  └─────────┘      │
└───────────────────────────┬─────────────────────────────────┘
                            │
┌───────────────────────────▼─────────────────────────────────┐
│                    Bluetooth HAL                             │
│              (Hardware interface layer)                      │
└───────────────────────────┬─────────────────────────────────┘
                            │
┌───────────────────────────▼─────────────────────────────────┐
│               Bluetooth Hardware Module                      │
└─────────────────────────────────────────────────────────────┘
```

---

## Bluetooth Profiles

### HFP (Hands-Free Profile)
- **Purpose**: Phone calls via vehicle speakers/mic
- **Audio Link**: SCO (Synchronous Connection-Oriented)
- **Codecs**: CVSD (narrow-band), mSBC (wide-band)

**Connection Flow:**
```
DISCONNECTED → CONNECTING → CONNECTED → SCO_ESTABLISHING → SCO_ESTABLISHED
                                              ↓
                                         SCO_RELEASED → CONNECTED
```

### A2DP (Advanced Audio Distribution Profile)
- **Purpose**: High-quality audio streaming (music)
- **Codecs**: SBC, AAC, aptX, LDAC
- **Latency**: ~100-200ms typical

**Connection States:**
```
DISCONNECTED → PAIRING → PAIRED → CONNECTING → CONNECTED → STREAMING
                            ↓
                       NOT_PAIRED (pairing lost)
```

### AVRCP (Audio/Video Remote Control Profile)
- **Purpose**: Play/pause, track skip, metadata
- **Version**: 1.6 typical (supports browsing)

### PBAP (Phone Book Access Profile)
- **Purpose**: Contact synchronization
- **Sync**: On-demand or automatic

---

## Connection Management

### Pairing States
| State | Description |
|-------|-------------|
| UNPAIRED | No bond exists |
| PAIRING | PIN/confirmation exchange |
| PAIRED | Bond stored, can auto-connect |
| CONNECTING | Establishing link |
| CONNECTED | Active connection |

### Auto-Reconnection
- On boot: Attempt to connect last paired device
- Timeout: 30 seconds default
- Retry: 3 attempts with exponential backoff

### Common Issues

1. **Profile Unavailable After Boot**
   - Symptom: A2DP shows NOT_PAIRED despite being paired before
   - Root Cause: Pairing database corruption or profile mismatch
   - DLT Pattern: `Profile A2DP unavailable.*reason=NOT_PAIRED`

2. **Call Disconnect During Long Calls**
   - Symptom: HFP drops after 5-15 minutes
   - Root Cause: ACK timeout, possible RF interference or protocol issue
   - DLT Pattern: `ACK timeout waiting for device response`

3. **Reconnection Failure**
   - Symptom: 3 reconnection attempts exhausted
   - Root Cause: Device out of range, device busy, or link key mismatch
   - DLT Pattern: `Reconnection failed attempts exhausted`

---

## SCO Link (Voice Calls)

### Establishment
```
HFP Connected
     │
     ▼
Call Incoming/Outgoing
     │
     ▼
SCO Request
     │
     ▼
SCO Negotiation (codec selection)
     │
     ▼
SCO Established
     │
     ▼
Audio routed to speakers/mic
```

### SCO Release
- Should occur when call ends
- Triggers audio focus release
- Must notify AudioFocusManager

**Issue: SCO Properly Released but Focus Stuck**
- SCO link released correctly
- But AudioFocusManager not notified
- Music doesn't resume
- DLT Pattern: `SCO link released` followed by `state stuck.*PHONE_FOCUS`

---

## DLT Identifiers

### BluetoothStack
- APP_ID: `CONN`
- CTX_ID: `BT01`
- Key logs:
  - `BluetoothStack HFP connected device=<MAC>`
  - `BluetoothStack SCO link established codec=<CODEC>`
  - `BluetoothStack ACK timeout`
  - `Connection lost reason=<REASON>`
  - `Profile A2DP unavailable`
  - `Reconnection attempt X/3`

### Phone Service
- APP_ID: `CONN`
- CTX_ID: `PHON`
- Key logs:
  - `Incoming call from <NUMBER>`
  - `Call started`
  - `Call ended duration=<MS>`

---

## RCA Decision Tree

```
Bluetooth Issue
      │
      ▼
┌─────────────────┐
│Connection type? │
└────────┬────────┘
    ┌────┴────┐
    ▼         ▼
  HFP?      A2DP?
    │         │
    ▼         ▼
┌───────┐  ┌────────┐
│SCO    │  │Pairing │
│state? │  │state?  │
└───┬───┘  └────┬───┘
    │           │
┌───┴───┐   ┌───┴───┐
▼       ▼   ▼       ▼
TIMEOUT DROP NOT_PAIRED STUCK
   │     │      │       │
   ▼     ▼      ▼       ▼
Protocol RF   Pairing  State
issue  issue  DB issue machine
```

---

## Key DLT Patterns for Bluetooth Issues

| Issue | DLT Pattern | Root Cause Area |
|-------|-------------|-----------------|
| HFP disconnect | `ACK timeout` | Protocol/RF |
| A2DP won't connect | `NOT_PAIRED` | Pairing database |
| Reconnect fails | `Reconnection failed attempts exhausted` | Device/range |
| Audio after call | `SCO link released` then no focus release | Integration issue |
| Pairing timeout | `Pairing timeout device=` | Device busy/range |

---

## Integration Points

### With AudioFocusManager
- HFP call → Request CALL focus (priority 100)
- Call end → Release focus → Should resume media
- **Critical**: Missing release notification causes stuck state

### With LUM (Last User Mode)
- Boot → Check last source
- If BT_A2DP → Trigger auto-connect
- **Issue**: State machine has no transition for `profile_unavailable`
  - DLT: `state machine stuck in CONNECTING no transition for profile_unavailable`
