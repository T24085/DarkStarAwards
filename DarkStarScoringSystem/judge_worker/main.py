"""Main worker loop for DSSS."""
import logging
import time
import socket
from datetime import datetime
from pathlib import Path
from typing import Optional

import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from config import Config
from judge_worker.firebase_client import FirebaseClient
from judge_worker.playwright_capture import PlaywrightCapture
from judge_worker.ollama_judge import OllamaJudge
from judge_worker.scoring import ScoringEngine
from audits.lighthouse_runner import LighthouseRunner
from audits.axe_runner import AxeRunner

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('dsss_worker.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class JudgeWorker:
    """Main worker for processing submissions."""
    
    def __init__(self):
        """Initialize worker with all components."""
        Config.validate()
        
        self.worker_id = socket.gethostname()
        self.firebase = FirebaseClient(
            Config.FIREBASE_PROJECT_ID,
            Config.FIREBASE_CREDENTIALS_JSON,
            Config.STORAGE_BUCKET
        )
        self.ollama = OllamaJudge(Config.OLLAMA_HOST, Config.OLLAMA_MODEL)
        self.scoring = ScoringEngine()
        
        logger.info(f"Worker initialized: {self.worker_id}")
    
    def process_submission(self, submission: dict) -> bool:
        """
        Process a single submission through the full pipeline.
        Returns True if successful, False otherwise.
        """
        submission_id = submission['id']
        url = submission.get('url')
        category = submission.get('category', 'Unknown')
        
        if not url:
            logger.error(f"Submission {submission_id} has no URL")
            self._write_error(submission_id, "No URL provided", "validation")
            return False
        
        logger.info(f"Processing submission {submission_id}: {url}")
        
        try:
            # Step 1: Capture evidence with Playwright
            with PlaywrightCapture(Config.ARTIFACTS_DIR) as capture:
                evidence = capture.capture(url, submission_id)
            
            # Step 2: Run Lighthouse audit
            lighthouse_runner = LighthouseRunner(Config.ARTIFACTS_DIR)
            lighthouse_metrics = lighthouse_runner.run_audit(url, submission_id)
            
            # Step 3: Run axe-core audit (need to reload page)
            # For now, we'll use the evidence from capture
            # In a full implementation, we'd reload the page for axe
            axe_summary = {
                'axeViolationsCount': 0,  # Placeholder - would need page reload
                'topViolations': []
            }
            
            # Step 4: Calculate objective scores
            objective_scores = self.scoring.calculate_objective_scores(
                lighthouse_metrics,
                axe_summary
            )
            
            # Step 5: Get subjective scores from Ollama
            ollama_result = self.ollama.judge(
                url=url,
                category=category,
                extracted_structure=evidence['extracted'],
                lighthouse_metrics=lighthouse_metrics,
                axe_summary=axe_summary,
                console_error_count=evidence.get('console_error_count', 0),
                failed_request_count=evidence.get('failed_request_count', 0)
            )
            
            if not ollama_result:
                raise Exception("Ollama judgment failed")
            
            # Step 6: Combine scores
            all_scores = self.scoring.calculate_total_score(
                objective_scores,
                ollama_result['scores']
            )
            
            # Step 7: Upload artifacts
            artifacts = {}
            try:
                # Upload screenshots
                if 'desktop' in evidence['screenshots']:
                    desktop_url = self.firebase.upload_artifact(
                        evidence['screenshots']['desktop'],
                        f"submissions/{submission_id}/desktop.png"
                    )
                    artifacts['screenshotDesktopUrl'] = desktop_url
                
                if 'mobile' in evidence['screenshots']:
                    mobile_url = self.firebase.upload_artifact(
                        evidence['screenshots']['mobile'],
                        f"submissions/{submission_id}/mobile.png"
                    )
                    artifacts['screenshotMobileUrl'] = mobile_url
                
                # Upload Lighthouse report if available
                if lighthouse_metrics.get('lighthouseReportPath'):
                    report_url = self.firebase.upload_artifact(
                        lighthouse_metrics['lighthouseReportPath'],
                        f"submissions/{submission_id}/lighthouse.json"
                    )
                    artifacts['lighthouseReportUrl'] = report_url
                
            except Exception as e:
                logger.warning(f"Error uploading artifacts: {e}")
            
            # Step 8: Prepare metrics
            metrics = self.scoring.prepare_metrics(
                lighthouse_metrics,
                axe_summary,
                evidence.get('console_error_count', 0),
                evidence.get('failed_request_count', 0)
            )
            
            # Step 9: Write results to Firestore
            self.firebase.write_results(
                submission_id=submission_id,
                scores=all_scores,
                notes=ollama_result['notes'],
                artifacts=artifacts,
                metrics=metrics
            )
            
            logger.info(f"Successfully processed submission {submission_id}")
            return True
        
        except Exception as e:
            logger.error(f"Error processing submission {submission_id}: {e}", exc_info=True)
            self._write_error(submission_id, str(e), "processing")
            return False
    
    def _write_error(self, submission_id: str, message: str, stage: str):
        """Write error to Firestore."""
        try:
            self.firebase.write_results(
                submission_id=submission_id,
                scores={},
                notes={},
                artifacts={},
                metrics={},
                error={
                    'message': message,
                    'stage': stage,
                    'details': {}
                }
            )
        except Exception as e:
            logger.error(f"Error writing error status: {e}")
    
    def run_loop(self):
        """Main worker loop - polls for pending submissions."""
        logger.info("Starting worker loop...")
        
        while True:
            try:
                # Get pending submissions
                pending = self.firebase.get_pending_submissions(limit=Config.MAX_CONCURRENT_JOBS)
                
                if not pending:
                    logger.info(f"No pending submissions. Sleeping for {Config.POLL_INTERVAL_SECONDS}s...")
                    time.sleep(Config.POLL_INTERVAL_SECONDS)
                    continue
                
                # Process each submission
                for submission in pending:
                    submission_id = submission['id']
                    
                    # Try to claim
                    if not self.firebase.claim_submission(submission_id, self.worker_id):
                        logger.info(f"Could not claim submission {submission_id} (already claimed)")
                        continue
                    
                    logger.info(f"Claimed submission {submission_id}")
                    
                    # Process with timeout
                    start_time = time.time()
                    success = self.process_submission(submission)
                    elapsed = time.time() - start_time
                    
                    logger.info(f"Submission {submission_id} processed in {elapsed:.1f}s (success: {success})")
                    
                    # Small delay between jobs
                    time.sleep(5)
            
            except KeyboardInterrupt:
                logger.info("Worker stopped by user")
                break
            except Exception as e:
                logger.error(f"Error in worker loop: {e}", exc_info=True)
                time.sleep(60)  # Wait before retrying

def main():
    """Entry point."""
    worker = JudgeWorker()
    worker.run_loop()

if __name__ == '__main__':
    main()

