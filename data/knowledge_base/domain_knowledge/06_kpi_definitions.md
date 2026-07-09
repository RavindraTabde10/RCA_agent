# KPI Definitions & Analysis - Domain Knowledge

## Overview
Key Performance Indicators (KPIs) measure system responsiveness and user experience quality. This document defines all infotainment KPIs, their measurement methods, and analysis techniques.

---

## KPI Summary Table

| KPI | Full Name | Threshold | Measurement |
|-----|-----------|-----------|-------------|
| STR | Source-To-Render | < 200ms | Source select to audio output |
| LUM/ENTLUM | Last User Mode | < 500ms | Boot to last source playing |
| BOOT | Boot Time | < 3000ms | Ignition to home screen |
| AFR | Audio Focus Release | < 200ms | Call end to focus released |
| BTC | Bluetooth Connect | < 5000ms | Boot to BT connected |

---

## STR (Source-To-Render)

### Definition
Time from user selecting an audio source until audio is audible.

### Measurement Points
```
START: [MEDIA] MuteStateSnapshotRepository SourceSnapshot source=<SRC> status=Selected
  │
  │  ... audio focus, decoder init, buffer fill ...
  │
 END: [MEDIA] MARKER STR source=<SRC> duration=<MS> ms
```

### Threshold
- **Pass**: ≤ 200ms
- **Fail**: > 200ms

### Sub-Component Timing
| Step | Typical | Max Allowed |
|------|---------|-------------|
| Source selection | 10ms | 20ms |
| Audio focus request | 20ms | 50ms |
| Device enumeration (USB) | 50ms | 100ms |
| Buffer initialization | 30ms | 50ms |
| First audio frame | 20ms | 50ms |
| **Total** | **130ms** | **200ms** |

### Common Failure Causes

1. **Buffer Flush Timeout**
   - DLT: `buffer flush timeout buffer_size=2048 expected=512`
   - Impact: +100-200ms delay
   - Fix: Reduce buffer size configuration

2. **USB Enumeration Delay**
   - DLT: `device enumeration complete.*delay=[2-9][0-9]{2}ms`
   - Impact: +100-300ms delay
   - Fix: USB driver optimization

3. **Audio Focus Contention**
   - DLT: Gap between `requestFocus` and `focus granted`
   - Impact: Variable delay
   - Fix: Priority configuration

### Analysis Example
```
10:00:00.100 [MEDIA] SourceSnapshot source=USB status=Selected  ← START
10:00:00.145 [USB] enumerating device
10:00:00.322 [USB] enumeration complete delay=177ms             ← SLOW!
10:00:00.367 [AUDIO] requestFocus app=MediaPlayer
10:00:00.412 [AUDIO] focus granted
10:00:00.478 [AUDIO] state=PLAYING
10:00:00.489 [MEDIA] MARKER STR source=USB duration=378 ms      ← FAIL

Root cause: USB enumeration took 177ms (should be <100ms)
```

---

## LUM / ENTLUM (Last User Mode)

### Definition
Time from boot completion (home screen displayed) until the last audio source is restored and playing.

### Measurement Points
```
START: [BOOT] phase=HOMESCREEN displayed total_boot_time=<MS>ms
  │
  │  ... read persisted state, connect source, request focus ...
  │
 END: [LUM] MARKER ENTLUM started playing in <MS> ms
```

### Threshold
- **Pass**: ≤ 500ms
- **Fail**: > 500ms OR `MARKER ENTLUM FAILED`

### Restoration Flow
1. Read persisted state file
2. Identify last source (USB/BT/FM/etc.)
3. Connect/initialize source
4. Request audio focus
5. Start playback

### Common Failure Causes

1. **Preset Not Persisted**
   - DLT: `preset_id not found in persisted state`
   - Impact: Falls back to default preset
   - Fix: Persistence file schema

2. **State Machine Stuck**
   - DLT: `state machine stuck in CONNECTING no transition for profile_unavailable`
   - Impact: Complete failure, no audio
   - Fix: Add missing state transition

3. **Bluetooth Not Ready**
   - DLT: `Profile A2DP unavailable.*reason=NOT_PAIRED`
   - Impact: Timeout waiting for BT
   - Fix: Fallback to alternate source

### Analysis Example (Failure)
```
08:00:02.890 [BOOT] phase=HOMESCREEN displayed                  ← START
08:00:03.012 [LUM] transition=ToAvailable
08:00:03.123 [LUM] restoreState begin source=BT_A2DP
08:00:03.567 [BT] Profile A2DP unavailable reason=NOT_PAIRED    ← PROBLEM
08:00:04.567 [LUM] ERROR state machine stuck                    ← STUCK
08:00:04.678 [LUM] MARKER ENTLUM FAILED duration=1250ms         ← FAIL

Root cause: State machine has no handler for profile_unavailable event
```

---

## BOOT (Boot Time)

### Definition
Time from ignition ON (power applied) until home screen is displayed.

### Measurement Points
```
START: [BOOT] System power on
  │
  │  ... kernel, services, HMI init ...
  │
 END: [BOOT] phase=HOMESCREEN displayed total_boot_time=<MS>ms
```

### Threshold
- **Pass**: ≤ 3000ms
- **Fail**: > 3000ms

### Phase Breakdown
| Phase | Target | Measure |
|-------|--------|---------|
| Kernel | 500ms | `phase=KERNEL complete time=` |
| Services | 2000ms (cumulative) | `phase=SERVICES complete time=` |
| HMI | 500ms | `phase=HOMESCREEN displayed` |

### Common Failure Causes

1. **Debug Logging Enabled**
   - DLT: `[DEBUG]` entries during boot
   - Impact: +1-2 seconds
   - Fix: Disable debug in production

2. **Service Init Slow**
   - DLT: Long gap in service startup
   - Impact: Variable
   - Fix: Optimize service init order

3. **HMI Render Slow**
   - DLT: Gap between services complete and homescreen
   - Impact: +500ms
   - Fix: HMI optimization

### Analysis Example (Regression)
```
07:00:00.000 [BOOT] System power on                             ← START
07:00:00.456 [BOOT] phase=KERNEL complete time=456ms            ← OK
07:00:00.567 [BOOT] phase=SERVICES starting
07:00:01.234 [DEBUG] ServiceManager loading config...           ← DEBUG!
07:00:01.567 [DEBUG] AudioService init trace enabled            ← DEBUG!
07:00:02.123 [DEBUG] MediaService detailed logging active       ← DEBUG!
07:00:02.879 [BOOT] phase=SERVICES complete time=2423ms         ← SLOW
07:00:04.250 [BOOT] phase=HOMESCREEN displayed total=4250ms     ← FAIL

Root cause: Debug logging enabled in production build
```

---

## AFR (Audio Focus Release)

### Definition
Time from phone call ending until audio focus is properly released.

### Measurement Points
```
START: [PHONE] Call ended duration=<MS>ms
  │
  │  ... SCO release, focus release ...
  │
 END: [AUDIO] AudioFocusManager releaseFocus (focus state = IDLE)
```

### Threshold
- **Pass**: ≤ 200ms
- **Fail**: > 200ms or focus stuck

### Symptom of Failure
- Music doesn't resume after call
- DLT shows `state stuck state=PHONE_FOCUS`

### Analysis Example (Failure)
```
08:01:45.000 [PHONE] Call ended                                 ← START
08:01:45.100 [BT] HFP SCO link released
08:01:45.200 [AUDIO] releaseFocus app=Phone
08:01:45.250 [AUDIO] state=PHONE_FOCUS waiting for release      ← PROBLEM
08:01:46.250 [AUDIO] state stuck duration=1000ms
08:01:47.250 [AUDIO] state stuck duration=2000ms
08:01:48.250 [AUDIO] state stuck duration>2500ms                ← FAIL

Root cause: Focus state machine missing release confirmation handler
```

---

## KPI Analysis Workflow

### Step 1: Extract KPI Markers
```bash
grep "MARKER" logfile.dlt
```

### Step 2: Check Pass/Fail
```bash
grep "MARKER.*FAILED\|duration=[3-9][0-9]{2}" logfile.dlt
```

### Step 3: Backtrack to Find Cause
Go back 20-50 lines before the MARKER and look for:
- `timeout`
- `delay`
- `waiting`
- `stuck`
- `error`

### Step 4: Calculate Sub-Timings
Use timestamps to identify which sub-step is slow.

### Step 5: Match to Known Issue
Compare pattern to documented issues above.

---

## KPI Monitoring Dashboard Queries

### STR Failures
```
Pattern: MARKER STR.*duration=[3-9][0-9]{2}
Meaning: STR duration 300-999ms (>200ms threshold)
```

### LUM Failures
```
Pattern: MARKER ENTLUM FAILED
Meaning: LUM restoration failed completely
```

### Boot Regressions
```
Pattern: KPI FAILED boot_time=
Meaning: Boot exceeded threshold
```

---

## Summary: Issue → KPI → Pattern

| User Symptom | KPI Affected | DLT Pattern |
|--------------|--------------|-------------|
| USB slow to play | STR | `STR.*duration=[3-9]` |
| Music not restored | LUM | `ENTLUM FAILED` |
| Boot feels slow | BOOT | `boot_time=[4-9]` |
| No audio after call | AFR | `state stuck.*PHONE_FOCUS` |
| Radio wrong preset | LUM | `preset_id not found` |
