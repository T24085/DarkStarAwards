"""Axe-core accessibility audit runner."""
import json
import logging
from pathlib import Path
from typing import Dict, Any, List
from playwright.sync_api import Page

logger = logging.getLogger(__name__)

class AxeRunner:
    """Run axe-core accessibility audits."""
    
    def __init__(self, artifacts_dir: Path):
        """Initialize with artifacts directory."""
        self.artifacts_dir = artifacts_dir
    
    def run_audit(self, page: Page, submission_id: str) -> Dict[str, Any]:
        """
        Run axe-core audit on the page.
        Returns violation count and top violations.
        """
        try:
            # Inject axe-core script
            page.add_script_tag(url='https://unpkg.com/axe-core@4.8.0/axe.min.js')
            
            # Run axe
            axe_results = page.evaluate("""
                async () => {
                    return await axe.run();
                }
            """)
            
            violations = axe_results.get('violations', [])
            violation_count = len(violations)
            
            # Get top 5 violations
            top_violations = sorted(
                violations,
                key=lambda v: len(v.get('nodes', [])),
                reverse=True
            )[:5]
            
            top_violations_summary = [
                {
                    'id': v.get('id'),
                    'impact': v.get('impact'),
                    'description': v.get('description'),
                    'help': v.get('help'),
                    'nodeCount': len(v.get('nodes', []))
                }
                for v in top_violations
            ]
            
            # Save full report
            report_path = self.artifacts_dir / f"{submission_id}_axe.json"
            with open(report_path, 'w', encoding='utf-8') as f:
                json.dump(axe_results, f, indent=2, ensure_ascii=False)
            
            result = {
                'axeViolationsCount': violation_count,
                'topViolations': top_violations_summary,
                'axeReportPath': str(report_path)
            }
            
            logger.info(f"Axe audit completed: {violation_count} violations")
            return result
        
        except Exception as e:
            logger.error(f"Error running axe audit: {e}")
            return {
                'axeViolationsCount': 0,
                'topViolations': [],
                'axeReportPath': None
            }

