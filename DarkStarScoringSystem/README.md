# Dark Star Scoring System (DSSS)

Automated website judging system for Dark Star Awards, running on Jetson Nano with Firebase and Ollama integration.

## Overview

DSSS automatically:
1. Detects new website submissions in Firebase
2. Captures website evidence using Playwright
3. Runs objective audits (Lighthouse, axe-core)
4. Uses Ollama for subjective scoring
5. Writes scores, notes, and artifacts back to Firebase

## Architecture

- **judge_worker/**: Main worker orchestration
  - `main.py`: Worker loop and job processing
  - `firebase_client.py`: Firestore and Storage operations
  - `playwright_capture.py`: Website evidence capture
  - `ollama_judge.py`: Ollama integration for subjective scoring
  - `scoring.py`: Score calculation logic

- **audits/**: Objective audit runners
  - `lighthouse_runner.py`: Lighthouse performance/accessibility audits
  - `axe_runner.py`: Axe-core accessibility violations

- **schemas/**: JSON schemas for validation
  - `ollama_output.schema.json`: Ollama response schema

- **utils/**: Utility functions

## Setup

### Prerequisites

1. **Jetson Nano** with:
   - Python 3.8+
   - Node.js (for Lighthouse)
   - Ollama installed and running

2. **Firebase**:
   - Service account credentials JSON
   - Firestore database created
   - Storage bucket configured

3. **Install Python dependencies**:
```bash
pip install -r requirements.txt
```

4. **Install Playwright browsers**:
```bash
playwright install chromium
```

5. **Install Lighthouse** (Node.js):
```bash
npm install -g lighthouse
```

6. **Setup Ollama**:
```bash
# Install Ollama
curl -fsSL https://ollama.ai/install.sh | sh

# Pull model
ollama pull llama3.1:8b
```

### Configuration

1. Copy `.env.example` to `.env`:
```bash
cp .env.example .env
```

2. Edit `.env` with your settings:
- Firebase project ID and credentials path
- Ollama host and model
- Worker polling interval
- Timeouts

3. Place Firebase service account JSON in `credentials/firebase-service-account.json`

## Running

### Start the worker:
```bash
python -m judge_worker.main
```

The worker will:
- Poll Firestore for pending submissions every 10 minutes (configurable)
- Claim and process submissions
- Write results back to Firestore
- Upload artifacts to Firebase Storage

### Logs

Logs are written to:
- `dsss_worker.log` (file)
- stdout (console)

## Scoring System

### Objective Scores (Automated)
- **Technical (0-20)**: From Lighthouse Performance score
- **Accessibility (0-10)**: From Lighthouse Accessibility with axe-core penalty

### Subjective Scores (Ollama)
- **Design (0-25)**: Visual appeal and design quality
- **UX (0-25)**: User experience and usability
- **Creativity (0-15)**: Originality and innovation
- **Content (0-5)**: Clarity and messaging
- **Bonus (0-15)**: Optional exceptional features

### Total Score
Sum of all categories, capped at 100 points.

## Firestore Data Model

### Collection: `entries`

Document structure:
```json
{
  "url": "https://example.com",
  "category": "Best Overall Website ⭐",
  "status": "pending|scoring|scored|error",
  "claimedBy": "worker-id",
  "claimedAt": "timestamp",
  "createdAt": "timestamp",
  "result": {
    "scores": {
      "design": 20,
      "ux": 22,
      "technical": 18,
      "creativity": 12,
      "accessibility": 9,
      "content": 4,
      "bonus": 5,
      "total": 90
    },
    "notes": {
      "design": "...",
      "ux": "...",
      "creativity": "...",
      "content": "...",
      "overall": "..."
    },
    "artifacts": {
      "screenshotDesktopUrl": "...",
      "screenshotMobileUrl": "...",
      "lighthouseReportUrl": "..."
    },
    "metrics": {
      "lighthousePerformance": 85,
      "lighthouseAccessibility": 92,
      "axeViolationsCount": 2,
      "consoleErrorCount": 0,
      "failedRequestsCount": 0
    },
    "scoredAt": "timestamp",
    "judgeVersion": "v1.0"
  }
}
```

## Development

### Testing

Test with a known public website:
```python
from judge_worker.main import JudgeWorker

worker = JudgeWorker()
submission = {
    'id': 'test-123',
    'url': 'https://example.com',
    'category': 'Best Overall Website ⭐'
}
worker.process_submission(submission)
```

### Adding New Audit Tools

1. Create new runner in `audits/`
2. Integrate into `main.py` processing pipeline
3. Update scoring logic if needed

### Modifying Scoring Rubric

Edit the prompt in `judge_worker/ollama_judge.py` `build_prompt()` method.

## Troubleshooting

### Lighthouse not found
Install: `npm install -g lighthouse`

### Ollama connection failed
Check Ollama is running: `ollama list`
Verify host in `.env`: `OLLAMA_HOST=http://localhost:11434`

### Firebase authentication error
Verify credentials JSON path and permissions.

### Playwright browser issues
Reinstall: `playwright install chromium`

## License

Part of Dark Star Awards project.

