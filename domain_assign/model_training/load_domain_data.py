#!/usr/bin/env python3
"""
Domain Assignment Data Utilities

This script provides utilities for working with the synthesized domain assignment data.
It can load, validate, merge, and prepare the data for training.
"""

import pandas as pd
import json
from pathlib import Path
from typing import Dict, List, Tuple
import numpy as np
from collections import Counter

# Define the four target domains
DOMAINS = [
    "audio_system_domain",
    "stability_memory_domain", 
    "bluetooth_connectivity_domain",
    "boot_and_system_domain"
]


class DomainDataLoader:
    """Load and manage domain assignment synthesized data"""
    
    def __init__(self, model_training_path: str = "."):
        self.model_training_path = Path(model_training_path)
        self.datasets = {}
        
    def load_all_synthesized_data(self) -> pd.DataFrame:
        """Load all synthesized datasets and combine them"""
        
        # Load dataset 1: Structured data
        df1 = pd.read_csv(self.model_training_path / "domain_assignment_synthesized_data.csv")
        df1['source'] = 'synthesized_structured'
        df1['text'] = df1['summary'] + ' ' + df1['description']
        
        # Load dataset 2: Extended data
        df2 = pd.read_csv(self.model_training_path / "domain_training_extended.csv")
        df2['source'] = 'synthesized_extended'
        df2['text'] = df2['summary'] + ' ' + df2['description']
        
        # Load dataset 3: Detailed data
        df3 = pd.read_csv(self.model_training_path / "domain_labeled_defects_detailed.csv")
        df3 = df3.rename(columns={'manual_label': 'domain'})
        df3['source'] = 'synthesized_detailed'
        df3['text'] = df3['summary'] + ' ' + df3['description']
        
        # Store individual datasets
        self.datasets['structured'] = df1
        self.datasets['extended'] = df2
        self.datasets['detailed'] = df3
        
        # Combine all datasets
        common_cols = ['ticket_id', 'summary', 'description', 'domain', 'text', 'source']
        
        combined = pd.concat([
            df1[common_cols],
            df2[common_cols],
            df3[common_cols]
        ], ignore_index=True)
        
        self.datasets['combined'] = combined
        
        print(f"✓ Loaded {len(df1)} records from structured dataset")
        print(f"✓ Loaded {len(df2)} records from extended dataset")
        print(f"✓ Loaded {len(df3)} records from detailed dataset")
        print(f"✓ Total combined records: {len(combined)}")
        
        return combined
    
    def get_dataset_statistics(self, df: pd.DataFrame = None) -> Dict:
        """Calculate statistics for the dataset"""
        
        if df is None:
            df = self.datasets.get('combined')
            if df is None:
                raise ValueError("No dataset loaded. Call load_all_synthesized_data() first.")
        
        stats = {
            'total_records': len(df),
            'domain_distribution': df['domain'].value_counts().to_dict(),
            'avg_description_length': df['description'].str.len().mean(),
            'avg_summary_length': df['summary'].str.len().mean(),
            'unique_tickets': df['ticket_id'].nunique(),
        }
        
        # Add domain percentages
        total = len(df)
        stats['domain_percentages'] = {
            domain: (count / total) * 100 
            for domain, count in stats['domain_distribution'].items()
        }
        
        # Priority distribution if available
        if 'priority' in df.columns:
            stats['priority_distribution'] = df['priority'].value_counts().to_dict()
            
        # Severity distribution if available
        if 'severity' in df.columns:
            stats['severity_distribution'] = df['severity'].value_counts().to_dict()
        
        return stats
    
    def print_statistics(self, df: pd.DataFrame = None):
        """Print formatted statistics"""
        
        stats = self.get_dataset_statistics(df)
        
        print("\n" + "="*60)
        print("DOMAIN ASSIGNMENT DATA STATISTICS")
        print("="*60)
        
        print(f"\nTotal Records: {stats['total_records']}")
        print(f"Unique Tickets: {stats['unique_tickets']}")
        
        print("\n📊 Domain Distribution:")
        print("-" * 60)
        for domain in DOMAINS:
            count = stats['domain_distribution'].get(domain, 0)
            pct = stats['domain_percentages'].get(domain, 0)
            bar = "█" * int(pct / 2)  # Scale for display
            print(f"{domain:25} {count:3} ({pct:5.1f}%) {bar}")
        
        if 'priority_distribution' in stats:
            print("\n🔴 Priority Distribution:")
            print("-" * 60)
            for priority, count in sorted(stats['priority_distribution'].items()):
                print(f"{priority:10} {count:3}")
        
        if 'severity_distribution' in stats:
            print("\n⚠️  Severity Distribution:")
            print("-" * 60)
            for severity, count in sorted(stats['severity_distribution'].items()):
                print(f"{severity:10} {count:3}")
        
        print(f"\n📝 Text Statistics:")
        print("-" * 60)
        print(f"Avg Summary Length:     {stats['avg_summary_length']:.0f} chars")
        print(f"Avg Description Length: {stats['avg_description_length']:.0f} chars")
        print("="*60 + "\n")
    
    def merge_with_historical_data(self, historical_data_path: str) -> pd.DataFrame:
        """Merge synthesized data with historical defects"""
        
        # Load historical data
        historical_path = Path(historical_data_path)
        
        if historical_path.suffix == '.json':
            with open(historical_path, 'r') as f:
                historical = json.load(f)
            
            # Convert to DataFrame
            if isinstance(historical, list):
                hist_df = pd.DataFrame(historical)
            else:
                hist_df = pd.DataFrame([historical])
        else:
            hist_df = pd.read_csv(historical_path)
        
        # Ensure historical data has required columns
        if 'domain' not in hist_df.columns:
            print("⚠️  Historical data missing 'domain' column. You'll need to classify it first.")
            hist_df['domain'] = None
        
        # Create text field if not present
        if 'text' not in hist_df.columns:
            if 'summary' in hist_df.columns and 'description' in hist_df.columns:
                hist_df['text'] = hist_df['summary'] + ' ' + hist_df['description']
            elif 'description' in hist_df.columns:
                hist_df['text'] = hist_df['description']
        
        hist_df['source'] = 'historical'
        
        # Get combined synthesized data
        synth_df = self.datasets.get('combined')
        if synth_df is None:
            synth_df = self.load_all_synthesized_data()
        
        # Find common columns
        common_cols = list(set(hist_df.columns) & set(synth_df.columns))
        
        # Merge datasets
        merged = pd.concat([
            hist_df[common_cols],
            synth_df[common_cols]
        ], ignore_index=True)
        
        print(f"\n✓ Merged {len(hist_df)} historical records with {len(synth_df)} synthesized records")
        print(f"✓ Total merged dataset: {len(merged)} records")
        
        return merged
    
    def prepare_for_training(self, df: pd.DataFrame = None, 
                            test_size: float = 0.2,
                            stratify: bool = True) -> Tuple[pd.DataFrame, pd.DataFrame]:
        """Prepare data for model training with train/test split"""
        
        if df is None:
            df = self.datasets.get('combined')
            if df is None:
                df = self.load_all_synthesized_data()
        
        # Remove records without domain labels
        df_labeled = df[df['domain'].notna()].copy()
        
        # Encode domain labels
        df_labeled['domain_id'] = pd.Categorical(df_labeled['domain'], 
                                                   categories=DOMAINS).codes
        
        # Split train/test
        from sklearn.model_selection import train_test_split
        
        if stratify:
            train_df, test_df = train_test_split(
                df_labeled, 
                test_size=test_size, 
                random_state=42,
                stratify=df_labeled['domain']
            )
        else:
            train_df, test_df = train_test_split(
                df_labeled,
                test_size=test_size,
                random_state=42
            )
        
        print(f"\n✓ Prepared training data:")
        print(f"  Training set: {len(train_df)} records")
        print(f"  Test set:     {len(test_df)} records")
        print(f"  Stratified:   {stratify}")
        
        return train_df, test_df
    
    def export_for_vector_db(self, output_path: str, df: pd.DataFrame = None):
        """Export data in format suitable for vector database ingestion"""
        
        if df is None:
            df = self.datasets.get('combined')
            if df is None:
                df = self.load_all_synthesized_data()
        
        # Prepare records for vector DB
        records = []
        for _, row in df.iterrows():
            record = {
                'id': row['ticket_id'],
                'summary': row['summary'],
                'description': row['description'],
                'domain': row['domain'],
                'text': row['text'],
                'source': row.get('source', 'synthesized')
            }
            
            # Add optional fields if available
            for field in ['root_cause', 'component', 'priority', 'severity', 'labels']:
                if field in row and pd.notna(row[field]):
                    record[field] = row[field]
            
            records.append(record)
        
        # Save as JSON
        output_path = Path(output_path)
        with open(output_path, 'w') as f:
            json.dump(records, f, indent=2)
        
        print(f"\n✓ Exported {len(records)} records to {output_path}")
    
    def get_samples_by_domain(self, domain: str, n: int = 5) -> pd.DataFrame:
        """Get sample records for a specific domain"""
        
        df = self.datasets.get('combined')
        if df is None:
            df = self.load_all_synthesized_data()
        
        samples = df[df['domain'] == domain].head(n)
        return samples
    
    def print_domain_samples(self, domain: str, n: int = 3):
        """Print sample defects for a domain"""
        
        samples = self.get_samples_by_domain(domain, n)
        
        print(f"\n{'='*80}")
        print(f"SAMPLE DEFECTS - {domain.upper()}")
        print(f"{'='*80}\n")
        
        for idx, (_, row) in enumerate(samples.iterrows(), 1):
            print(f"[{idx}] {row['ticket_id']}: {row['summary']}")
            desc = row['description'][:200] + "..." if len(row['description']) > 200 else row['description']
            print(f"    {desc}\n")
        
        print(f"{'='*80}\n")


def main():
    """Example usage of DomainDataLoader"""
    
    print("Domain Assignment Data Loader")
    print("=" * 60)
    
    # Initialize loader
    loader = DomainDataLoader(".")
    
    # Load all synthesized data
    combined_df = loader.load_all_synthesized_data()
    
    # Print statistics
    loader.print_statistics()
    
    # Show samples from each domain
    for domain in DOMAINS:
        loader.print_domain_samples(domain, n=2)
    
    # Prepare for training
    train_df, test_df = loader.prepare_for_training(test_size=0.2)
    
    print("\n✅ Data loading complete!")
    print(f"   Access datasets via loader.datasets dictionary")
    print(f"   - loader.datasets['combined']: All synthesized data")
    print(f"   - loader.datasets['structured']: Structured dataset")
    print(f"   - loader.datasets['extended']: Extended dataset")
    print(f"   - loader.datasets['detailed']: Detailed dataset")
    
    # Export for vector DB
    loader.export_for_vector_db("domain_defects_vectordb.json")
    
    return loader


if __name__ == "__main__":
    loader = main()
