# Audio Subsystem - Domain Knowledge

## Overview
The infotainment audio subsystem manages all audio routing, mixing, and playback within the vehicle. It follows a layered architecture common in automotive Linux/QNX systems.

---

## Audio Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    Applications Layer                        │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐    │
│  │MediaPlayer│  │  Phone   │  │Navigation│  │  Alerts  │    │
│  └────┬─────┘  └────┬─────┘  └────┬─────┘  └────┬─────┘    │
└───────┼─────────────┼─────────────┼─────────────┼───────────┘
        │             │             │             │
┌───────▼─────────────▼─────────────▼─────────────▼───────────┐
│                  AudioFocusManager                           │
│         (Priority-based audio routing control)               │
└───────────────────────────┬─────────────────────────────────┘
                            │
┌───────────────────────────▼─────────────────────────────────┐
│                      AudioMixer                              │
│    (Stream mixing, volume control, ducking, fading)          │
└───────────────────────────┬─────────────────────────────────┘
                            │
┌───────────────────────────▼─────────────────────────────────┐
│                    Audio HAL / ALSA                          │
│              (Hardware abstraction layer)                    │
└───────────────────────────┬─────────────────────────────────┘
                            │
┌───────────────────────────▼─────────────────────────────────┐
│              Audio Output (MOST/I2S/Analog)                  │
│                    → Amplifier → Speakers                    │
└─────────────────────────────────────────────────────────────┘
```

---

## AudioFocusManager

### Purpose
Manages which application has permission to output audio at any given time. Prevents audio conflicts (e.g., navigation voice over music during phone call).

### Focus Types
| Type | Priority | Description | Example |
|------|----------|-------------|---------|
| CALL | 100 | Phone calls - highest priority | Bluetooth HFP call |
| ALERT | 90 | Safety/emergency alerts | Collision warning |
| NAVIGATION | 80 | Turn-by-turn guidance | Voice guidance |
| MEDIA | 50 | Entertainment audio | Music, radio |
| NOTIFICATION | 30 | System notifications | Message tone |

### Focus States
```
IDLE → REQUESTING → GRANTED → RELEASING → IDLE
                        ↓
                   PHONE_FOCUS (special state for calls)
```

### Common Issues
1. **State Machine Stuck**: Focus not released after call ends
   - Root Cause: Missing transition handler for `profile_unavailable`
   - DLT Pattern: `state stuck state=PHONE_FOCUS duration>`

2. **Focus Conflict**: Two apps holding focus simultaneously
   - Root Cause: Race condition in focus arbitration
   - DLT Pattern: `focus granted` appearing twice without `releaseFocus`

### DLT Identifiers
- APP_ID: `AUDI`
- CTX_ID: `FOCS`
- Key logs:
  - `requestFocus app=<APP> type=<TYPE>`
  - `focus granted app=<APP>`
  - `releaseFocus app=<APP>`
  - `state stuck state=<STATE>`

---

## AudioMixer

### Purpose
Mixes multiple audio streams, applies volume/balance/fading, and routes to output.

### Stream Management
- Each audio source gets a stream ID
- Streams can be: ACTIVE, PAUSED, MUTED, DUCKED
- Buffer management critical for latency

### Buffer Configuration
| Parameter | Default | Optimal | Impact |
|-----------|---------|---------|--------|
| buffer_size | 2048 | 512 | Latency |
| sample_rate | 48000 | 44100/48000 | Quality |
| channels | 2 | 2/6/8 | Surround |

### Common Issues
1. **Buffer Flush Timeout**: Large buffer causes playback delay
   - Root Cause: buffer_size too large (2048 vs expected 512)
   - DLT Pattern: `buffer flush timeout buffer_size=2048 expected=512`
   - Impact: STR KPI failure (>200ms delay)

2. **Stream Attachment Delay**: Slow stream initialization
   - DLT Pattern: Long gap between `requestFocus` and `stream attached`

### DLT Identifiers
- APP_ID: `AUDI`
- CTX_ID: `MIX0`
- Key logs:
  - `AudioMixer stream attached id=<ID>`
  - `AudioMixer buffer flush timeout`
  - `AudioMixer first audio frame`

---

## Playback State Machine

### States
```
STOPPED → PREPARING → PLAYING → PAUSED → STOPPED
              ↓           ↓
           ERROR      BUFFERING
```

### STR (Source-To-Render) Measurement
- **Start**: `SourceSnapshot source=<SRC> status=Selected`
- **End**: `PlaybackStateUpdater state=PLAYING`
- **KPI**: < 200ms

### Common Issues
1. **Slow USB Enumeration**: Device detection delay
   - DLT Pattern: `device enumeration complete vendor=Generic delay=XXXms`
   
2. **Resume Blocked**: Waiting for audio focus indefinitely
   - DLT Pattern: `MediaPlayer resume blocked - waiting for audio focus`

### DLT Identifiers
- APP_ID: `MDIA`
- CTX_ID: `PLAY`, `SRCS`
- Key logs:
  - `MARKER STR source=<SRC> duration=<MS>`
  - `MediaPlayer opening track`
  - `PlaybackStateUpdater state=<STATE>`

---

## Audio Output Interfaces

### MOST (Media Oriented Systems Transport)
- Ring topology for premium audio
- Synchronous streaming to amplifier
- CPU load affects sync timing

**Issues:**
- Ring synchronization lost under high CPU
- DLT Pattern: `ring synchronization lost missed_frames=`

### I2S (Inter-IC Sound)
- Direct digital audio connection
- Used for basic audio output

### CAN (for volume/control only)
- Volume commands via CAN bus
- Not for audio streaming

---

## RCA Decision Tree

```
Audio Issue Reported
        │
        ▼
┌───────────────────┐
│ Check focus state │
└────────┬──────────┘
         │
    ┌────┴────┐
    ▼         ▼
STUCK?    GRANTED?
  │           │
  ▼           ▼
Focus      Check mixer
release    buffer state
issue        │
         ┌───┴───┐
         ▼       ▼
    TIMEOUT?  ATTACHED?
       │         │
       ▼         ▼
    Buffer    Check HAL/
    config    output link
```

---

## Key DLT Patterns for Audio Issues

| Issue | DLT Pattern | Root Cause Area |
|-------|-------------|-----------------|
| Slow playback start | `STR.*duration=[3-9][0-9]{2}` | Buffer/enumeration |
| No resume after call | `state stuck.*PHONE_FOCUS` | FocusManager state machine |
| Audio stops | `MOST link down` | Bus communication |
| Crackling/dropout | `buffer.*underrun` | Buffer configuration |
| Volume issues | `mixer.*mute` stuck | Mixer state |
