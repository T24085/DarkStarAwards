"""Firebase client for Firestore and Storage operations."""
import json
import logging
from datetime import datetime, timedelta
from typing import Optional, Dict, Any
from firebase_admin import initialize_app, credentials, firestore, storage
from firebase_admin.exceptions import FirebaseError

logger = logging.getLogger(__name__)

class FirebaseClient:
    """Client for Firebase operations."""
    
    _initialized = False
    
    def __init__(self, project_id: str, credentials_path: str, storage_bucket: str):
        """Initialize Firebase client."""
        if not FirebaseClient._initialized:
            cred = credentials.Certificate(credentials_path)
            initialize_app(cred, {
                'storageBucket': storage_bucket
            })
            FirebaseClient._initialized = True
        
        self.db = firestore.client()
        self.bucket = storage.bucket()
        self.project_id = project_id
    
    def claim_submission(self, submission_id: str, worker_id: str) -> bool:
        """
        Claim a submission for processing using a transaction.
        Returns True if successfully claimed, False if already claimed.
        """
        submission_ref = self.db.collection('entries').document(submission_id)
        
        try:
            @firestore.transactional
            def claim_transaction(transaction):
                doc = submission_ref.get(transaction=transaction)
                if not doc.exists:
                    return False
                
                data = doc.to_dict()
                status = data.get('status', 'pending')
                
                # Check if already claimed or stale
                if status == 'scoring':
                    claimed_at = data.get('claimedAt')
                    if claimed_at:
                        claimed_time = claimed_at
                        if isinstance(claimed_time, datetime):
                            if datetime.now() - claimed_time < timedelta(minutes=30):
                                return False  # Still valid claim
                        # Stale claim, allow re-claim
                
                if status != 'pending' and status != 'scoring':
                    return False
                
                # Claim it
                transaction.update(submission_ref, {
                    'status': 'scoring',
                    'claimedBy': worker_id,
                    'claimedAt': firestore.SERVER_TIMESTAMP
                })
                return True
            
            transaction = self.db.transaction()
            return claim_transaction(transaction)
        
        except Exception as e:
            logger.error(f"Error claiming submission {submission_id}: {e}")
            return False
    
    def get_pending_submissions(self, limit: int = 5) -> list:
        """Get pending submissions ordered by submittedAt."""
        try:
            query = (
                self.db.collection('entries')
                .where('status', '==', 'pending')
                .order_by('createdAt', direction=firestore.Query.ASCENDING)
                .limit(limit)
            )
            docs = query.stream()
            return [{'id': doc.id, **doc.to_dict()} for doc in docs]
        except Exception as e:
            logger.error(f"Error fetching pending submissions: {e}")
            return []
    
    def write_results(
        self,
        submission_id: str,
        scores: Dict[str, int],
        notes: Dict[str, str],
        artifacts: Dict[str, str],
        metrics: Dict[str, Any],
        error: Optional[Dict[str, str]] = None
    ):
        """Write scoring results back to Firestore."""
        submission_ref = self.db.collection('entries').document(submission_id)
        
        result_data = {
            'scores': scores,
            'notes': notes,
            'artifacts': artifacts,
            'metrics': metrics,
            'scoredAt': firestore.SERVER_TIMESTAMP,
            'judgeVersion': self.judge_version
        }
        
        update_data = {
            'status': 'error' if error else 'scored',
            'result': result_data
        }
        
        if error:
            update_data['error'] = error
        
        try:
            submission_ref.update(update_data)
            logger.info(f"Results written for submission {submission_id}")
        except Exception as e:
            logger.error(f"Error writing results for {submission_id}: {e}")
            raise
    
    def upload_artifact(self, local_path: str, remote_path: str) -> str:
        """Upload artifact to Firebase Storage and return public URL."""
        try:
            blob = self.bucket.blob(remote_path)
            blob.upload_from_filename(local_path)
            blob.make_public()
            return blob.public_url
        except Exception as e:
            logger.error(f"Error uploading artifact {local_path}: {e}")
            raise
    
    def __init__(self, project_id: str, credentials_path: str, storage_bucket: str):
        """Initialize Firebase client."""
        if not FirebaseClient._initialized:
            cred = credentials.Certificate(credentials_path)
            initialize_app(cred, {
                'storageBucket': storage_bucket
            })
            FirebaseClient._initialized = True
        
        self.db = firestore.client()
        self.bucket = storage.bucket()
        self.project_id = project_id
        
        # Get judge version
        import sys
        from pathlib import Path
        sys.path.insert(0, str(Path(__file__).parent.parent))
        from config import Config
        self._judge_version = Config.JUDGE_VERSION
    
    @property
    def judge_version(self) -> str:
        """Get judge version from config."""
        return self._judge_version

