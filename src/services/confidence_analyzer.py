# src/services/confidence_analyzer.py
import logging
import torch
import torch.nn.functional as F
from typing import Dict, List, Any, Optional

class ConfidenceAnalyzer:
    def __init__(self):
        self.logger = logging.getLogger(__name__)
    
    def calculate_token_confidence(self, scores: List[torch.Tensor]) -> Dict[str, Any]:
        """Calculate confidence from model output scores."""
        if not scores:
            return {
                'avg_confidence': 0.0,
                'min_confidence': 0.0,
                'max_confidence': 0.0,
                'confidence_scores': [],
                'confidence_label': 'Unknown'
            }
        
        try:
            confidences = []
            for score in scores:
                # Apply softmax and get max probability
                probs = F.softmax(score, dim=-1)
                max_prob = probs.max().item()
                confidences.append(max_prob)
            
            avg_conf = sum(confidences) / len(confidences) if confidences else 0.0
            min_conf = min(confidences) if confidences else 0.0
            max_conf = max(confidences) if confidences else 0.0
            
            confidence_label = self._interpret_confidence(avg_conf)
            
            return {
                'avg_confidence': round(avg_conf, 3),
                'min_confidence': round(min_conf, 3),
                'max_confidence': round(max_conf, 3),
                'confidence_scores': [round(c, 3) for c in confidences],
                'confidence_label': confidence_label
            }
            
        except Exception as e:
            self.logger.error(f"Confidence calculation error: {e}")
            return {
                'avg_confidence': 0.0,
                'min_confidence': 0.0,
                'max_confidence': 0.0,
                'confidence_scores': [],
                'confidence_label': 'Error'
            }
    
    def _interpret_confidence(self, score: float) -> str:
        """Convert confidence score to human-readable label."""
        if score is None:
            return "Unknown"
        elif score >= 0.85:
            return "High"
        elif score >= 0.65:
            return "Medium"
        elif score >= 0.45:
            return "Low"
        else:
            return "Very Low"
    
    def analyze_generation_quality(self, generated_text: str, confidence_score: float) -> Dict[str, Any]:
        """Analyze overall quality of generation."""
        quality_indicators = {
            'text_length': len(generated_text),
            'has_sql_keyword': any(kw in generated_text.upper() for kw in ['SELECT', 'FROM', 'WHERE', 'JOIN']),
            'has_semicolon': generated_text.strip().endswith(';'),
            'has_backticks': '```' in generated_text,
            'confidence_score': confidence_score
        }
        
        # Calculate quality score
        quality_score = 0
        if quality_indicators['has_sql_keyword']:
            quality_score += 25
        if quality_indicators['has_semicolon']:
            quality_score += 20
        if quality_indicators['text_length'] > 10:  # Has some content
            quality_score += 20
        if confidence_score >= 0.6:  # High confidence
            quality_score += 35
        
        quality_label = self._interpret_quality(quality_score)
        
        return {
            'quality_score': quality_score,
            'quality_label': quality_label,
            'indicators': quality_indicators
        }
    
    def _interpret_quality(self, score: int) -> str:
        """Convert quality score to label."""
        if score >= 80:
            return "Excellent"
        elif score >= 60:
            return "Good"
        elif score >= 40:
            return "Fair"
        else:
            return "Poor"
    
    def get_confidence_summary(self, confidence_data: Dict[str, Any]) -> str:
        """Get human-readable confidence summary."""
        avg_conf = confidence_data.get('avg_confidence', 0)
        label = confidence_data.get('confidence_label', 'Unknown')
        
        return f"Confidence: {avg_conf:.1%} ({label})"