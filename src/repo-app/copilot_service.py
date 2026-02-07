"""
GitHub Copilot SDK integration service.

Author: Automated Software Engineering Team
Date: February 2026
"""

import json
import re
from pathlib import Path
from typing import List, Dict, Optional

from .constants import COPILOT_BATCH_SIZE, COPILOT_TIMEOUT, FILE_PREVIEW_LENGTH


# Optional Copilot SDK import
try:
    from copilot import CopilotClient
    from copilot.types import MessageOptions
    COPILOT_SDK_AVAILABLE = True
except ImportError:
    COPILOT_SDK_AVAILABLE = False
    CopilotClient = None
    MessageOptions = None


class CopilotTestAnalyzer:
    """
    GitHub Copilot SDK service for intelligent test classification.
    
    Encapsulates all Copilot-specific logic in a single class.
    """
    
    def __init__(self, enabled: bool = True):
        """
        Initialize Copilot analyzer.
        
        Args:
            enabled: Enable Copilot SDK if available
        """
        self.enabled = enabled and COPILOT_SDK_AVAILABLE
        self.client: Optional[CopilotClient] = None
        self.session = None
        self._initialized = False
    
    def is_available(self) -> bool:
        """Check if Copilot is available and initialized"""
        return self.enabled and self._initialized
    
    async def initialize(self):
        """Initialize Copilot client (async)"""
        if not self.enabled or self._initialized:
            return
        
        try:
            self.client = CopilotClient()
            await self.client.start()
            self._initialized = True
            print("   🤖 GitHub Copilot SDK initialized")
        except Exception as e:
            print(f"   ⚠️  Copilot SDK initialization failed: {e}")
            self.enabled = False
            self.client = None
    
    async def cleanup(self):
        """Cleanup Copilot resources"""
        if not self.client or not self._initialized:
            return
        
        try:
            if self.session:
                await self.session.destroy()
                self.session = None
            await self.client.stop()
            self._initialized = False
        except Exception as e:
            print(f"   ⚠️  Copilot cleanup error: {e}")
    
    async def classify_tests(self, test_files: List[Path]) -> List[Dict[str, str | int]]:
        """
        Classify test files using Copilot SDK.
        
        Args:
            test_files: List of test file paths
            
        Returns:
            List of classification dictionaries with 'file', 'type', and 'count' keys
        """
        if not self.is_available():
            return []
        
        all_classifications = []
        
        try:
            # Create session for this analysis
            self.session = await self.client.create_session()
            
            # Process files in batches
            for i in range(0, len(test_files), COPILOT_BATCH_SIZE):
                batch = test_files[i:i + COPILOT_BATCH_SIZE]
                batch_results = await self._classify_batch(batch)
                all_classifications.extend(batch_results)
            
            # Cleanup session
            if self.session:
                await self.session.destroy()
                self.session = None
        
        except Exception as e:
            print(f"   ⚠️  Copilot analysis failed: {e}")
            if self.session:
                await self.session.destroy()
                self.session = None
        
        return all_classifications
    
    async def _classify_batch(self, test_files: List[Path]) -> List[Dict[str, str | int]]:
        """Classify a batch of test files"""
        if not self.session:
            return []
        
        # Prepare file information
        file_info = self._prepare_file_info(test_files)
        if not file_info:
            return []
        
        # Build prompt
        prompt = self._build_classification_prompt(file_info)
        
        # Send to Copilot
        try:
            response = await self._send_to_copilot(prompt)
            return self._parse_copilot_response(response)
        except Exception as e:
            print(f"   ⚠️  Batch classification failed: {e}")
            return []
    
    def _prepare_file_info(self, test_files: List[Path]) -> List[Dict[str, str]]:
        """Prepare file information for Copilot analysis"""
        file_info = []
        
        for test_file in test_files:
            try:
                content = test_file.read_text()[:FILE_PREVIEW_LENGTH]
                file_info.append({
                    "path": str(test_file),
                    "name": test_file.name,
                    "preview": content
                })
            except Exception:
                continue
        
        return file_info
    
    def _build_classification_prompt(self, file_info: List[Dict[str, str]]) -> str:
        """Build prompt for Copilot test classification"""
        return f"""Analyze these test files and classify each as one of: unit, integration, e2e, performance, or smoke test.

For each file, respond with the format: "filename: type"

Files to analyze:
{json.dumps(file_info, indent=2)}

Classifications:"""
    
    async def _send_to_copilot(self, prompt: str) -> Optional[any]:
        """Send prompt to Copilot and wait for response"""
        message_options: MessageOptions = {
            "prompt": prompt,
        }
        return await self.session.send_and_wait(message_options, timeout=COPILOT_TIMEOUT)
    
    def _parse_copilot_response(self, response) -> List[Dict[str, str | int]]:
        """Parse Copilot response into classification results"""
        classifications = []
        
        if not response or not hasattr(response, 'data'):
            return classifications
        
        if not hasattr(response.data, 'content'):
            return classifications
        
        content = response.data.content
        if not content:
            return classifications
        
        # Extract classifications from response
        for line in content.split('\n'):
            match = re.search(
                r'([^:]+):\s*(unit|integration|e2e|performance|smoke)',
                line,
                re.IGNORECASE
            )
            if match:
                classifications.append({
                    "file": match.group(1).strip(),
                    "type": match.group(2).lower(),
                    "count": 1  # Could be improved with actual test counting
                })
        
        return classifications
