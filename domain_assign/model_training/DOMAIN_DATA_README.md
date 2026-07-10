# Domain Assignment Synthesized Data

## Overview
This directory contains synthesized defect data for training domain classification models. The data has been generated to augment existing historical defects with comprehensive examples across four key automotive infotainment system domains.

## Four Target Domains

### 1. Audio System
Defects related to audio playback, processing, and output:
- Audio source switching and routing
- Volume control and audio mixing
- Audio format support and codecs
- Speaker configuration and balance
- Audio quality issues (noise, distortion, artifacts)
- Audio focus management
- Voice guidance and TTS
- Radio tuners (FM/DAB/Satellite)

### 2. Stability/memory
Defects related to system stability and memory management:
- Memory leaks and heap corruption
- Out-of-memory (OOM) errors
- System crashes and kernel panics
- Resource exhaustion (file descriptors, PIDs, threads)
- Performance degradation over time
- Process crashes and segmentation faults
- Watchdog timeouts
- Graphics/GPU memory issues

### 3. Bluetooth connectivity
Defects related to Bluetooth connections and operations:
- Device pairing and authentication
- Connection stability and dropouts
- Audio streaming (A2DP, HFP)
- Profile management (PBAP, AVRCP, MAP)
- Hands-free calling issues
- Multi-device and multipoint connections
- Bluetooth range and RF issues
- BLE (Bluetooth Low Energy) problems

### 4. Boot and System
Defects related to boot process and system initialization:
- Boot time performance
- Boot failures and hangs
- Filesystem mounting and integrity
- Service initialization and dependencies
- Bootloader and kernel issues
- Cold vs warm boot differences
- Power management during boot
- Recovery and fallback mechanisms

## Dataset Files

### 1. domain_assignment_synthesized_data.csv
**Format:** Structured CSV with key fields
**Records:** 110 defects (27-28 per domain)
**Fields:**
- `ticket_id`: Unique identifier (SAM1-3001 to SAM1-3110)
- `summary`: Brief one-line description
- `description`: Detailed problem description
- `root_cause`: Technical root cause analysis
- `domain`: Target domain label
- `priority`: Priority level (P0-P3)
- `severity`: Severity (Critical, High, Medium, Low)

**Use Case:** Structured training data with clear fields for classification models

### 2. domain_training_extended.csv
**Format:** Extended CSV with additional metadata
**Records:** 100 defects (25 per domain)
**Fields:**
- All fields from dataset 1, plus:
- `component`: Specific component affected
- `labels`: Comma-separated tags
- `frequency`: How often the issue occurs (Always, Sometimes, Rarely, Frequently)

**Use Case:** Richer feature set for advanced classification and feature engineering

### 3. domain_labeled_defects_detailed.csv
**Format:** Matches existing balanced_dataset.csv format
**Records:** 20 detailed defects (5 per domain)
**Fields:**
- `Unnamed: 0`: Index
- `ticket_id`: Unique identifier
- `summary`: Brief description
- `description`: VERY detailed description with:
  - Problem description
  - Steps to reproduce
  - Expected vs actual results
  - Log evidence
  - Technical analysis
  - Root cause
- `manual_label`: Domain classification

**Use Case:** Most comprehensive descriptions for text-based ML models, matches your existing data format

## Data Statistics

### Total Synthesized Records
- **domain_assignment_synthesized_data.csv**: 110 records
- **domain_training_extended.csv**: 100 records  
- **domain_labeled_defects_detailed.csv**: 20 records
- **TOTAL**: 230 synthesized defect records

### Distribution by Domain
Each dataset is balanced across the four domains:
- Audio System: ~25-28 records per file
- Stability/memory: ~25-28 records per file
- Bluetooth connectivity: ~25-28 records per file
- Boot and System: ~25-28 records per file

### Severity Distribution
- **Critical/P0**: ~15% (Boot failures, system crashes, security issues)
- **High/P1**: ~40% (Memory leaks, connection failures, major bugs)
- **Medium/P2**: ~35% (Performance issues, minor functional defects)
- **Low/P3**: ~10% (Cosmetic issues, nice-to-have fixes)

## Usage Recommendations

### Training Pipeline
1. **Data Combination**: Merge synthesized data with existing historical_defects.json and jira_api_defects.json
2. **Data Validation**: Check for data quality and balance across domains
3. **Feature Engineering**: Extract features from detailed descriptions
4. **Model Training**: Train classification model (see below)
5. **Validation**: Use held-out test set for evaluation

### Recommended Approach for Domain Classification

#### Option 1: Text-Based Classification (Recommended)
```python
# Use the detailed descriptions for training
import pandas as pd
from sklearn.model_selection import train_test_split
from transformers import AutoTokenizer, AutoModelForSequenceClassification

# Load data
df1 = pd.read_csv('domain_assignment_synthesized_data.csv')
df2 = pd.read_csv('domain_training_extended.csv')
df3 = pd.read_csv('domain_labeled_defects_detailed.csv')

# Combine all data
all_data = pd.concat([
    df1[['summary', 'description', 'domain']],
    df2[['summary', 'description', 'domain']],
    df3[['summary', 'description', 'manual_label']].rename(columns={'manual_label': 'domain'})
])

# Create combined text field
all_data['text'] = all_data['summary'] + ' ' + all_data['description']

# Train BERT-based classifier
# Use existing all-MiniLM-L6-v2 model or similar
```

#### Option 2: Feature-Based Classification
```python
# Extract features from structured fields
features = ['priority', 'severity', 'component', 'labels', 'frequency']
# Use TF-IDF on text fields
# Combine with categorical features
# Train gradient boosting or random forest classifier
```

### Data Augmentation Suggestions
1. **Paraphrasing**: Use the synthesized data as templates and create variations
2. **Combination**: Mix symptoms from different defects in same domain
3. **Historical Integration**: Blend with your existing defects_data.json
4. **Cross-Domain Edge Cases**: Create ambiguous cases spanning multiple domains

## Integration with Existing Data

### Merging with Historical Data
```python
import json
import pandas as pd

# Load existing historical data
with open('../data/historical_defects/defects_data.json', 'r') as f:
    historical = json.load(f)

# Load synthesized data
synthesized = pd.read_csv('domain_assignment_synthesized_data.csv')

# Add domain labels to historical data (if not present)
# Train model on synthesized data
# Predict domains for historical data
# Combine datasets
```

### Vector Database Integration
The synthesized data can be indexed into your LanceDB vector database:
```python
# Add to vector database for semantic search
from RCA_agent.src.knowledge_layer.vector_store import VectorStore

vs = VectorStore()
for _, row in synthesized_df.iterrows():
    vs.add_defect({
        'id': row['ticket_id'],
        'summary': row['summary'],
        'description': row['description'],
        'domain': row['domain'],
        'root_cause': row['root_cause']
    })
```

## Data Quality Notes

### Realism
- All defects based on common automotive infotainment system issues
- Root causes reflect real technical problems
- Symptoms and behaviors mirror actual defect reports
- Technical details (buffer sizes, timeouts, error codes) are realistic

### Variety
- Multiple manifestations of each domain category
- Different severity levels and priorities
- Various component interactions
- Edge cases and corner scenarios

### Consistency
- Ticket ID numbering system consistent (SAM1-XXXX)
- Domain labels standardized across all files
- Field formats aligned with existing data
- Compatible with existing RCA_agent infrastructure

## Next Steps

1. **Review Data**: Examine samples from each domain to ensure quality
2. **Validate Balance**: Check class distribution is appropriate
3. **Merge Datasets**: Combine with existing historical data
4. **Train Baseline Model**: Establish baseline accuracy metrics
5. **Iterate**: Refine based on model performance
6. **Deploy**: Integrate with RCA_agent domain classification pipeline

## File Locations
```
RCA_agent/Model/model_training/
├── domain_assignment_synthesized_data.csv       # 110 records, structured
├── domain_training_extended.csv                 # 100 records, rich metadata  
├── domain_labeled_defects_detailed.csv          # 20 records, very detailed
└── DOMAIN_DATA_README.md                        # This file
```

## Contact
For questions about this synthesized data or suggestions for additional scenarios, please refer to the main RCA_agent documentation.

---
Generated: 2026-07-09
Purpose: Domain classification training data augmentation
Domains: Audio System, Stability/memory, Bluetooth connectivity, Boot and System
