"""Scoring logic for objective and subjective metrics."""
import logging
from typing import Dict, Any

logger = logging.getLogger(__name__)

class ScoringEngine:
    """Calculate scores from objective metrics and Ollama judgments."""
    
    @staticmethod
    def calculate_objective_scores(
        lighthouse_metrics: Dict[str, int],
        axe_summary: Dict[str, Any]
    ) -> Dict[str, int]:
        """
        Calculate objective scores from Lighthouse and axe metrics.
        Returns dict with technical and accessibility scores.
        """
        # Technical score (0-20) from Lighthouse Performance
        lighthouse_perf = lighthouse_metrics.get('lighthousePerformance', 0)
        technical = round(lighthouse_perf / 100 * 20)
        
        # Accessibility score (0-10)
        # Base from Lighthouse accessibility (7 points max)
        lighthouse_a11y = lighthouse_metrics.get('lighthouseAccessibility', 0)
        base = round(lighthouse_a11y / 100 * 7)
        
        # Penalty from axe violations (up to 3 points)
        axe_violations = axe_summary.get('axeViolationsCount', 0)
        penalty = min(3, axe_violations // 5)
        
        accessibility = max(0, min(10, base - penalty))
        
        return {
            'technical': technical,
            'accessibility': accessibility
        }
    
    @staticmethod
    def calculate_total_score(
        objective_scores: Dict[str, int],
        ollama_scores: Dict[str, int]
    ) -> Dict[str, int]:
        """
        Combine objective and subjective scores.
        Returns complete scores dict with total (capped at 100).
        """
        scores = {
            **objective_scores,
            **ollama_scores
        }
        
        # Calculate total
        total = sum([
            scores.get('design', 0),
            scores.get('ux', 0),
            scores.get('technical', 0),
            scores.get('creativity', 0),
            scores.get('accessibility', 0),
            scores.get('content', 0),
            scores.get('bonus', 0)
        ])
        
        # Cap at 100
        scores['total'] = min(100, total)
        
        return scores
    
    @staticmethod
    def prepare_metrics(
        lighthouse_metrics: Dict[str, int],
        axe_summary: Dict[str, Any],
        console_error_count: int,
        failed_request_count: int
    ) -> Dict[str, Any]:
        """Prepare metrics dict for Firestore."""
        return {
            'lighthousePerformance': lighthouse_metrics.get('lighthousePerformance', 0),
            'lighthouseSEO': lighthouse_metrics.get('lighthouseSEO', 0),
            'lighthouseBestPractices': lighthouse_metrics.get('lighthouseBestPractices', 0),
            'lighthouseAccessibility': lighthouse_metrics.get('lighthouseAccessibility', 0),
            'axeViolationsCount': axe_summary.get('axeViolationsCount', 0),
            'consoleErrorCount': console_error_count,
            'failedRequestsCount': failed_request_count
        }

