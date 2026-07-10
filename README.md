# RCA Agent - AI-Powered Root Cause Analysis Tool

An intelligent Root Cause Analysis (RCA) system designed for **multiple industries** including automotive, telecom, healthcare, finance, and manufacturing. It automatically analyzes software defects by processing logs, matching historical defects using vector similarity, and leveraging LLM analysis to identify root causes and recommend fixes.

## 🆕 What's New

- **ML-Based Domain Classification** - Auto-assign defects to Audio/Bluetooth/Boot/Stability teams using trained model
- **Real-Time Monitoring Dashboard** - Live token tracking, analysis progress, and event logs
- **Multi-Industry Support** - Configure domain: automotive, telecom, healthcare, finance, manufacturing, software
- **Token Consumption Tracking** - Live cost monitoring per analysis stage
- **Analysis Throttling** - 2-second gap between concurrent analyses for stability

---

## 📋 Table of Contents

- [Overview](#overview)
- [Domain Classification](#-ml-based-domain-classification)
- [Real-Time Dashboard](#-real-time-monitoring-dashboard)
- [Multi-Industry Support](#-multi-industry-domain-support)
- [Architecture](#architecture)
- [System Flow](#system-flow)
- [Components](#components)
- [Installation](#installation)
- [Configuration](#configuration)
- [Usage](#usage)
- [Automated Scheduling](#-automated-scheduling-no-manual-intervention)
- [Data Structure](#data-structure)
- [API Reference](#api-reference)

---

## 🎯 Overview

### Problem Statement

Software defect analysis is time-consuming and error-prone:
- Engineers spend **4-6 hours** on initial review
- **25-30%** of defects are assigned to wrong teams
- Knowledge is siloed with specific experts
- Root causes are often confused with symptoms

### Solution

The RCA Agent automates defect analysis through:
- **DLT Log Parsing** - Extract errors, warnings, and patterns from diagnostic logs (supports **binary & text** formats)
- **Semantic Search** - Find similar historical defects using AI embeddings (LanceDB)
- **Duplicate Detection** - Automatically identify potential duplicate tickets (≥90% similarity)
- **LLM Analysis** - AI-powered root cause identification with confidence scores
- **JIRA Integration** - Auto-update tickets with analysis results

### Impact

| Metric | Before | After | Improvement |
|--------|--------|-------|-------------|
| Initial Review Time | 4-6 hours | 15-30 min | **85-90%** faster |
| Time to Fix | 2-5 days | 0.5-1.5 days | **60-70%** faster |
| Wrong Team Assignment | 25-30% | 5-10% | **70-80%** less |
| Correct Diagnosis | 60-70% | 85-95% | **25-35%** better |

---

## 🎯 ML-Based Domain Classification

Automatically assigns defects to the correct team using a trained machine learning model (Sentence Transformer + Logistic Regression).

### Supported Domains

| Domain | Team | Icon | Keywords |
|--------|------|------|----------|
| **Audio System** | Audio Engineering | 🔊 | audio, sound, speaker, volume, playback |
| **Bluetooth Connectivity** | Connectivity Team | 📱 | bluetooth, BT, pairing, A2DP, HFP |
| **Boot & System** | Boot/Platform Team | 🚀 | boot, startup, kernel, init, cold start |
| **Stability/Memory** | System Stability Team | 💾 | memory, leak, crash, OOM, freeze |

### How It Works

```
┌─────────────────────────────────────────────────────────────────────┐
│                    Domain Classification Flow                        │
├─────────────────────────────────────────────────────────────────────┤
│                                                                      │
│  Defect Text ──► Sentence Transformer ──► ML Model ──► Domain       │
│  (summary +       (all-MiniLM-L6-v2)      (Logistic    Assignment   │
│   description)                             Regression)              │
│                                                                      │
│  Example:                                                            │
│  "Bluetooth phone disconnects after 10 min"                         │
│       │                                                              │
│       ▼                                                              │
│  📱 bluetooth_connectivity_domain (92% confidence)                  │
│  → Assigned to: Connectivity Team                                    │
│                                                                      │
└─────────────────────────────────────────────────────────────────────┘
```

### Training Data

The model is trained on **230 synthesized defect records** located in:
```
domain_assign/model_training/
├── domain_classifier_logistic.pkl      # Trained model
├── all-MiniLM-L6-v2/                   # Sentence transformer model
├── domain_assignment_synthesized_data.csv
├── domain_training_extended.csv
└── domain_labeled_defects_detailed.csv
```

### Usage

```python
# Automatic (integrated with RCA Engine)
result = engine.analyze_defect("SAM1-2001")
print(result["stages"]["domain_classification"]["data"])
# {'domain': 'audio_system_domain', 'confidence': 0.87, 'team': 'Audio Engineering'}

# Manual prediction
from src.rca_infotainment.domain_classifier import predict_domain_for_defect

defect = {"summary": "Audio stutters during USB playback", "description": "..."}
prediction = predict_domain_for_defect(defect)
# {'domain': 'audio_system_domain', 'domain_display': 'Audio System', 'confidence': 0.85}
```

---

## 📊 Real-Time Monitoring Dashboard

The RCA Monitoring Dashboard provides live visibility into analysis progress, token consumption, and system events.

### Features

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│                       RCA MONITORING DASHBOARD                                   │
├─────────────────────────────────────────────────────────────────────────────────┤
│  TICKETS    TOKENS      QUOTA      COST        ACTIVE     SESSION              │
│     3       12.5K         0       €0.46          1        5m 23s               │
├─────────────────────────────────────────────────────────────────────────────────┤
│                                                                                  │
│  ┌─────────────────────────────┐  ┌──────────────────────────────────────────┐ │
│  │ ⚡ Active Analyses          │  │ 📜 Live Event Log                        │ │
│  │                             │  │                                          │ │
│  │  TEST-001  [llm_analysis]   │  │  01:07:20  stage   TEST-001: llm...     │ │
│  │  ✓ DLT Analysis    1,006 tk │  │  01:07:19  tokens  +500 tokens          │ │
│  │  ✓ Source Mapping    550 tk │  │  01:07:18  stage   historical_match     │ │
│  │  ● LLM Analysis    2,350 tk │  │  01:07:17  tokens  +250 tokens          │ │
│  └─────────────────────────────┘  └──────────────────────────────────────────┘ │
│                                                                                  │
│  ┌─────────────────────────────┐  ┌──────────────────────────────────────────┐ │
│  │ 💰 Token Events              │  │ 📋 Recent Analyses                      │ │
│  │                             │  │                                          │ │
│  │ TIME    TICKET   STAGE  +TK │  │ TICKET      STATUS   TOKENS   COST      │ │
│  │ 01:07   TEST-001 llm   +500 │  │ TEST-001    ✓        6.0K     €0.22     │ │
│  │ 01:06   TEST-001 src   +400 │  │ SAM1-2001   ✓        5.2K     €0.19     │ │
│  └─────────────────────────────┘  └──────────────────────────────────────────┘ │
│                                                                                  │
│  📈 Token Consumption Over Time                Peak: 706  Avg: 387  Rate: 43K/m │
│  ┌──────────────────────────────────────────────────────────────────────────────┐│
│  │     ╱‾‾‾‾‾‾‾‾‾‾‾‾‾──────────────────────────────────────────────           ││
│  │    ╱                                                                        ││
│  │   ╱                                                            ● Tokens    ││
│  │  ╱                                                             ● Cost      ││
│  └──────────────────────────────────────────────────────────────────────────────┘│
└─────────────────────────────────────────────────────────────────────────────────┘
```

### Dashboard Usage

```bash
# Run analysis with live dashboard
python test_rca_dry_full.py

# Dashboard opens automatically at http://localhost:5050
```

### Dashboard Metrics

| Metric | Description |
|--------|-------------|
| **Tickets** | Total tickets analyzed this session |
| **Tokens** | Cumulative token consumption |
| **Quota** | Daily quota remaining (if configured) |
| **Cost** | Estimated cost in EUR |
| **Active** | Currently running analyses |
| **Session** | Dashboard uptime |

### Token Tracking by Stage

Each analysis stage reports token usage:

| Stage | Description | Typical Tokens |
|-------|-------------|----------------|
| `dlt_analysis` | DLT log parsing and pattern extraction | 500-1,500 |
| `source_mapping` | Map errors to source code | 300-800 |
| `historical_match` | Search similar defects | 400-1,000 |
| `llm_analysis` | LLM root cause analysis | 2,000-5,000 |
| `report_generation` | Generate MD/HTML reports | 200-500 |

---

## 🌐 Multi-Industry Domain Support

RCA Agent supports multiple industry domains with domain-specific:
- Error/warning keywords
- Component mappings
- Common root causes
- LLM analysis context
- Report terminology

### Supported Domains

| Domain | Industry | Log Formats | Focus Areas |
|--------|----------|-------------|-------------|
| `automotive` | Automotive/Infotainment | DLT, CAN, LIN | ECU, Media, Bluetooth, Boot |
| `telecom` | Telecommunications | Syslog, CDR, PCAP | 5G/LTE, Signaling, SIP |
| `healthcare` | Healthcare/Medical | HL7, FHIR, DICOM | EHR, Lab, Medical Devices |
| `finance` | Financial Services | JSON, FIX, SWIFT | Trading, Payments, Compliance |
| `manufacturing` | Manufacturing/IoT | OPC-UA, Modbus, MQTT | PLC, SCADA, Sensors |
| `software` | Generic Software | JSON, Syslog, Text | Applications, APIs, Databases |

### Configure Domain

**Option 1: Environment Variable**
```bash
# Windows PowerShell
$env:RCA_DOMAIN='automotive'
python test_rca_dry_full.py

# Linux/Mac
export RCA_DOMAIN=telecom
python test_rca_dry_full.py
```

**Option 2: .env File**
```bash
# .env
RCA_DOMAIN=automotive
RCA_DOMAIN_LOG_FORMAT=dlt
RCA_ENABLE_DOMAIN_RULES=true
```

**Option 3: config.yaml**
```yaml
domain:
  type: "automotive"
  log_format: "dlt"
  enable_domain_rules: true
```

### Domain Configuration Details

Each domain includes:

```python
# src/rca_infotainment/domain_config.py

AUTOMOTIVE_CONFIG = DomainConfig(
    domain=DomainType.AUTOMOTIVE,
    display_name="Automotive / Infotainment",
    
    error_keywords=["ERROR", "FATAL", "TIMEOUT", "DEADLOCK", ...],
    warning_keywords=["WARNING", "KPI_FAIL", "THRESHOLD_EXCEEDED", ...],
    
    component_keywords={
        "Media": ["MEDIA", "USB", "BT", "AUDIO", "VIDEO"],
        "Navigation": ["NAVI", "GPS", "MAP", "ROUTE"],
        "HMI": ["HMI", "GUI", "DISPLAY", "TOUCH"],
        ...
    },
    
    common_root_causes=[
        "Thread synchronization issue",
        "Memory leak or corruption",
        "CAN bus timeout",
        "USB enumeration failure",
        ...
    ],
    
    kpi_definitions={
        "STR": {"name": "Source-To-Render", "threshold": 200, "unit": "ms"},
        "BOOT": {"name": "Cold Boot Time", "threshold": 30, "unit": "s"},
        ...
    },
    
    system_prompt_suffix="""
    You are analyzing automotive infotainment system logs (DLT format).
    Focus on: timing issues, CAN/LIN communication, audio/video sync.
    """
)
```

### Using Domain in Code

```python
from rca_infotainment.domain_config import (
    get_domain_config,
    get_domain_type,
    is_automotive,
    get_error_keywords,
    get_common_root_causes
)

# Get current domain configuration
config = get_domain_config()
print(f"Domain: {config.display_name}")

# Check domain type
if is_automotive():
    print("Using automotive-specific analysis")

# Get domain-specific keywords
errors = get_error_keywords()  # ["ERROR", "FATAL", ...]
causes = get_common_root_causes()  # ["Thread sync...", ...]
```

---

## 🏗️ Architecture

### High-Level Architecture

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│                              RCA AGENT ARCHITECTURE                              │
└─────────────────────────────────────────────────────────────────────────────────┘

    ┌─────────────────────────────────────────────────────────────────────────────┐
    │                            INPUT LAYER                                       │
    │  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐     │
    │  │   Defect     │  │  DLT Logs    │  │   Comments   │  │    Time      │     │
    │  │ Description  │  │  (*.dlt)     │  │  & History   │  │   Stamps     │     │
    │  └──────┬───────┘  └──────┬───────┘  └──────┬───────┘  └──────┬───────┘     │
    └─────────┼─────────────────┼─────────────────┼─────────────────┼─────────────┘
              │                 │                 │                 │
              └────────────────┬┴─────────────────┴─────────────────┘
                               │
                               ▼
    ┌─────────────────────────────────────────────────────────────────────────────┐
    │                          PROCESSING LAYER                                    │
    │                                                                              │
    │  ┌──────────────────────────────────────────────────────────────────────┐   │
    │  │                         RCA ENGINE                                    │   │
    │  │                     (Orchestrator)                                    │   │
    │  └──────────────────────────────────────────────────────────────────────┘   │
    │           │                    │                    │                        │
    │           ▼                    ▼                    ▼                        │
    │  ┌────────────────┐   ┌────────────────┐   ┌────────────────┐               │
    │  │  DLT Analyzer  │   │ Source Mapper  │   │   Historical   │               │
    │  │                │   │                │   │    Matcher     │               │
    │  │ • Parse logs   │   │ • Map errors   │   │                │               │
    │  │ • Extract      │   │   to code      │   │ • Keyword      │               │
    │  │   errors       │   │ • Get context  │   │   search       │               │
    │  │ • Detect       │   │ • Git blame    │   │ • Semantic     │               │
    │  │   patterns     │   │                │   │   search       │               │
    │  └────────────────┘   └────────────────┘   └───────┬────────┘               │
    │                                                     │                        │
    └─────────────────────────────────────────────────────┼────────────────────────┘
                                                          │
                               ┌──────────────────────────┴──────────────────────┐
                               │                                                  │
                               ▼                                                  ▼
    ┌─────────────────────────────────────────────┐    ┌──────────────────────────────┐
    │              KNOWLEDGE LAYER                 │    │       EXTERNAL SERVICES      │
    │                                              │    │                              │
    │  ┌────────────────────────────────────────┐ │    │  ┌────────────────────────┐  │
    │  │      HISTORICAL DEFECTS (Source)       │ │    │  │     LLM Service        │  │
    │  │    data/historical_defects/            │ │    │  │  (Azure OpenAI/GPT-4)  │  │
    │  │         defects_data.json              │ │    │  │                        │  │
    │  │    (1000+ defects with root causes)    │ │    │  │  • Analyze context     │  │
    │  └──────────────────┬─────────────────────┘ │    │  │  • Identify root cause│  │
    │                     │                        │    │  │  • Suggest fixes       │  │
    │                     │ build_vector_db.py     │    │  │  • Confidence score    │  │
    │                     │ (generates embeddings) │    │  └────────────────────────┘  │
    │                     ▼                        │    │                              │
    │  ┌────────────────────────────────────────┐ │    │  ┌────────────────────────┐  │
    │  │     VECTOR DATABASE (LanceDB)          │ │    │  │     JIRA Service       │  │
    │  │        data/vector_db/                 │ │    │  │                        │  │
    │  │   (PRIMARY SEARCH MECHANISM)           │ │    │  │  • Fetch defects       │  │
    │  │                                        │ │    │  │  • Add comments        │  │
    │  │  ┌─────────────────────────────────┐   │ │    │  │  • Upload reports      │  │
    │  │  │  defects.lance (1536-dim vectors)│   │ │    │  │  • Link duplicates     │  │
    │  │  │  • Semantic similarity search   │   │ │    │  └────────────────────────┘  │
    │  │  │  • Cosine distance matching     │   │ │    │                              │
    │  │  │  • Fast duplicate detection     │   │ │    │  ┌────────────────────────┐  │
    │  │  └─────────────────────────────────┘   │ │    │  │      Git Service       │  │
    │  │                                        │ │    │  │                        │  │
    │  │  Fallback: Keyword search on JSON      │ │    │  │  • Pull source code    │  │
    │  │  if Vector DB unavailable              │ │    │  │  • Search files        │  │
    │  └────────────────────────────────────────┘ │    │  │  • Git blame           │  │
    │                                              │    │  └────────────────────────┘  │
    │  ┌────────────────────────────────────────┐ │    └──────────────────────────────┘
    │  │       DOMAIN KNOWLEDGE (MD Files)      │ │
    │  │  data/knowledge_base/domain_knowledge/ │ │
    │  │                                        │ │
    │  │  ┌──────────────────────────────────┐  │ │
    │  │  │ 01_audio_subsystem.md            │  │ │
    │  │  │ • Audio architecture             │  │ │
    │  │  │ • Common issues & DLT patterns   │  │ │
    │  │  │ • AudioFocusManager states       │  │ │
    │  │  ├──────────────────────────────────┤  │ │
    │  │  │ 02_bluetooth_connectivity.md     │  │ │
    │  │  │ • BT stack architecture          │  │ │
    │  │  │ • HFP/A2DP profiles              │  │ │
    │  │  │ • Connection state machines      │  │ │
    │  │  ├──────────────────────────────────┤  │ │
    │  │  │ 03_dlt_logging_guide.md          │  │ │
    │  │  │ • DLT message format             │  │ │
    │  │  │ • APP_ID → Component mapping     │  │ │
    │  │  │ • CTX_ID definitions             │  │ │
    │  │  ├──────────────────────────────────┤  │ │
    │  │  │ 06_kpi_definitions.md            │  │ │
    │  │  │ • STR, LUM, BOOT thresholds      │  │ │
    │  │  │ • Measurement methods            │  │ │
    │  │  │ • Failure analysis examples      │  │ │
    │  │  ├──────────────────────────────────┤  │ │
    │  │  │ 07_rca_quick_reference.md        │  │ │
    │  │  │ • Pattern → Root Cause lookup    │  │ │
    │  │  │ • Component identification       │  │ │
    │  │  └──────────────────────────────────┘  │ │
    │  └────────────────────────────────────────┘ │
    └──────────────────────────────────────────────┘
                               │                                      
                               │                                      
                               └──────────────────────────────────────┘
                                                  │
                                                  ▼
    ┌─────────────────────────────────────────────────────────────────────────────┐
    │                            OUTPUT LAYER                                      │
    │                                                                              │
    │  ┌──────────────────┐  ┌──────────────────┐  ┌──────────────────────────┐   │
    │  │   Markdown       │  │   HTML Report    │  │   JIRA Updates           │   │
    │  │   Report         │  │                  │  │                          │   │
    │  │                  │  │  • Styled        │  │  • Comment with RCA      │   │
    │  │  • Root Cause    │  │  • Interactive   │  │  • Attach reports        │   │
    │  │  • Evidence      │  │  • Shareable     │  │  • Link duplicates       │   │
    │  │  • Fix Reco      │  │                  │  │  • Update fields         │   │
    │  └──────────────────┘  └──────────────────┘  └──────────────────────────┘   │
    │                                                                              │
    └─────────────────────────────────────────────────────────────────────────────┘
```

### Layer Responsibilities

| Layer | Components | Responsibility |
|-------|------------|----------------|
| **Input** | DefectParser, LogProcessor | Ingest defects, DLT logs, comments |
| **Processing** | RCAEngine, DLTAnalyzer, SourceMapper, HistoricalMatcher | Analyze, correlate, and match data |
| **Knowledge** | VectorStore (LanceDB), HistoricalDefects, DomainKnowledge | Store and retrieve relevant context |
| **Output** | ReportGenerator, TeamAssignment | Generate reports, update JIRA |

---

## 🔄 System Flow

### Complete Analysis Pipeline

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│                         END-TO-END ANALYSIS FLOW                                 │
└─────────────────────────────────────────────────────────────────────────────────┘

 User Command
 ────────────
 python -m src.rca_infotainment.rca_cli analyze SAM1-2001 --jira
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────────────────┐
│ STAGE 1: LOAD DEFECT                                                             │
│ ───────────────────                                                              │
│                                                                                  │
│  Source: JIRA API (--jira) OR data/defects/jira_api_defects.json                │
│                                                                                  │
│  Output:                                                                         │
│  {                                                                               │
│    "key": "SAM1-2001",                                                          │
│    "summary": "Audio playback delay when switching to USB source",               │
│    "component": "MediaService",                                                  │
│    "priority": "P1",                                                             │
│    "dlt_log_content": "ECU1 2026/06/15... [AUDIO] AudioMixer buffer flush..."   │
│  }                                                                               │
└─────────────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────────────────┐
│ STAGE 2: DLT LOG ANALYSIS                                                        │
│ ─────────────────────────                                                        │
│                                                                                  │
│  Component: dlt_analyzer.py                                                      │
│                                                                                  │
│  Supports: BINARY DLT (AUTOSAR) + TEXT DLT (human-readable)                     │
│  Auto-detects format via analyze_file() method                                  │
│                                                                                  │
│  Process:                                                                        │
│  ┌──────────────────────────────────────────────────────────────────────────┐   │
│  │ Raw DLT Log                                                               │   │
│  │ "ECU1 2026/06/15 10:23:45.412345 AUDI MIX0 WARN AudioMixer buffer        │   │
│  │  flush timeout buffer_size=2048 expected=512"                             │   │
│  └──────────────────────────────────────────────────────────────────────────┘   │
│                          │                                                       │
│                          ▼                                                       │
│  ┌──────────────────────────────────────────────────────────────────────────┐   │
│  │ Parse & Extract                                                           │   │
│  │ • APP_ID: AUDI → Component: AudioService                                  │   │
│  │ • Level: WARN                                                             │   │
│  │ • Pattern: "timeout" detected                                             │   │
│  │ • Message: "buffer_size=2048 expected=512"                                │   │
│  └──────────────────────────────────────────────────────────────────────────┘   │
│                          │                                                       │
│                          ▼                                                       │
│  Output:                                                                         │
│  {                                                                               │
│    "errors": [],                                                                 │
│    "warnings": [{"level": "WARN", "app_id": "AUDI", "message": "buffer..."}],   │
│    "components": ["AudioService", "MediaController"],                            │
│    "patterns": [{"type": "timeout", "line": 5}],                                │
│    "summary": {"warning_count": 1, "pattern_types": ["timeout"]}                │
│  }                                                                               │
└─────────────────────────────────────────────────────────────────────────────────┘
│                                                                                  │
│  DLT Format Support:                                                             │
│  ┌────────────────────────────────┬────────────────────────────────────────────┐│
│  │ BINARY DLT (AUTOSAR)           │ TEXT DLT (Human-Readable)                  ││
│  ├────────────────────────────────┼────────────────────────────────────────────┤│
│  │ • Storage Header: DLT\x01      │ • Format 1: timestamp APP LEVEL msg        ││
│  │ • Standard + Extended Headers  │ • Format 2: [time] [APP] LEVEL: msg        ││
│  │ • APP_ID, CTX_ID extraction    │ • Format 3: time | APP | LEVEL | msg       ││
│  │ • Verbose/Non-verbose payloads │ • Regex-based parsing                      ││
│  │ • Auto-detected by magic bytes │ • Fallback for non-binary files            ││
│  └────────────────────────────────┴────────────────────────────────────────────┘│
│                                                                                  │
└─────────────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────────────────┐
│ STAGE 3: SOURCE CODE MAPPING                                                     │
│ ────────────────────────────                                                     │
│                                                                                  │
│  Component: source_mapper.py + git_service.py                                    │
│                                                                                  │
│  Process:                                                                        │
│  ┌─────────────────────┐         ┌─────────────────────────────────────────┐    │
│  │ DLT Patterns        │         │ Git Repository (if configured)          │    │
│  │ • APP_ID: AUDI      │ ──────▶ │ • Search: "AudioMixer" in src/          │    │
│  │ • Pattern: timeout  │         │ • Found: src/audio/AudioMixer.cpp       │    │
│  │ • Keyword: buffer   │         │ • Get code context around "buffer"      │    │
│  └─────────────────────┘         └─────────────────────────────────────────┘    │
│                                                                                  │
│  Output:                                                                         │
│  {                                                                               │
│    "mapped_files": [                                                             │
│      {"file": "src/audio/AudioMixer.cpp", "reason": "APP_ID AUDI maps..."}      │
│    ],                                                                            │
│    "git_enabled": true,                                                          │
│    "source_code": {"src/audio/AudioMixer.cpp": "static constexpr..."}           │
│  }                                                                               │
└─────────────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────────────────┐
│ STAGE 4: HISTORICAL DEFECT MATCHING (Vector DB)                                  │
│ ───────────────────────────────────────────────                                  │
│                                                                                  │
│  Component: historical_matcher.py + vector_store.py                              │
│                                                                                  │
│  ┌──────────────────────────────────────────────────────────────────────────┐   │
│  │                     SEMANTIC SEARCH FLOW                                  │   │
│  │                                                                           │   │
│  │  Query: "Audio playback delay when switching to USB source"               │   │
│  │                              │                                            │   │
│  │                              ▼                                            │   │
│  │  ┌─────────────────────────────────────────────────────────────────┐     │   │
│  │  │            Generate Embedding (1536 dimensions)                  │     │   │
│  │  │  [0.023, -0.156, 0.089, 0.234, -0.067, ...]                     │     │   │
│  │  └─────────────────────────────────────────────────────────────────┘     │   │
│  │                              │                                            │   │
│  │                              ▼                                            │   │
│  │  ┌─────────────────────────────────────────────────────────────────┐     │   │
│  │  │              Vector Similarity Search (LanceDB)                  │     │   │
│  │  │                    data/vector_db/defects.lance                  │     │   │
│  │  │                                                                  │     │   │
│  │  │  Compare query vector against 1000+ historical defect vectors    │     │   │
│  │  │  Using cosine similarity / L2 distance                           │     │   │
│  │  └─────────────────────────────────────────────────────────────────┘     │   │
│  │                              │                                            │   │
│  │                              ▼                                            │   │
│  │  ┌─────────────────────────────────────────────────────────────────┐     │   │
│  │  │                    RESULTS (Ranked by Similarity)                │     │   │
│  │  │                                                                  │     │   │
│  │  │  1. SAM1-342 │ Distance: 0.08 │ Similarity: 92% │ ⚠️ DUPLICATE  │     │   │
│  │  │     "Audio takes long time to start after source change"         │     │   │
│  │  │     Root Cause: Buffer size 1024 → reduced to 512               │     │   │
│  │  │                                                                  │     │   │
│  │  │  2. SAM1-156 │ Distance: 0.22 │ Similarity: 78% │ Related        │     │   │
│  │  │     "STR KPI failure when switching to Bluetooth audio"          │     │   │
│  │  │                                                                  │     │   │
│  │  │  3. SAM1-892 │ Distance: 0.31 │ Similarity: 69%                  │     │   │
│  │  │     "Audio playback delayed during cold boot"                    │     │   │
│  │  └─────────────────────────────────────────────────────────────────┘     │   │
│  └──────────────────────────────────────────────────────────────────────────┘   │
│                                                                                  │
│  Thresholds:                                                                     │
│  • ≥ 90% similarity → POTENTIAL DUPLICATE                                        │
│  • ≥ 75% similarity → RELATED ISSUE                                              │
│  • ≥ 50% similarity → WORTH MENTIONING                                           │
└─────────────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────────────────┐
│ STAGE 5: LLM ANALYSIS                                                            │
│ ─────────────────────                                                            │
│                                                                                  │
│  Component: llm_service.py → Azure OpenAI / GPT-4                                │
│                                                                                  │
│  ┌──────────────────────────────────────────────────────────────────────────┐   │
│  │                         PROMPT CONSTRUCTION                               │   │
│  │                                                                           │   │
│  │  ## DEFECT INFORMATION                                                    │   │
│  │  ID: SAM1-2001                                                            │   │
│  │  Summary: Audio playback delay when switching to USB source               │   │
│  │  Component: MediaService                                                  │   │
│  │                                                                           │   │
│  │  ## DLT LOG ANALYSIS                                                      │   │
│  │  ### Warnings Found:                                                      │   │
│  │  - AudioMixer buffer flush timeout buffer_size=2048 expected=512          │   │
│  │                                                                           │   │
│  │  ## SOURCE CODE MAPPING                                                   │   │
│  │  - src/audio/AudioMixer.cpp: APP_ID AUDI maps to AudioService             │   │
│  │                                                                           │   │
│  │  ## DOMAIN KNOWLEDGE CONTEXT                                              │   │
│  │  From 06_kpi_definitions.md: STR threshold < 200ms                        │   │
│  │  From 07_rca_quick_reference.md:                                          │   │
│  │    Pattern "buffer flush timeout" → Root Cause: Buffer too large          │   │
│  │                                                                           │   │
│  │  ## SIMILAR HISTORICAL DEFECTS (from Vector DB)                           │   │
│  │  - SAM1-342 (92% similar)                                                 │   │
│  │    Root Cause: Buffer size was set to 1024 samples...                     │   │
│  │                                                                           │   │
│  │  ## ANALYSIS REQUEST                                                      │   │
│  │  Please provide: ROOT CAUSE, EVIDENCE, AFFECTED CODE, FIX, CONFIDENCE     │   │
│  └──────────────────────────────────────────────────────────────────────────┘   │
│                              │                                                   │
│                              ▼                                                   │
│  ┌──────────────────────────────────────────────────────────────────────────┐   │
│  │                         LLM RESPONSE                                      │   │
│  │                                                                           │   │
│  │  ROOT CAUSE: BUFFER_SIZE constant in AudioMixer.cpp is set to 2048       │   │
│  │  samples instead of 512. During source switching, flushBuffers() must    │   │
│  │  drain the entire buffer. A 4x larger buffer = 4x longer flush time.     │   │
│  │                                                                           │   │
│  │  CONFIDENCE: 92%                                                          │   │
│  │                                                                           │   │
│  │  FIX RECOMMENDATION: Change BUFFER_SIZE from 2048 to 512 in              │   │
│  │  AudioMixer.cpp line 15-17.                                               │   │
│  └──────────────────────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────────────────┐
│ STAGE 6: REPORT GENERATION                                                       │
│ ──────────────────────────                                                       │
│                                                                                  │
│  Component: report_generator.py                                                  │
│                                                                                  │
│  Output Files:                                                                   │
│  ┌────────────────────────────────────────────────────────────────────────┐     │
│  │  output/reports/SAM1-2001_rca.md                                        │     │
│  │  ──────────────────────────────────────                                 │     │
│  │  # Root Cause Analysis Report: SAM1-2001                                │     │
│  │                                                                         │     │
│  │  **Status:** ⚠️ POTENTIAL DUPLICATE                                     │     │
│  │                                                                         │     │
│  │  ## ⚠️ Duplicate Detection                                              │     │
│  │  This defect is **92%** similar to **SAM1-342**                         │     │
│  │                                                                         │     │
│  │  ## 🔍 Root Cause Analysis                                              │     │
│  │  **Confidence:** 92%                                                    │     │
│  │  BUFFER_SIZE constant in AudioMixer.cpp is set to 2048...               │     │
│  │                                                                         │     │
│  │  ## 💡 Fix Recommendation                                               │     │
│  │  ```cpp                                                                 │     │
│  │  // Change from:                                                        │     │
│  │  static constexpr uint32_t BUFFER_SIZE = 2048;                          │     │
│  │  // To:                                                                 │     │
│  │  static constexpr uint32_t BUFFER_SIZE = 512;                           │     │
│  │  ```                                                                    │     │
│  └────────────────────────────────────────────────────────────────────────┘     │
│                                                                                  │
│  ┌────────────────────────────────────────────────────────────────────────┐     │
│  │  output/reports/SAM1-2001_rca.html                                      │     │
│  │  ──────────────────────────────────────                                 │     │
│  │  Styled HTML version with CSS for web viewing                           │     │
│  └────────────────────────────────────────────────────────────────────────┘     │
└─────────────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────────────────┐
│ STAGE 7: JIRA INTEGRATION (if --jira flag)                                       │
│ ───────────────────────────────────────────                                      │
│                                                                                  │
│  Component: jira_service.py                                                      │
│                                                                                  │
│  Actions:                                                                        │
│  ┌────────────────────────────────────────────────────────────────────────┐     │
│  │ 1. ADD COMMENT to SAM1-2001                                             │     │
│  │    ┌──────────────────────────────────────────────────────────────┐    │     │
│  │    │ h2. 🔍 AI Root Cause Analysis                                 │    │     │
│  │    │                                                               │    │     │
│  │    │ {panel:title=⚠️ POTENTIAL DUPLICATE|borderColor=#ffcc00}      │    │     │
│  │    │ This defect is 92% similar to *SAM1-342*                      │    │     │
│  │    │ {panel}                                                       │    │     │
│  │    │                                                               │    │     │
│  │    │ h3. Root Cause                                                │    │     │
│  │    │ BUFFER_SIZE set to 2048 instead of 512...                     │    │     │
│  │    │                                                               │    │     │
│  │    │ *Confidence:* 92%                                             │    │     │
│  │    └──────────────────────────────────────────────────────────────┘    │     │
│  │                                                                         │     │
│  │ 2. UPLOAD ATTACHMENTS                                                   │     │
│  │    • SAM1-2001_rca.md                                                   │     │
│  │    • SAM1-2001_rca.html                                                 │     │
│  │                                                                         │     │
│  │ 3. LINK DUPLICATE (if similarity ≥ 90%)                                 │     │
│  │    SAM1-2001 ──[is duplicate of]──▶ SAM1-342                            │     │
│  └────────────────────────────────────────────────────────────────────────┘     │
└─────────────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────────────────┐
│ FINAL OUTPUT                                                                     │
│ ────────────                                                                     │
│                                                                                  │
│  Console:                                                                        │
│  ╭──────────────────────────────────────────────────────────────────────────╮   │
│  │ ✅ Analysis Complete for SAM1-2001                                        │   │
│  ╰──────────────────────────────────────────────────────────────────────────╯   │
│  ╭──────────────────────────────────────────────────────────────────────────╮   │
│  │ ⚠️ POTENTIAL DUPLICATE - 92% similar to SAM1-342                          │   │
│  ╰──────────────────────────────────────────────────────────────────────────╯   │
│  ┌──────────────────────────────────────────────────────────────────────────┐   │
│  │ Root Cause: BUFFER_SIZE set to 2048 instead of 512 in AudioMixer.cpp     │   │
│  │ Confidence: 92%                                                           │   │
│  │ Affected Files: src/audio/AudioMixer.cpp                                  │   │
│  └──────────────────────────────────────────────────────────────────────────┘   │
│  Reports saved to: output/reports/                                               │
│  JIRA Updated: ✓ Comment ✓ Attachments ✓ Duplicate Link                          │
└─────────────────────────────────────────────────────────────────────────────────┘
```

---

## 📦 Components

### Module Structure

```
src/
├── rca_infotainment/           # Main RCA module
│   ├── rca_cli.py              # Command-line interface
│   ├── rca_engine.py           # Main orchestrator
│   ├── dlt_analyzer.py         # DLT log parsing (binary + text)
│   ├── domain_config.py        # Multi-industry domain configuration
│   ├── domain_classifier.py    # ML-based domain classification
│   ├── source_mapper.py        # Error → code mapping
│   ├── historical_matcher.py   # Similarity matching
│   ├── report_generator.py     # MD/HTML reports
│   ├── html_report_generator.py# Styled HTML report generation
│   ├── llm_service.py          # LLM integration (domain-aware)
│   ├── jira_service.py         # JIRA API client
│   ├── git_service.py          # Git repository access
│   └── dashboard/              # Real-time monitoring dashboard
│       ├── dashboard_server.py # HTTP server with SSE updates
│       └── tracker.py          # Analysis tracking utilities
│
├── knowledge_layer/
│   └── vector_store.py         # LanceDB vector database
│
├── input_layer/
│   ├── defect_parser.py        # Parse defect data
│   └── log_processor.py        # Process log files
│
├── integrations/
│   ├── git_integration.py      # Git repository integration
│   └── jira_integration.py     # JIRA system integration
│
├── processing_layer/
│   └── agents/
│       └── orchestrator.py     # Multi-agent coordination
│
├── output_layer/
│   ├── diagnosis_generator.py  # Generate diagnosis
│   └── team_assignment.py      # Route to teams
│
├── models/
│   ├── defect.py               # Defect data models
│   └── diagnosis.py            # Diagnosis data models
│
└── utils/                      # Utility modules

# Root level scripts
rca_scheduler.py                # Automated scheduler (label-based)
build_vector_db.py              # Build vector database from historical defects
jira_data_fetcher.py            # Fetch defects from JIRA
test_rca_dry_full.py            # Main dry test with dashboard

# Deployment scripts (Windows)
run_dashboard_demo.bat          # Run dashboard demo (no JIRA)
run_rca_cli.bat                 # Run CLI commands
run_rca_scheduler.bat           # Run automated scheduler

# Deployment scripts (Linux/Mac)
run_rca_scheduler.sh            # Run automated scheduler
```

### Key Components

| Component | File | Description |
|-----------|------|-------------|
| **Domain Classifier** | `domain_classifier.py` | ML-based team assignment (Audio/BT/Boot/Stability) |
| **RCA Dashboard** | `dashboard/dashboard_server.py` | Real-time monitoring with token tracking |
| **Token Tracker** | `dashboard/tracker.py` | Analysis and token tracking utilities |
| **Domain Config** | `domain_config.py` | Multi-industry domain support |
| **RCA Scheduler** | `rca_scheduler.py` | Automated job - fetches tickets by label |
| **RCA Engine** | `rca_engine.py` | Main orchestrator - coordinates all stages |
| **DLT Analyzer** | `dlt_analyzer.py` | Parses DLT logs (binary & text), extracts errors/patterns |
| **Historical Matcher** | `historical_matcher.py` | Keyword + semantic search for similar defects |
| **Vector Store** | `vector_store.py` | LanceDB integration for semantic search |
| **LLM Service** | `llm_service.py` | Azure OpenAI / GPT-4 integration |
| **Report Generator** | `report_generator.py` | Creates MD and HTML reports |
| **JIRA Service** | `jira_service.py` | JIRA API - fetch, comment, attach, link |

---

## 🚀 Installation

### Prerequisites

- Python 3.9+
- pip package manager

### Setup

```bash
# 1. Clone repository
git clone <repository-url>
cd RCA_agent-main

# 2. Create virtual environment
python -m venv venv

# 3. Activate virtual environment
# Windows:
venv\Scripts\activate
# Linux/Mac:
source venv/bin/activate

# 4. Install dependencies
pip install -r requirements_rca.txt

# 5. Build vector database (IMPORTANT - enables semantic search)
python build_vector_db.py
```

### Quick Start Scripts (Windows)

After setup, use these batch files to run the tool:

```batch
# Demo dashboard (no JIRA required - tests full pipeline)
run_dashboard_demo.bat

# Analyze a defect with dashboard
run_rca_cli.bat analyze SAM1-2001 --dashboard

# Analyze and upload to JIRA
run_rca_cli.bat analyze SAM1-2001 --jira

# Run automated scheduler
run_rca_scheduler.bat

# Run scheduler in dry-run mode (no JIRA updates)
run_rca_scheduler.bat --dry-run
```

### Quick Start Scripts (Linux/Mac)

```bash
# Make scripts executable
chmod +x run_rca_scheduler.sh

# Run automated scheduler
./run_rca_scheduler.sh

# Or run Python directly
python src/rca_infotainment/rca_cli.py analyze SAM1-2001 --dashboard
```

### Vector Database Build

The `build_vector_db.py` script:
1. Reads historical defects from `data/historical_defects/defects_data.json`
2. Generates 1536-dimensional embeddings for each defect
3. Stores them in LanceDB at `data/vector_db/defects.lance`

This enables **semantic similarity search** for finding duplicates and related defects.
Without this step, the system falls back to keyword-based search.

---

## ⚙️ Configuration

### Quick Start: Copy .env.example

```bash
# Copy the example environment file
cp .env.example .env

# Edit with your values
nano .env  # or use any editor
```

### Environment Variables (.env)

```bash
# ============================================================================
# DOMAIN CONFIGURATION (NEW!)
# ============================================================================
# Industry domain: automotive, telecom, healthcare, finance, manufacturing, software
RCA_DOMAIN=automotive
RCA_DOMAIN_LOG_FORMAT=dlt
RCA_ENABLE_DOMAIN_RULES=true

# ============================================================================
# DASHBOARD CONFIGURATION
# ============================================================================
DASHBOARD_PORT=5050
DASHBOARD_HOST=localhost
DASHBOARD_AUTO_OPEN=true

# ============================================================================
# TOKEN TRACKING & COST
# ============================================================================
TOKEN_COST_PER_1K=0.037      # €0.037 per 1000 tokens
TOKEN_DAILY_QUOTA=100000      # Daily limit (0 = unlimited)

# ============================================================================
# LLM CONFIGURATION
# ============================================================================
# Azure OpenAI (recommended)
AZURE_OPENAI_ENDPOINT=https://your-resource.openai.azure.com/
AZURE_OPENAI_API_KEY=your-api-key
AZURE_OPENAI_DEPLOYMENT_NAME=gpt-4
AZURE_OPENAI_API_VERSION=2024-02-15-preview

# OR OpenAI
# OPENAI_API_KEY=your-api-key

# ============================================================================
# JIRA INTEGRATION
# ============================================================================
JIRA_URL=https://yourcompany.atlassian.net
JIRA_EMAIL=your-email@company.com
JIRA_API_TOKEN=your-api-token
JIRA_PROJECT_KEY=SAM1

# Git Integration (optional)
GIT_REPO_URL=https://github.com/org/repo.git
GIT_TOKEN=your-personal-access-token
GIT_BRANCH=main
```

### Configuration File

Edit `config/config.yaml`:

```yaml
# Enable services
llm:
  provider: "azure_openai"  # or "openai" or "placeholder"

integrations:
  jira:
    enabled: true
  git:
    enabled: true

# Duplicate detection thresholds
thresholds:
  duplicate: 0.90    # 90%+ = duplicate
  related: 0.75      # 75%+ = related
  min_similarity: 0.50
```

---

## 📖 Usage

### Quick Start: Dry Test with Dashboard

```bash
# Run dry test (no JIRA, uses sample DLT file)
# Opens dashboard automatically at http://localhost:5050
python test_rca_dry_full.py

# With specific domain
$env:RCA_DOMAIN='telecom'
python test_rca_dry_full.py
```

### CLI Commands

```bash
# List all defects
python -m src.rca_infotainment.rca_cli list

# Show statistics
python -m src.rca_infotainment.rca_cli stats

# Search historical defects
python -m src.rca_infotainment.rca_cli search "bluetooth timeout"

# Analyze a defect (local mode)
python -m src.rca_infotainment.rca_cli analyze SAM1-2001

# Analyze and upload to JIRA
python -m src.rca_infotainment.rca_cli analyze SAM1-2001 --jira

# Check service status
python -m src.rca_infotainment.rca_cli status
```

### Python API

```python
from src.rca_infotainment.rca_engine import RCAEngine
from src.rca_infotainment.llm_service import LLMService
from src.utils.config import load_config

# Initialize
config = load_config("config/config.yaml")
engine = RCAEngine(config)
engine.set_llm_client(LLMService(config))

# Analyze defect
result = engine.analyze_defect(
    defect_id="SAM1-2001",
    from_jira=False,
    upload_to_jira=False
)

print(f"Root Cause: {result['root_cause']}")
print(f"Confidence: {result['confidence']:.0%}")
```

### Test Scripts

The repository includes several test scripts for different purposes:

| Script | Purpose |
|--------|---------|
| `test_rca_dry_full.py` | **Main dry test** - Full RCA with dashboard, no JIRA |
| `test_dashboard_tokens.py` | Test dashboard token tracking |
| `test_html_report_dry.py` | Test HTML report generation |
| `test_local_rca.py` | Test local RCA without external services |
| `test_llm_integration.py` | Test LLM service integration |
| `test_vector_store.py` | Test vector database operations |
| `test_vector_integration.py` | Test vector search integration |
| `test_jira_fetcher.py` | Test JIRA data fetching |
| `test_jira_search.py` | Test JIRA search functionality |
| `test_rca_scheduler.py` | Test automated scheduler |

```bash
# Run main dry test (recommended for first-time users)
python test_rca_dry_full.py

# Test HTML report generation
python test_html_report_dry.py

# Test vector store search
python test_vector_store.py
```

---

## ⏰ Automated Scheduling (No Manual Intervention)

### Overview

The RCA Scheduler automatically fetches and analyzes JIRA tickets based on labels - **no manual intervention required**.

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│                       AUTOMATED RCA WORKFLOW                                     │
└─────────────────────────────────────────────────────────────────────────────────┘

   USER/TESTER                           RCA SCHEDULER (Automated)
       │                                         │
       │  Adds label "needs-rca"                 │
       │  to JIRA ticket                         │
       ▼                                         │
  ┌──────────┐                                   │
  │  JIRA    │                                   │
  │ SAM1-2001│ ◄──────── Scheduled Job ──────────┤
  │          │           (every 5 min)           │
  │ [needs-  │                                   │
  │   rca]   │                                   │
  └──────────┘                                   │
       │                                         │
       │  Fetches tickets with                   │
       │  label "needs-rca"                      │
       ▼                                         ▼
  ┌──────────────────────────────────────────────────────────────────────────────┐
  │  AUTOMATIC PROCESSING                                                         │
  │                                                                                │
  │  1. Fetch ticket by label: needs-rca                                          │
  │  2. Add label: rca-in-progress                                                │
  │  3. Run RCA analysis (DLT → Vector DB → LLM)                                  │
  │  4. Generate MD/HTML reports                                                  │
  │  5. Update JIRA: comment + attachments + duplicate links                     │
  │  6. Update labels: remove "needs-rca", add "rca-complete"                    │
  └──────────────────────────────────────────────────────────────────────────────┘
       │
       ▼
  ┌──────────┐
  │  JIRA    │
  │ SAM1-2001│
  │          │
  │ [rca-    │  ← RCA Comment + Reports attached
  │ complete]│
  └──────────┘
```

### Scheduler Commands

```bash
# Run once (process all tickets with trigger labels)
python rca_scheduler.py

# Run continuously as daemon (every 5 minutes)
python rca_scheduler.py --daemon

# Custom interval (every 1 minute)
python rca_scheduler.py --daemon --interval 60

# Test mode (no JIRA updates)
python rca_scheduler.py --dry-run

# Custom trigger labels
python rca_scheduler.py --labels needs-rca auto-analyze
```

### Label-Based Workflow

| Label | Purpose | When Applied |
|-------|---------|--------------|
| `needs-rca` | Trigger RCA | User adds to ticket |
| `rca-in-progress` | Analysis running | Scheduler adds automatically |
| `rca-complete` | Analysis done | Scheduler adds on success |
| `rca-error` | Analysis failed | Scheduler adds on error |

### Schedule with Windows Task Scheduler

```powershell
# Create scheduled task (runs every 5 minutes)
schtasks /create /tn "RCA Scheduler" /tr "python C:\path\to\rca_scheduler.py" /sc minute /mo 5

# View task
schtasks /query /tn "RCA Scheduler"

# Delete task
schtasks /delete /tn "RCA Scheduler" /f
```

### Schedule with Linux Cron

```bash
# Edit crontab
crontab -e

# Add line (runs every 5 minutes)
*/5 * * * * cd /path/to/RCA_agent && python rca_scheduler.py >> logs/cron.log 2>&1
```

### Scheduler Configuration

Edit `config/config.yaml`:

```yaml
scheduler:
  # Labels that trigger RCA
  trigger_labels:
    - "needs-rca"
    - "auto-rca"
  
  # Label added after success
  completion_label: "rca-complete"
  
  # Max tickets per run
  max_tickets_per_run: 10
  
  # Only process open tickets
  jql_filter: "status != Closed"
  
  # Daemon interval (seconds)
  daemon_interval: 300
```

---

## 📁 Data Structure

```
data/
├── defects/
│   └── jira_api_defects.json      # Current defects to analyze
│
├── dlt_logs/
│   ├── audio_delay_defect.dlt     # DLT log files (binary or text)
│   ├── bt_disconnect_defect.dlt   # Auto-detected by analyze_file()
│   └── ...
│
├── historical_defects/
│   └── defects_data.json          # SOURCE: 1000+ historical defects
│               │
│               │  build_vector_db.py
│               │  (generates 1536-dim embeddings)
│               ▼
├── vector_db/                      # LanceDB vector database
│   ├── defects.lance/              # PRIMARY SEARCH: Embedded defects
│   │   ├── data/                   # Vector data files
│   │   ├── _transactions/          # Transaction logs
│   │   └── _versions/              # Version history
│   └── __manifest/                 # Database manifest
│
└── knowledge_base/
    └── domain_knowledge/           # DOMAIN KNOWLEDGE (MD Files)
        ├── 01_audio_subsystem.md       # Audio architecture & issues
        ├── 02_bluetooth_connectivity.md # BT stack & profiles
        ├── 03_dlt_logging_guide.md      # APP_ID/CTX_ID mappings
        ├── 04_boot_and_system.md        # Boot sequence knowledge
        ├── 05_vehicle_bus_communication.md # CAN/MOST protocols
        ├── 06_kpi_definitions.md        # KPI thresholds & analysis
        └── 07_rca_quick_reference.md    # Pattern → Root Cause lookup
```

### Vector Database Build Flow

```
┌─────────────────────────────────────────────────────────────────┐
│   defects_data.json                                              │
│   (1000+ historical defects)                                     │
└───────────────────────────┬─────────────────────────────────────┘
                            │
                            │  python build_vector_db.py
                            │
                            ▼
┌─────────────────────────────────────────────────────────────────┐
│   For each defect:                                               │
│   1. Combine: summary + description + component + root_cause     │
│   2. Generate embedding (1536 dimensions)                        │
│   3. Store in LanceDB                                            │
└───────────────────────────┬─────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────────┐
│   data/vector_db/defects.lance                                   │
│   (Fast semantic similarity search)                              │
└─────────────────────────────────────────────────────────────────┘
```

### Search Priority

1. **Primary**: Vector DB semantic search (if `data/vector_db` exists)
2. **Fallback**: Keyword-based search on JSON (if Vector DB unavailable)

### Historical Defect Format

```json
{
  "key": "SAM1-342",
  "summary": "Audio takes long time to start after source change",
  "description": "Switching from FM Radio to USB causes noticeable delay",
  "component": "AudioService",
  "labels": ["audio", "source-switch", "latency"],
  "root_cause": "Audio buffer size was set to 1024 samples causing flush delay",
  "resolution": "Fixed",
  "fix_commit": "abc123def",
  "related_file": "src/audio/AudioMixer.cpp",
  "duplicate_to": ["SAM1-156", "SAM1-892"]
}
```

### Domain Knowledge Files

Located in `data/knowledge_base/domain_knowledge/`:

| File | Purpose | Contains |
|------|---------|----------|
| `01_audio_subsystem.md` | Audio architecture | AudioFocusManager states, common issues, DLT patterns |
| `02_bluetooth_connectivity.md` | BT stack | HFP/A2DP profiles, connection state machines |
| `03_dlt_logging_guide.md` | Log parsing | DLT format, APP_ID→Component, CTX_ID mapping |
| `04_boot_and_system.md` | Boot process | Boot phases, timing requirements |
| `05_vehicle_bus_communication.md` | CAN/MOST | Bus protocols, message handling |
| `06_kpi_definitions.md` | KPI thresholds | STR <200ms, LUM <500ms, BOOT <3000ms |
| `07_rca_quick_reference.md` | Pattern lookup | DLT Pattern → Root Cause → Fix tables |

#### Example: Pattern → Root Cause Lookup (from `07_rca_quick_reference.md`)

```
┌─────────────────────────────────────────┬───────────────────────────┬─────────────────┐
│ DLT Pattern                             │ Root Cause                │ Fix Area        │
├─────────────────────────────────────────┼───────────────────────────┼─────────────────┤
│ buffer flush timeout buffer_size=2048   │ Buffer too large          │ Config: → 512   │
│ state stuck state=PHONE_FOCUS           │ Missing state transition  │ Code: handler   │
│ ACK timeout waiting for device          │ Protocol timeout          │ Timeout config  │
│ STR.*duration=[3-9][0-9]{2}             │ Multiple possible         │ Check sub-times │
└─────────────────────────────────────────┴───────────────────────────┴─────────────────┘
```

#### How Domain Knowledge is Used

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                    DOMAIN KNOWLEDGE INTEGRATION                              │
└─────────────────────────────────────────────────────────────────────────────┘

    DLT Log: "[AUDIO] AudioMixer buffer flush timeout buffer_size=2048"
                                    │
                                    ▼
    ┌─────────────────────────────────────────────────────────────────────┐
    │  1. DLT Analyzer extracts:                                          │
    │     • APP_ID: AUDI                                                   │
    │     • Pattern: "buffer flush timeout"                                │
    │     • Value: buffer_size=2048                                        │
    └─────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
    ┌─────────────────────────────────────────────────────────────────────┐
    │  2. Lookup in 03_dlt_logging_guide.md:                              │
    │     APP_ID "AUDI" → AudioService                                     │
    │     CTX_ID "MIX0" → AudioMixer                                       │
    └─────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
    ┌─────────────────────────────────────────────────────────────────────┐
    │  3. Lookup in 07_rca_quick_reference.md:                            │
    │     Pattern "buffer flush timeout buffer_size=2048"                  │
    │     → Root Cause: "Buffer too large"                                 │
    │     → Fix: "Config: reduce to 512"                                   │
    └─────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
    ┌─────────────────────────────────────────────────────────────────────┐
    │  4. Lookup in 06_kpi_definitions.md:                                │
    │     STR threshold: < 200ms                                           │
    │     Buffer flush causing STR > 200ms = KPI FAILURE                   │
    └─────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
    ┌─────────────────────────────────────────────────────────────────────┐
    │  5. Combined with Vector DB results (similar historical defects)    │
    │     + LLM Analysis                                                   │
    │     → Final Root Cause with high confidence                         │
    └─────────────────────────────────────────────────────────────────────┘
```

---

## 🔧 API Reference

### RCAEngine

```python
class RCAEngine:
    def analyze_defect(
        defect_id: str,
        from_jira: bool = False,
        upload_to_jira: bool = True,
        mark_duplicates: bool = True
    ) -> Dict[str, Any]:
        """
        Perform complete RCA for a defect.
        
        Returns:
            {
                "defect_id": "SAM1-2001",
                "status": "completed",
                "root_cause": "...",
                "confidence": 0.92,
                "duplicate_info": {...},
                "reports": {"markdown": {...}, "html": {...}}
            }
        """
```

### VectorStore

```python
class VectorStore:
    def search_similar_defects(
        query: str,
        limit: int = 5,
        component_filter: str = None
    ) -> List[Dict[str, Any]]:
        """
        Semantic search for similar defects.
        
        Returns:
            [
                {"key": "SAM1-342", "summary": "...", "distance": 0.08},
                ...
            ]
        """
```

---

## 📜 License

MIT License

---

## 🤝 Support

- GitHub Issues: [repository-url]/issues
- Documentation: [docs/](docs/)

---

**Version**: 2.0.0  
**Last Updated**: 2026-07-10

### Changelog v2.0.0

- Added Real-Time Monitoring Dashboard with live token tracking
- Added Multi-Industry Domain Support (automotive, telecom, healthcare, finance, manufacturing, software)
- Added Token Consumption Tracking per analysis stage
- Added Analysis Throttling (2-second gap between concurrent analyses)
- Added .env.example with comprehensive configuration
- Updated branding to "RCA MONITORING DASHBOARD"
- Added domain-aware LLM prompts
- Improved auto-scroll for live event logs