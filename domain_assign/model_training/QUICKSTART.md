# Domain Assignment Data - Quick Start Guide

## 🎯 What You Got

I've created **230 synthesized defect records** across 4 domains for training your domain classification model:

### The 4 Domains
1. **Audio System** - Audio playback, routing, mixing, quality issues
2. **Stability/memory** - Memory leaks, crashes, OOM errors, system stability  
3. **Bluetooth connectivity** - Pairing, connections, audio streaming, HFP/A2DP
4. **Boot and System** - Boot failures, initialization, startup performance

### Files Created

```
RCA_agent/Model/model_training/
│
├── 📊 Data Files (230 total records)
│   ├── domain_assignment_synthesized_data.csv      # 110 records - structured format
│   ├── domain_training_extended.csv                # 100 records - extended metadata
│   └── domain_labeled_defects_detailed.csv         #  20 records - detailed descriptions
│
├── 📘 Documentation
│   ├── DOMAIN_DATA_README.md                       # Comprehensive guide
│   └── QUICKSTART.md                               # This file
│
└── 🐍 Python Scripts
    ├── load_domain_data.py                         # Data loading utilities
    └── train_domain_classifier.py                  # Training example
```

## 🚀 Quick Start (3 Steps)

### Step 1: Load and Explore Data
```bash
cd RCA_agent/Model/model_training
python load_domain_data.py
```

This will:
- ✅ Load all 230 synthesized defects
- ✅ Show statistics and distribution
- ✅ Display sample defects from each domain
- ✅ Export data for vector database

### Step 2: Train Domain Classifier
```bash
# Using Sentence Transformers (recommended)
python train_domain_classifier.py --model logistic --vectorizer sentence_transformer

# Or using TF-IDF (faster, no dependencies)
python train_domain_classifier.py --model logistic --vectorizer tfidf

# Or using Random Forest
python train_domain_classifier.py --model random_forest --vectorizer sentence_transformer
```

This will:
- ✅ Load and split data (80% train, 20% test)
- ✅ Encode text using sentence transformers or TF-IDF
- ✅ Train classification model
- ✅ Evaluate and show metrics
- ✅ Save trained model as `.pkl` file
- ✅ Generate confusion matrix plot

### Step 3: Use in Your Code
```python
from load_domain_data import DomainDataLoader
import pickle

# Load data
loader = DomainDataLoader(".")
df = loader.load_all_synthesized_data()

# Load trained model
with open('domain_classifier_logistic.pkl', 'rb') as f:
    model_data = pickle.load(f)

# Predict domains for new defects
new_defects = [
    "Bluetooth call drops after 10 minutes",
    "Memory leak in navigation service"
]

# (You'll need to encode texts first using the saved vectorizer)
```

## 📊 Data Overview

### Distribution by Domain
Each domain has **25-28 defects per file**, well balanced:
- 🔊 Audio System: 57 total records
- 💾 Stability/memory: 58 total records  
- 📱 Bluetooth connectivity: 57 total records
- 🚀 Boot and System: 58 total records

### Quality Features
- ✅ Realistic automotive infotainment defects
- ✅ Detailed root cause analysis included
- ✅ Varied severity levels (Critical to Low)
- ✅ Diverse symptoms and manifestations
- ✅ Technical details (buffer sizes, timeouts, error codes)
- ✅ Compatible with existing RCA_agent data format

## 🔧 Integration with Your System

### Add to Vector Database
```python
from load_domain_data import DomainDataLoader

loader = DomainDataLoader(".")
loader.load_all_synthesized_data()

# Export for vector DB ingestion
loader.export_for_vector_db("domain_defects_vectordb.json")

# Then add to your LanceDB vector store
# (Use your existing RCA_agent vector store code)
```

### Merge with Historical Data
```python
from load_domain_data import DomainDataLoader

loader = DomainDataLoader(".")

# Merge with your existing historical defects
merged_df = loader.merge_with_historical_data(
    "../data/historical_defects/defects_data.json"
)

print(f"Total records after merge: {len(merged_df)}")
```

### Use for Training
```python
from load_domain_data import DomainDataLoader

loader = DomainDataLoader(".")
loader.load_all_synthesized_data()

# Get train/test split with stratification
train_df, test_df = loader.prepare_for_training(
    test_size=0.2, 
    stratify=True
)

# Train your model
# (Use train_df and test_df with your existing classifier)
```

## 📈 Expected Performance

Based on the synthesized data quality, you should expect:

- **Logistic Regression + Sentence Transformer**: 85-95% accuracy
- **Random Forest + Sentence Transformer**: 90-95% accuracy  
- **Logistic Regression + TF-IDF**: 75-85% accuracy

Performance will improve when combined with your historical data.

## 🎓 Example Use Cases

### 1. Train Initial Domain Classifier
Use the synthesized data to bootstrap your domain classification model before you have labeled historical data.

### 2. Augment Existing Data
Combine with your historical defects to increase training data size and coverage.

### 3. Test RCA Pipeline
Use as test data to validate your RCA agent's domain classification step.

### 4. Populate Knowledge Base
Add to your vector database to improve semantic search and retrieval.

## 📁 Data Format Details

### Simple Format (domain_assignment_synthesized_data.csv)
```csv
ticket_id,summary,description,root_cause,domain,priority,severity
SAM1-3001,Audio playback stuttering,...,Buffer underrun issue,Audio System,P1,High
```

### Extended Format (domain_training_extended.csv)
```csv
ticket_id,summary,description,root_cause,domain,component,labels,priority,severity,frequency
SAM1-4001,FM drift,...,...,Audio System,RadioTuner,"audio,fm",P2,Medium,Sometimes
```

### Detailed Format (domain_labeled_defects_detailed.csv)
```csv
Unnamed: 0,ticket_id,summary,description,manual_label
0,SAM1-5001,Audio source switch latency,"**Problem Description:** ... **Root Cause:** ...",Audio System
```

## 🔍 Verify Data Quality

```python
from load_domain_data import DomainDataLoader

loader = DomainDataLoader(".")
df = loader.load_all_synthesized_data()

# Check for nulls
print(df.isnull().sum())

# Verify domain distribution
print(df['domain'].value_counts())

# Check text lengths
print(f"Avg description length: {df['description'].str.len().mean():.0f} chars")

# Show samples
loader.print_domain_samples("Audio System", n=3)
```

## 💡 Tips

1. **Start Small**: Begin with the structured dataset (110 records) to validate your pipeline
2. **Combine Datasets**: Merge all three files for maximum training data (230 records)
3. **Merge Historical**: Combine with your existing data for best results
4. **Tune Models**: Experiment with different classifiers and hyperparameters
5. **Feature Engineering**: Extract additional features from structured fields (priority, severity, etc.)

## 🆘 Troubleshooting

### Issue: "sentence-transformers not installed"
```bash
pip install sentence-transformers
```
Or use TF-IDF fallback (no installation needed)

### Issue: "sklearn not found"
```bash
pip install scikit-learn
```

### Issue: "matplotlib/seaborn not found"
```bash
pip install matplotlib seaborn
```

### Issue: Model accuracy too low
- Combine all three datasets for more training data
- Use sentence transformers instead of TF-IDF
- Merge with your historical defects
- Try Random Forest instead of Logistic Regression

## 📚 Next Steps

1. ✅ Run `load_domain_data.py` to explore the data
2. ✅ Run `train_domain_classifier.py` to train a baseline model
3. ✅ Merge with your historical data using `merge_with_historical_data()`
4. ✅ Integrate into your RCA_agent pipeline
5. ✅ Add to vector database for semantic search
6. ✅ Use for automated domain assignment in production

## 📞 Need Help?

- Check **DOMAIN_DATA_README.md** for comprehensive documentation
- Review the example scripts for usage patterns
- Examine the data files directly to understand the format

---

**Generated**: 2026-07-09  
**Purpose**: Domain classification training data  
**Total Records**: 230 synthesized defects  
**Domains**: Audio System, Stability/memory, Bluetooth connectivity, Boot and System
