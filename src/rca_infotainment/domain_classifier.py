"""
Domain Classifier Service - ML-based domain assignment for RCA

Uses a trained model to automatically assign defects to the appropriate domain:
- audio_system_domain: Audio playback, routing, mixing, quality issues
- stability_memory_domain: Memory leaks, crashes, OOM errors, system stability
- bluetooth_connectivity_domain: Pairing, connections, audio streaming, HFP/A2DP
- boot_and_system_domain: Boot failures, initialization, startup performance
"""

import os
import pickle
import logging
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple

# Domain mappings
DOMAIN_INFO = {
    "audio_system_domain": {
        "display_name": "Audio System",
        "icon": "🔊",
        "team": "Audio Engineering",
        "keywords": ["audio", "sound", "speaker", "microphone", "volume", "playback", "AUD", "mixer"]
    },
    "stability_memory_domain": {
        "display_name": "Stability/Memory",
        "icon": "💾",
        "team": "System Stability Team",
        "keywords": ["memory", "leak", "crash", "OOM", "freeze", "stability", "fault", "segfault"]
    },
    "bluetooth_connectivity_domain": {
        "display_name": "Bluetooth Connectivity",
        "icon": "📱",
        "team": "Connectivity Team",
        "keywords": ["bluetooth", "BT", "pairing", "A2DP", "HFP", "phone", "handsfree", "wireless"]
    },
    "boot_and_system_domain": {
        "display_name": "Boot & System",
        "icon": "🚀",
        "team": "Boot/Platform Team",
        "keywords": ["boot", "startup", "init", "kernel", "system", "bootloader", "cold start"]
    }
}

# Friendly domain name mapping
DOMAIN_FRIENDLY_NAMES = {
    "audio_system_domain": "Audio",
    "stability_memory_domain": "Stability",
    "bluetooth_connectivity_domain": "Bluetooth",
    "boot_and_system_domain": "Boot"
}


class DomainClassifier:
    """
    ML-based domain classifier for automotive infotainment defects.
    
    Uses a pre-trained model (Sentence Transformer + Logistic Regression)
    to predict the appropriate domain for a defect based on its text.
    """
    
    def __init__(self, model_path: str = None):
        """
        Initialize the domain classifier.
        
        Args:
            model_path: Path to the model directory. If None, uses default location.
        """
        self.logger = logging.getLogger(__name__)
        self.model = None
        self.vectorizer = None
        self.label_encoder = None
        self.is_loaded = False
        
        # Default model path
        if model_path is None:
            base_path = Path(__file__).parent.parent.parent
            model_path = base_path / "domain_assign" / "model_training"
        
        self.model_path = Path(model_path)
        self.model_file = self.model_path / "domain_classifier_logistic.pkl"
        
        # Try to load model on init
        self._load_model()
    
    def _load_model(self) -> bool:
        """Load the trained model from disk."""
        if not self.model_file.exists():
            self.logger.debug(f"Domain classifier model  {self.model_file}")
            return False
        
        try:
            import warnings
            with warnings.catch_warnings():
                warnings.simplefilter("ignore")
                with open(self.model_file, 'rb') as f:
                    model_data = pickle.load(f)
            
            self.model = model_data['model']
            self.vectorizer = model_data['vectorizer']
            self.label_encoder = model_data['label_encoder']
            self.is_loaded = True
            
            self.logger.info(f"Domain classifier loaded: {model_data.get('model_type', 'unknown')}")
            return True
            
        except Exception as e:
            self.logger.debug(f"ML model not available, using keyword fallback: {e}")
            return False
    
    def predict(self, text: str) -> Tuple[str, float, Dict[str, float]]:
        """
        Predict domain for a defect based on its text.
        
        Args:
            text: Combined summary + description text
            
        Returns:
            Tuple of (predicted_domain, confidence, all_probabilities)
        """
        if not self.is_loaded:
            self.logger.info("Domain classifier loaded")
            return self._fallback_predict(text)
        
        try:
            # Encode text
            if hasattr(self.vectorizer, 'encode'):
                # Sentence transformer
                X = self.vectorizer.encode([text], show_progress_bar=False)
            else:
                # TF-IDF fallback
                X = self.vectorizer.transform([text]).toarray()
            
            # Predict
            y_pred = self.model.predict(X)
            y_proba = self.model.predict_proba(X)
            
            # Decode label
            domain = self.label_encoder.inverse_transform(y_pred)[0]
            confidence = float(max(y_proba[0]))
            
            # Get probabilities for all classes
            probabilities = {}
            for i, class_name in enumerate(self.label_encoder.classes_):
                probabilities[class_name] = float(y_proba[0][i])
            
            return domain, confidence, probabilities
            
        except Exception as e:
            self.logger.error(f"Domain prediction failed: {e}")
            return self._fallback_predict(text)
    
    def _fallback_predict(self, text: str) -> Tuple[str, float, Dict[str, float]]:
        """
        Keyword-based fallback when ML model is not available.
        
        Args:
            text: Combined summary + description text
            
        Returns:
            Tuple of (predicted_domain, confidence, all_probabilities)
        """
        text_lower = text.lower()
        scores = {}
        
        for domain, info in DOMAIN_INFO.items():
            score = 0
            for keyword in info["keywords"]:
                if keyword.lower() in text_lower:
                    score += 1
            scores[domain] = score
        
        # Find best match
        total_score = sum(scores.values()) or 1
        probabilities = {d: s / total_score for d, s in scores.items()}
        
        best_domain = max(scores.keys(), key=lambda d: scores[d])
        confidence = probabilities[best_domain] if scores[best_domain] > 0 else 0.25
        
        return best_domain, confidence, probabilities
    
    def predict_from_defect(self, defect_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Predict domain from defect data dictionary.
        
        Args:
            defect_data: Defect dictionary with 'summary' and 'description' fields
            
        Returns:
            Dictionary with prediction results
        """
        # Combine summary and description
        summary = defect_data.get('summary', '') or ''
        description = defect_data.get('description', '') or ''
        text = f"{summary} {description}".strip()
        
        if not text:
            return {
                "domain": "boot_and_system_domain",
                "domain_display": "Boot & System",
                "confidence": 0.0,
                "probabilities": {},
                "team": "Boot/Platform Team",
                "method": "default"
            }
        
        # Predict
        domain, confidence, probabilities = self.predict(text)
        
        # Get domain info
        info = DOMAIN_INFO.get(domain, {})
        
        return {
            "domain": domain,
            "domain_display": info.get("display_name", domain),
            "domain_short": DOMAIN_FRIENDLY_NAMES.get(domain, domain),
            "icon": info.get("icon", "📋"),
            "confidence": confidence,
            "probabilities": probabilities,
            "team": info.get("team", "Unknown Team"),
            "method": "ml_model" if self.is_loaded else "keyword_fallback"
        }
    
    def get_top_domains(self, text: str, top_k: int = 2) -> List[Dict[str, Any]]:
        """
        Get top K domain predictions with confidence scores.
        
        Args:
            text: Combined text to classify
            top_k: Number of top predictions to return
            
        Returns:
            List of domain predictions sorted by confidence
        """
        _, _, probabilities = self.predict(text)
        
        sorted_domains = sorted(
            probabilities.items(),
            key=lambda x: x[1],
            reverse=True
        )[:top_k]
        
        results = []
        for domain, prob in sorted_domains:
            info = DOMAIN_INFO.get(domain, {})
            results.append({
                "domain": domain,
                "domain_display": info.get("display_name", domain),
                "confidence": prob,
                "team": info.get("team", "Unknown Team"),
                "icon": info.get("icon", "📋")
            })
        
        return results
    
    def is_available(self) -> bool:
        """Check if the ML model is loaded and available."""
        return self.is_loaded
    
    @staticmethod
    def get_domain_info(domain: str) -> Dict[str, Any]:
        """Get information about a specific domain."""
        return DOMAIN_INFO.get(domain, {
            "display_name": domain,
            "icon": "📋",
            "team": "Unknown Team",
            "keywords": []
        })
    
    @staticmethod
    def get_all_domains() -> List[str]:
        """Get list of all supported domains."""
        return list(DOMAIN_INFO.keys())


# Singleton instance for easy access
_classifier_instance = None

def get_domain_classifier() -> DomainClassifier:
    """
    Get singleton instance of domain classifier.
    
    Returns:
        DomainClassifier instance
    """
    global _classifier_instance
    if _classifier_instance is None:
        _classifier_instance = DomainClassifier()
    return _classifier_instance


def predict_domain(text: str) -> Tuple[str, float]:
    """
    Quick utility function to predict domain for text.
    
    Args:
        text: Text to classify
        
    Returns:
        Tuple of (domain, confidence)
    """
    classifier = get_domain_classifier()
    domain, confidence, _ = classifier.predict(text)
    return domain, confidence


def predict_domain_for_defect(defect_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Quick utility function to predict domain for a defect.
    
    Args:
        defect_data: Defect dictionary
        
    Returns:
        Prediction result dictionary
    """
    classifier = get_domain_classifier()
    return classifier.predict_from_defect(defect_data)
