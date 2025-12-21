"""Ollama integration for subjective scoring."""
import json
import logging
import requests
from typing import Dict, Any, Optional
from jsonschema import validate, ValidationError
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))
from config import Config

logger = logging.getLogger(__name__)

# JSON Schema for Ollama output
OLLAMA_OUTPUT_SCHEMA = {
    "type": "object",
    "required": ["scores", "notes"],
    "properties": {
        "judgeVersion": {"type": "string"},
        "scores": {
            "type": "object",
            "required": ["design", "ux", "creativity", "content"],
            "properties": {
                "design": {"type": "integer", "minimum": 0, "maximum": 25},
                "ux": {"type": "integer", "minimum": 0, "maximum": 25},
                "creativity": {"type": "integer", "minimum": 0, "maximum": 15},
                "content": {"type": "integer", "minimum": 0, "maximum": 5},
                "bonus": {"type": "integer", "minimum": 0, "maximum": 15}
            }
        },
        "notes": {
            "type": "object",
            "required": ["design", "ux", "creativity", "content", "overall"],
            "properties": {
                "design": {"type": "string"},
                "ux": {"type": "string"},
                "creativity": {"type": "string"},
                "content": {"type": "string"},
                "overall": {"type": "string"}
            }
        },
        "flags": {
            "type": "object",
            "properties": {
                "possibleTemplate": {"type": "boolean"},
                "majorBrokenUX": {"type": "boolean"},
                "accessibilityConcerns": {"type": "boolean"}
            }
        }
    }
}

class OllamaJudge:
    """Judge websites using Ollama for subjective scoring."""
    
    def __init__(self, host: str, model: str):
        """Initialize Ollama judge."""
        self.host = host.rstrip('/')
        self.model = model
        self.api_url = f"{self.host}/api/generate"
    
    def build_prompt(
        self,
        url: str,
        category: str,
        extracted_structure: Dict[str, Any],
        lighthouse_metrics: Dict[str, int],
        axe_summary: Dict[str, Any],
        console_error_count: int,
        failed_request_count: int
    ) -> str:
        """Build the scoring prompt for Ollama."""
        
        # Format extracted structure
        structure_text = f"""
Page Title: {extracted_structure.get('title', 'N/A')}
Meta Description: {extracted_structure.get('metaDescription', 'N/A')}
H1 Headings: {', '.join(extracted_structure.get('headings', {}).get('h1', []))}
H2 Headings: {', '.join(extracted_structure.get('headings', {}).get('h2', [])[:5])}
Navigation Links: {len(extracted_structure.get('navLinks', []))} links found
Visible Text Sample: {extracted_structure.get('visibleText', '')[:500]}...
"""
        
        # Format metrics
        metrics_text = f"""
Lighthouse Performance: {lighthouse_metrics.get('lighthousePerformance', 0)}/100
Lighthouse Accessibility: {lighthouse_metrics.get('lighthouseAccessibility', 0)}/100
Lighthouse SEO: {lighthouse_metrics.get('lighthouseSEO', 0)}/100
Lighthouse Best Practices: {lighthouse_metrics.get('lighthouseBestPractices', 0)}/100
Axe Violations: {axe_summary.get('axeViolationsCount', 0)}
Console Errors: {console_error_count}
Failed Requests: {failed_request_count}
"""
        
        prompt = f"""You are an expert web design judge for the Dark Star Awards competition. Evaluate the website at {url} entered in the "{category}" category.

## Website Structure:
{structure_text}

## Technical Metrics:
{metrics_text}

## Scoring Rubric:

**Design & Visual Appeal (0-25 points):**
- 0-5: Unreadable, chaotic, poor visual hierarchy
- 6-10: Basic design, functional but unpolished
- 11-18: Polished design with good visual hierarchy
- 19-25: Award-level design, exceptional visual appeal

**User Experience (UX) (0-25 points):**
- 0-5: Confusing, broken navigation, poor usability
- 6-10: Usable but with issues
- 11-18: Excellent UX, intuitive navigation
- 19-25: Exceptional UX, delightful interactions

**Creativity & Innovation (0-15 points):**
- 0-3: Generic, template-like
- 4-7: Some originality
- 8-12: Distinctive and creative
- 13-15: Unique and highly effective innovation

**Content & Messaging (0-5 points):**
- 0-1: Unclear purpose, poor copy
- 2-3: Clear purpose and messaging
- 4-5: Excellent clarity, strong CTAs

**Bonus Points (0-15, optional):**
- Award up to 15 bonus points for exceptional features (open-source, sustainability, documentation, etc.)

## Output Requirements:
You MUST output ONLY valid JSON. No markdown, no explanations outside the JSON.

Output this exact structure:
{{
  "judgeVersion": "v1.0",
  "scores": {{
    "design": <0-25>,
    "ux": <0-25>,
    "creativity": <0-15>,
    "content": <0-5>,
    "bonus": <0-15>
  }},
  "notes": {{
    "design": "<brief explanation>",
    "ux": "<brief explanation>",
    "creativity": "<brief explanation>",
    "content": "<brief explanation>",
    "overall": "<overall assessment>"
  }},
  "flags": {{
    "possibleTemplate": <true/false>,
    "majorBrokenUX": <true/false>,
    "accessibilityConcerns": <true/false>
  }}
}}

Evaluate the website and output the JSON now:"""
        
        return prompt
    
    def judge(
        self,
        url: str,
        category: str,
        extracted_structure: Dict[str, Any],
        lighthouse_metrics: Dict[str, int],
        axe_summary: Dict[str, Any],
        console_error_count: int,
        failed_request_count: int
    ) -> Optional[Dict[str, Any]]:
        """
        Judge website using Ollama.
        Returns parsed JSON response or None if failed.
        """
        prompt = self.build_prompt(
            url, category, extracted_structure,
            lighthouse_metrics, axe_summary,
            console_error_count, failed_request_count
        )
        
        try:
            logger.info(f"Calling Ollama model {self.model}")
            response = requests.post(
                self.api_url,
                json={
                    'model': self.model,
                    'prompt': prompt,
                    'stream': False,
                    'options': {
                        'temperature': 0.3,  # Lower temperature for more consistent scoring
                        'top_p': 0.9
                    }
                },
                timeout=120
            )
            response.raise_for_status()
            
            result = response.json()
            response_text = result.get('response', '').strip()
            
            # Try to extract JSON from response
            json_text = self._extract_json(response_text)
            
            if not json_text:
                logger.warning("No JSON found in Ollama response, attempting retry")
                return self._retry_with_fix_prompt(prompt)
            
            # Parse and validate
            parsed = json.loads(json_text)
            validate(instance=parsed, schema=OLLAMA_OUTPUT_SCHEMA)
            
            logger.info(f"Ollama judgment completed: {parsed.get('scores')}")
            return parsed
        
        except ValidationError as e:
            logger.error(f"JSON validation error: {e}")
            return self._retry_with_fix_prompt(prompt)
        except json.JSONDecodeError as e:
            logger.error(f"JSON decode error: {e}")
            return self._retry_with_fix_prompt(prompt)
        except Exception as e:
            logger.error(f"Error calling Ollama: {e}")
            return None
    
    def _extract_json(self, text: str) -> Optional[str]:
        """Extract JSON from text response."""
        # Try to find JSON object
        start = text.find('{')
        end = text.rfind('}') + 1
        
        if start >= 0 and end > start:
            return text[start:end]
        return None
    
    def _retry_with_fix_prompt(self, original_prompt: str) -> Optional[Dict[str, Any]]:
        """Retry with a prompt asking to fix JSON."""
        fix_prompt = f"""{original_prompt}

The previous response was not valid JSON. Please output ONLY the JSON object, no other text:"""
        
        try:
            response = requests.post(
                self.api_url,
                json={
                    'model': self.model,
                    'prompt': fix_prompt,
                    'stream': False
                },
                timeout=120
            )
            response.raise_for_status()
            
            result = response.json()
            response_text = result.get('response', '').strip()
            json_text = self._extract_json(response_text)
            
            if json_text:
                parsed = json.loads(json_text)
                validate(instance=parsed, schema=OLLAMA_OUTPUT_SCHEMA)
                return parsed
        
        except Exception as e:
            logger.error(f"Retry failed: {e}")
        
        return None

