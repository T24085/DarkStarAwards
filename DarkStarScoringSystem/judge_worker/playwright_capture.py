"""Playwright-based website evidence capture."""
import json
import logging
from pathlib import Path
from typing import Dict, Any, List
from playwright.sync_api import sync_playwright, Page, Browser
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))
from config import Config

logger = logging.getLogger(__name__)

class PlaywrightCapture:
    """Capture website evidence using Playwright."""
    
    def __init__(self, artifacts_dir: Path):
        """Initialize capture with artifacts directory."""
        self.artifacts_dir = artifacts_dir
        self.playwright = None
        self.browser = None
    
    def __enter__(self):
        """Context manager entry."""
        self.playwright = sync_playwright().start()
        self.browser = self.playwright.chromium.launch(
            headless=True,
            args=['--no-sandbox', '--disable-gpu']
        )
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        if self.browser:
            self.browser.close()
        if self.playwright:
            self.playwright.stop()
    
    def capture(self, url: str, submission_id: str) -> Dict[str, Any]:
        """
        Capture evidence from website.
        Returns dict with screenshots, extracted data, console logs, network errors.
        """
        context = self.browser.new_context(
            viewport={'width': 1440, 'height': 900},
            user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        )
        page = context.new_page()
        
        evidence = {
            'url': url,
            'submission_id': submission_id,
            'screenshots': {},
            'extracted': {},
            'console': [],
            'network_errors': [],
            'failed_requests': []
        }
        
        try:
            # Set up console and network listeners
            console_logs = []
            network_errors = []
            failed_requests = []
            
            def handle_console(msg):
                console_logs.append({
                    'type': msg.type,
                    'text': msg.text,
                    'location': str(msg.location) if msg.location else None
                })
            
            def handle_response(response):
                if response.status >= 400:
                    failed_requests.append({
                        'url': response.url,
                        'status': response.status,
                        'method': response.request.method
                    })
            
            page.on('console', handle_console)
            page.on('response', handle_response)
            
            # Navigate with timeout
            logger.info(f"Navigating to {url}")
            page.goto(
                url,
                wait_until='networkidle',
                timeout=Config.NAVIGATION_TIMEOUT_MS
            )
            
            # Wait a bit for dynamic content
            page.wait_for_timeout(2000)
            
            # Scroll to load lazy content
            page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
            page.wait_for_timeout(1000)
            page.evaluate("window.scrollTo(0, 0)")
            page.wait_for_timeout(500)
            
            # Capture desktop screenshot
            desktop_path = self.artifacts_dir / f"{submission_id}_desktop.png"
            page.screenshot(path=str(desktop_path), full_page=True)
            evidence['screenshots']['desktop'] = str(desktop_path)
            
            # Extract page structure
            extracted = page.evaluate("""
                () => {
                    const data = {
                        title: document.title,
                        metaDescription: document.querySelector('meta[name="description"]')?.content || '',
                        headings: {
                            h1: Array.from(document.querySelectorAll('h1')).map(h => h.textContent.trim()),
                            h2: Array.from(document.querySelectorAll('h2')).map(h => h.textContent.trim()),
                            h3: Array.from(document.querySelectorAll('h3')).map(h => h.textContent.trim())
                        },
                        navLinks: Array.from(document.querySelectorAll('nav a, header a')).map(a => ({
                            text: a.textContent.trim(),
                            href: a.href
                        })).slice(0, 20),
                        visibleText: document.body.innerText.substring(0, 2000)
                    };
                    return data;
                }
            """)
            evidence['extracted'] = extracted
            
            # Switch to mobile viewport
            mobile_context = self.browser.new_context(
                viewport={'width': 390, 'height': 844},  # iPhone 12 size
                user_agent='Mozilla/5.0 (iPhone; CPU iPhone OS 14_0 like Mac OS X) AppleWebKit/605.1.15'
            )
            mobile_page = mobile_context.new_page()
            mobile_page.goto(url, wait_until='networkidle', timeout=Config.NAVIGATION_TIMEOUT_MS)
            mobile_page.wait_for_timeout(2000)
            
            mobile_path = self.artifacts_dir / f"{submission_id}_mobile.png"
            mobile_page.screenshot(path=str(mobile_path), full_page=True)
            evidence['screenshots']['mobile'] = str(mobile_path)
            
            mobile_context.close()
            
            # Collect console and network data
            evidence['console'] = console_logs
            evidence['network_errors'] = network_errors
            evidence['failed_requests'] = failed_requests
            
            # Count console errors
            console_error_count = len([log for log in console_logs if log['type'] == 'error'])
            evidence['console_error_count'] = console_error_count
            evidence['failed_request_count'] = len(failed_requests)
            
            # Save extracted structure JSON
            structure_path = self.artifacts_dir / f"{submission_id}_structure.json"
            with open(structure_path, 'w', encoding='utf-8') as f:
                json.dump(extracted, f, indent=2, ensure_ascii=False)
            evidence['structure_json'] = str(structure_path)
            
            logger.info(f"Capture completed for {url}")
            return evidence
        
        except Exception as e:
            logger.error(f"Error capturing {url}: {e}")
            raise
        
        finally:
            context.close()

