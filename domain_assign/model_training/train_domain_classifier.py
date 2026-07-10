#!/usr/bin/env python3
"""
Domain Classification Model Training Example

This script demonstrates how to train a domain classifier using the synthesized data.
It uses a sentence transformer model for text embedding and classification.
"""

import pandas as pd
import numpy as np
from pathlib import Path
from typing import Tuple
import pickle

from sklearn.model_selection import train_test_split, cross_val_score, StratifiedKFold
from sklearn.metrics import classification_report, confusion_matrix
from sklearn.linear_model import LogisticRegression
from sklearn.ensemble import RandomForestClassifier
import matplotlib.pyplot as plt
import seaborn as sns

# Import the data loader
from load_domain_data import DomainDataLoader, DOMAINS


class DomainClassifier:
    """Train and evaluate domain classification models"""
    
    def __init__(self, model_type: str = 'logistic'):
        self.model_type = model_type
        self.model = None
        self.vectorizer = None
        self.label_encoder = None
        
    def load_sentence_transformer(self, model_name: str = 'all-MiniLM-L6-v2'):
        """Load sentence transformer for text embeddings"""
        try:
            from sentence_transformers import SentenceTransformer
            
            # Check if local model exists
            local_model_path = Path(model_name)
            if local_model_path.exists():
                print(f"Loading local model from {model_name}")
                self.vectorizer = SentenceTransformer(str(local_model_path))
            else:
                print(f"Loading model: {model_name}")
                self.vectorizer = SentenceTransformer(model_name)
            
            print(f"✓ Loaded sentence transformer: {model_name}")
        except ImportError:
            print("⚠️  sentence-transformers not installed. Using TF-IDF fallback.")
            self.load_tfidf_vectorizer()
    
    def load_tfidf_vectorizer(self):
        """Fallback to TF-IDF if sentence transformers not available"""
        from sklearn.feature_extraction.text import TfidfVectorizer
        
        self.vectorizer = TfidfVectorizer(
            max_features=1000,
            ngram_range=(1, 2),
            min_df=2,
            stop_words='english'
        )
        print("✓ Using TF-IDF vectorizer (fallback)")
    
    def encode_texts(self, texts: list, fit: bool = False) -> np.ndarray:
        """Encode texts to vectors"""
        
        if self.vectorizer is None:
            self.load_sentence_transformer()
        
        # Sentence transformer
        if hasattr(self.vectorizer, 'encode'):
            embeddings = self.vectorizer.encode(texts, show_progress_bar=True)
            return embeddings
        
        # TF-IDF
        else:
            if fit:
                embeddings = self.vectorizer.fit_transform(texts)
            else:
                embeddings = self.vectorizer.transform(texts)
            return embeddings.toarray()
    
    def prepare_labels(self, domains: pd.Series, fit: bool = False) -> np.ndarray:
        """Encode domain labels to integers"""
        
        if fit or self.label_encoder is None:
            from sklearn.preprocessing import LabelEncoder
            self.label_encoder = LabelEncoder()
            self.label_encoder.fit(DOMAINS)
        
        labels = self.label_encoder.transform(domains)
        return labels
    
    def train(self, X_train: np.ndarray, y_train: np.ndarray):
        """Train the classification model"""
        
        print(f"\nTraining {self.model_type} classifier...")
        
        if self.model_type == 'logistic':
            self.model = LogisticRegression(
                max_iter=1000,
                multi_class='multinomial',
                class_weight='balanced',
                random_state=42
            )
        elif self.model_type == 'random_forest':
            self.model = RandomForestClassifier(
                n_estimators=100,
                max_depth=20,
                class_weight='balanced',
                random_state=42,
                n_jobs=-1
            )
        else:
            raise ValueError(f"Unknown model type: {self.model_type}")
        
        self.model.fit(X_train, y_train)
        
        # Training accuracy
        train_acc = self.model.score(X_train, y_train)
        print(f"✓ Training accuracy: {train_acc:.3f}")
    
    def cross_validate(self, X: np.ndarray, y: np.ndarray, cv_folds: int = 5):
        """Perform k-fold cross-validation"""
        
        print(f"\nPerforming {cv_folds}-fold cross-validation...")
        
        # Create model
        if self.model_type == 'logistic':
            model = LogisticRegression(
                max_iter=1000,
                multi_class='multinomial',
                class_weight='balanced',
                random_state=42
            )
        elif self.model_type == 'random_forest':
            model = RandomForestClassifier(
                n_estimators=100,
                max_depth=20,
                class_weight='balanced',
                random_state=42,
                n_jobs=-1
            )
        else:
            raise ValueError(f"Unknown model type: {self.model_type}")
        
        # Stratified K-Fold
        skf = StratifiedKFold(n_splits=cv_folds, shuffle=True, random_state=42)
        
        # Perform cross-validation
        cv_scores = cross_val_score(model, X, y, cv=skf, scoring='accuracy', n_jobs=-1)
        
        print(f"\nCross-validation results:")
        print("-" * 60)
        for i, score in enumerate(cv_scores, 1):
            print(f"  Fold {i}: {score:.3f}")
        print("-" * 60)
        print(f"  Mean CV Accuracy: {cv_scores.mean():.3f} (+/- {cv_scores.std() * 2:.3f})")
        print(f"  Min: {cv_scores.min():.3f}, Max: {cv_scores.max():.3f}")
        
        return cv_scores
    
    def evaluate(self, X_test: np.ndarray, y_test: np.ndarray):
        """Evaluate the model on test set"""
        
        if self.model is None:
            raise ValueError("Model not trained yet!")
        
        # Predictions
        y_pred = self.model.predict(X_test)
        
        # Test accuracy
        test_acc = self.model.score(X_test, y_test)
        print(f"\n✓ Test accuracy: {test_acc:.3f}")
        
        # Classification report
        print("\nClassification Report:")
        print("="*60)
        report = classification_report(
            y_test, 
            y_pred, 
            target_names=self.label_encoder.classes_,
            digits=3
        )
        print(report)
        
        # Confusion matrix
        cm = confusion_matrix(y_test, y_pred)
        self.plot_confusion_matrix(cm, self.label_encoder.classes_)
        
        return test_acc, report, cm
    
    def plot_confusion_matrix(self, cm: np.ndarray, class_names: list):
        """Plot confusion matrix"""
        
        plt.figure(figsize=(10, 8))
        sns.heatmap(
            cm, 
            annot=True, 
            fmt='d', 
            cmap='Blues',
            xticklabels=class_names,
            yticklabels=class_names
        )
        plt.title('Domain Classification Confusion Matrix')
        plt.ylabel('True Domain')
        plt.xlabel('Predicted Domain')
        plt.tight_layout()
        plt.savefig('confusion_matrix.png', dpi=300, bbox_inches='tight')
        print("\n✓ Confusion matrix saved to confusion_matrix.png")
    
    def predict(self, texts: list) -> list:
        """Predict domains for new texts"""
        
        if self.model is None:
            raise ValueError("Model not trained yet!")
        
        # Encode texts
        X = self.encode_texts(texts)
        
        # Predict
        y_pred = self.model.predict(X)
        
        # Decode labels
        domains = self.label_encoder.inverse_transform(y_pred)
        
        return domains
    
    def save_model(self, filepath: str):
        """Save trained model"""
        
        model_data = {
            'model': self.model,
            'vectorizer': self.vectorizer,
            'label_encoder': self.label_encoder,
            'model_type': self.model_type
        }
        
        with open(filepath, 'wb') as f:
            pickle.dump(model_data, f)
        
        print(f"\n✓ Model saved to {filepath}")
    
    def load_model(self, filepath: str):
        """Load trained model"""
        
        with open(filepath, 'rb') as f:
            model_data = pickle.load(f)
        
        self.model = model_data['model']
        self.vectorizer = model_data['vectorizer']
        self.label_encoder = model_data['label_encoder']
        self.model_type = model_data['model_type']
        
        print(f"\n✓ Model loaded from {filepath}")


def train_domain_classifier(model_type: str = 'logistic', 
                            use_sentence_transformer: bool = True):
    """Complete training pipeline"""
    
    print("\n" + "="*80)
    print("DOMAIN CLASSIFICATION MODEL TRAINING")
    print("="*80 + "\n")
    
    # Load data
    print("Step 1: Loading synthesized data...")
    loader = DomainDataLoader(".")
    combined_df = loader.load_all_synthesized_data()
    loader.print_statistics()
    
    # Prepare train/test split
    print("\nStep 2: Preparing train/test split...")
    train_df, test_df = loader.prepare_for_training(test_size=0.2, stratify=True)
    
    # Initialize classifier
    print("\nStep 3: Initializing classifier...")
    classifier = DomainClassifier(model_type=model_type)
    
    if use_sentence_transformer:
        classifier.load_sentence_transformer('all-MiniLM-L6-v2')
    else:
        classifier.load_tfidf_vectorizer()
    
    # Encode training data
    print("\nStep 4: Encoding training texts...")
    X_train = classifier.encode_texts(train_df['text'].tolist(), fit=True)
    y_train = classifier.prepare_labels(train_df['domain'], fit=True)
    
    print(f"✓ Training features shape: {X_train.shape}")
    print(f"✓ Training labels shape: {y_train.shape}")
    
    # Encode test data
    print("\nStep 5: Encoding test texts...")
    X_test = classifier.encode_texts(test_df['text'].tolist(), fit=False)
    y_test = classifier.prepare_labels(test_df['domain'], fit=False)
    
    print(f"✓ Test features shape: {X_test.shape}")
    print(f"✓ Test labels shape: {y_test.shape}")
    
    # Perform cross-validation on ALL data
    print("\nStep 6: Cross-validation on full dataset...")
    X_all = classifier.encode_texts(combined_df['text'].tolist(), fit=False)
    y_all = classifier.prepare_labels(combined_df['domain'], fit=False)
    cv_scores = classifier.cross_validate(X_all, y_all, cv_folds=5)
    
    # Train model
    print("\nStep 7: Training final model on training set...")
    classifier.train(X_train, y_train)
    
    # Evaluate model
    print("\nStep 8: Evaluating on held-out test set...")
    test_acc, report, cm = classifier.evaluate(X_test, y_test)
    
    # Save model
    print("\nStep 9: Saving model...")
    model_filename = f'domain_classifier_{model_type}.pkl'
    classifier.save_model(model_filename)
    
    # Test predictions
    print("\nStep 10: Testing predictions on samples...")
    test_samples = [
        "Bluetooth phone disconnects after 10 minutes of hands-free call",
        "Audio playback has stuttering during USB source switch",
        "System freeze and yellow screen after suspend to RAM",
        "Boot time exceeds 60 seconds on cold start"
    ]
    
    predictions = classifier.predict(test_samples)
    
    print("\nSample Predictions:")
    print("-" * 80)
    for text, pred in zip(test_samples, predictions):
        print(f"Text: {text[:60]}...")
        print(f"Predicted Domain: {pred}\n")
    
    print("\n" + "="*80)
    print("TRAINING COMPLETE!")
    print("="*80)
    print(f"\nModel Type: {model_type}")
    print(f"Cross-Validation Mean Accuracy: {cv_scores.mean():.3f} (+/- {cv_scores.std() * 2:.3f})")
    print(f"Test Set Accuracy: {test_acc:.3f}")
    print(f"Model saved to: {model_filename}")
    print(f"Confusion matrix saved to: confusion_matrix.png")
    
    return classifier, test_acc, cv_scores


def main():
    """Main entry point"""
    
    import argparse
    
    parser = argparse.ArgumentParser(description='Train domain classification model')
    parser.add_argument('--model', type=str, default='logistic',
                       choices=['logistic', 'random_forest'],
                       help='Model type to train')
    parser.add_argument('--vectorizer', type=str, default='sentence_transformer',
                       choices=['sentence_transformer', 'tfidf'],
                       help='Text vectorization method')
    
    args = parser.parse_args()
    
    use_st = args.vectorizer == 'sentence_transformer'
    
    classifier, accuracy, cv_scores = train_domain_classifier(
        model_type=args.model,
        use_sentence_transformer=use_st
    )
    
    return classifier


if __name__ == "__main__":
    classifier = main()
