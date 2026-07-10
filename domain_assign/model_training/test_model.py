#!/usr/bin/env python3
"""
Test the trained domain classification model
"""

import pickle
import numpy as np

def load_model(model_path='domain_classifier_logistic.pkl'):
    """Load the trained model"""
    print(f"Loading model from {model_path}...")
    with open(model_path, 'rb') as f:
        model_data = pickle.load(f)
    
    print(f"✓ Model loaded successfully")
    print(f"  Model type: {model_data['model_type']}")
    print(f"  Vectorizer type: {type(model_data['vectorizer']).__name__}")
    
    return model_data

def predict_domain(model_data, defect_text):
    """Predict domain for a defect description"""
    
    # Get components
    model = model_data['model']
    vectorizer = model_data['vectorizer']
    label_encoder = model_data['label_encoder']
    
    # Encode text
    if hasattr(vectorizer, 'encode'):
        # Sentence transformer
        X = vectorizer.encode([defect_text], show_progress_bar=False)
    else:
        # TF-IDF
        X = vectorizer.transform([defect_text]).toarray()
    
    # Predict
    y_pred = model.predict(X)
    y_proba = model.predict_proba(X)
    
    # Decode label
    domain = label_encoder.inverse_transform(y_pred)[0]
    
    # Get probabilities for all classes
    probabilities = {}
    for i, class_name in enumerate(label_encoder.classes_):
        probabilities[class_name] = y_proba[0][i]
    
    return domain, probabilities

def main():
    print("="*80)
    print("DOMAIN CLASSIFIER MODEL TESTING")
    print("="*80)
    
    # Load model
    model_data = load_model('domain_classifier_logistic.pkl')
    
    # Test cases - various defect descriptions
    test_cases = [
        # Audio System
        "Audio playback stutters when switching from radio to USB. Buffer underrun detected in logs.",
        "Microphone echo during hands-free Bluetooth calls. Caller hears their own voice.",
        "Volume control not working properly. Audio too loud at low settings.",
        
        # Bluetooth connectivity
        "Bluetooth phone disconnects after 10 minutes. Auto-reconnect fails.",
        "Cannot pair iPhone to vehicle. Android phones work fine.",
        "Bluetooth audio quality very poor with frequent dropouts.",
        
        # Boot and System
        "System takes 90 seconds to boot instead of 45 seconds.",
        "Kernel panic during boot sequence. System never completes startup.",
        "Boot hangs at 67% progress indefinitely.",
        
        # Stability/memory
        "Memory leak in navigation service. Memory grows 50MB per hour.",
        "System crash with out of memory error after 6 hours operation.",
        "Application segfault when switching user profiles.",
        "Random system freeze and yellow screen of death.",
    ]
    
    print(f"\n{'='*80}")
    print("TESTING ON SAMPLE DEFECTS")
    print(f"{'='*80}\n")
    
    for i, defect in enumerate(test_cases, 1):
        print(f"Test {i}:")
        print(f"  Defect: {defect[:70]}...")
        
        # Predict
        domain, probabilities = predict_domain(model_data, defect)
        
        print(f"  Predicted Domain: {domain}")
        print(f"  Confidence Scores:")
        
        # Sort by probability
        sorted_probs = sorted(probabilities.items(), key=lambda x: x[1], reverse=True)
        for dom, prob in sorted_probs:
            bar = "█" * int(prob * 30)
            print(f"    {dom:30} {prob:6.2%} {bar}")
        
        print()
    
    print("="*80)
    print("INTERACTIVE TESTING")
    print("="*80)
    print("\nYou can now test your own defect descriptions.")
    print("Type 'quit' to exit.\n")
    
    while True:
        try:
            user_input = input("Enter defect description: ").strip()
            
            if user_input.lower() in ['quit', 'exit', 'q']:
                print("\nExiting...")
                break
            
            if not user_input:
                continue
            
            # Predict
            domain, probabilities = predict_domain(model_data, user_input)
            
            print(f"\n  Predicted Domain: {domain}")
            print(f"  Confidence Scores:")
            
            sorted_probs = sorted(probabilities.items(), key=lambda x: x[1], reverse=True)
            for dom, prob in sorted_probs:
                bar = "█" * int(prob * 30)
                print(f"    {dom:30} {prob:6.2%} {bar}")
            
            print()
        
        except KeyboardInterrupt:
            print("\n\nExiting...")
            break
        except Exception as e:
            print(f"\nError: {e}")
            continue

if __name__ == "__main__":
    main()
