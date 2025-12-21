"""Lighthouse audit runner."""
import json
import logging
import subprocess
from pathlib import Path
from typing import Dict, Any, Optional

logger = logging.getLogger(__name__)

class LighthouseRunner:
    """Run Lighthouse audits and parse results."""
    
    def __init__(self, artifacts_dir: Path):
        """Initialize with artifacts directory."""
        self.artifacts_dir = artifacts_dir
    
    def run_audit(self, url: str, submission_id: str) -> Dict[str, Any]:
        """
        Run Lighthouse audit and return metrics.
        Returns dict with performance, accessibility, SEO, best practices scores.
        """
        output_path = self.artifacts_dir / f"{submission_id}_lighthouse.json"
        
        try:
            # Run Lighthouse via CLI
            cmd = [
                'lighthouse',
                url,
                '--output=json',
                f'--output-path={output_path}',
                '--only-categories=performance,accessibility,seo,best-practices',
                '--chrome-flags=--headless --no-sandbox --disable-gpu',
                '--quiet'
            ]
            
            logger.info(f"Running Lighthouse for {url}")
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=120
            )
            
            if result.returncode != 0:
                logger.warning(f"Lighthouse returned non-zero exit code: {result.stderr}")
                # Return default scores if Lighthouse fails
                return self._default_metrics()
            
            # Parse results
            with open(output_path, 'r', encoding='utf-8') as f:
                report = json.load(f)
            
            categories = report.get('categories', {})
            
            metrics = {
                'lighthousePerformance': int(categories.get('performance', {}).get('score', 0) * 100),
                'lighthouseAccessibility': int(categories.get('accessibility', {}).get('score', 0) * 100),
                'lighthouseSEO': int(categories.get('seo', {}).get('score', 0) * 100),
                'lighthouseBestPractices': int(categories.get('best-practices', {}).get('score', 0) * 100),
                'lighthouseReportPath': str(output_path)
            }
            
            logger.info(f"Lighthouse completed: {metrics}")
            return metrics
        
        except subprocess.TimeoutExpired:
            logger.error("Lighthouse audit timed out")
            return self._default_metrics()
        except FileNotFoundError:
            logger.warning("Lighthouse CLI not found. Install with: npm install -g lighthouse")
            return self._default_metrics()
        except Exception as e:
            logger.error(f"Error running Lighthouse: {e}")
            return self._default_metrics()
    
    def _default_metrics(self) -> Dict[str, int]:
        """Return default metrics when Lighthouse fails."""
        return {
            'lighthousePerformance': 0,
            'lighthouseAccessibility': 0,
            'lighthouseSEO': 0,
            'lighthouseBestPractices': 0,
            'lighthouseReportPath': None
        }

