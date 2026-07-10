#!/usr/bin/env python3
"""
Verify data shuffling and show expected improvements
"""

import pandas as pd

print("="*80)
print("DATA QUALITY VERIFICATION")
print("="*80)

# Check file 1
df1 = pd.read_csv("domain_assignment_synthesized_data.csv")
print(f"\nFile 1: domain_assignment_synthesized_data.csv")
print(f"  Total records: {len(df1)}")

# Count domain transitions
prev = None
transitions = 0
for _, row in df1.iterrows():
    if prev and prev != row['domain']:
        transitions += 1
    prev = row['domain']

print(f"  Domain transitions: {transitions}")
print(f"  Data quality: {'GOOD - Well shuffled' if transitions > 50 else 'BAD - Needs shuffling'}")

# Show first 10 to verify shuffling
print(f"\n  First 10 records:")
for i in range(10):
    print(f"    {i+1:2}. {df1.iloc[i]['ticket_id']:12} - {df1.iloc[i]['domain']}")

# Domain distribution
print(f"\n  Domain distribution:")
for domain, count in df1['domain'].value_counts().sort_index().items():
    print(f"    {domain:30} {count:3} records")

print("\n" + "="*80)
print("EXPECTED TRAINING IMPROVEMENTS")
print("="*80)
print("""
BEFORE (Ordered Data):
  - Test Accuracy: 100% (unrealistic)
  - Model too confident
  - Poor generalization expected

AFTER (Shuffled Data with Cross-Validation):
  - Cross-Validation Accuracy: 85-95% (realistic)
  - Test Accuracy: 85-95% (realistic)
  - Better generalization
  - More reliable performance estimate

The 5-fold cross-validation will give you a more honest assessment
of how well the model will perform on unseen data.
""")

print("="*80)
print("\nRun training to see the improved results:")
print("  python train_domain_classifier.py --model logistic --vectorizer sentence_transformer")
print("="*80)
