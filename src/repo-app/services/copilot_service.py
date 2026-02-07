"""
GitHub Copilot SDK integration service.

Author: Automated Software Engineering Team
Date: February 2026
"""

import re
from typing import List, Optional

from logger import get_logger

# GitHub Copilot SDK imports
try:
    from copilot import CopilotClient
    from copilot.types import MessageOptions
    COPILOT_SDK_AVAILABLE = True
except ImportError:
    COPILOT_SDK_AVAILABLE = False
    CopilotClient = None
    MessageOptions = None


class CopilotService:
    """Service for GitHub Copilot SDK integration"""
    
    def __init__(self, use_copilot: bool = True):
        """
        Initialize Copilot service.
        
        Args:
            use_copilot: Whether to enable Copilot SDK
        """
        self.use_copilot = use_copilot and COPILOT_SDK_AVAILABLE
        self.copilot_client = None
        self.copilot_session = None
        self._copilot_started = False
    
    def is_available(self) -> bool:
        """Check if Copilot SDK is available and initialized"""
        return self.use_copilot and self._copilot_started
    
    async def start(self):
        """Initialize Copilot client"""
        logger = get_logger()
        if self.use_copilot and not self._copilot_started:
            try:
                if CopilotClient is None:
                    logger.warning("Copilot SDK not available")
                    self.use_copilot = False
                    return
                
                self.copilot_client = CopilotClient()
                await self.copilot_client.start()
                self._copilot_started = True
                logger.info("   🤖 GitHub Copilot SDK initialized")
            except Exception as e:
                logger.warning(f"Copilot SDK initialization failed: {e}")
                self.use_copilot = False
                self.copilot_client = None
    
    async def cleanup(self):
        """Clean up Copilot client"""
        logger = get_logger()
        if self.copilot_client and self._copilot_started:
            try:
                if self.copilot_session:
                    await self.copilot_session.destroy()
                    self.copilot_session = None
                await self.copilot_client.stop()
                self._copilot_started = False
            except Exception as e:
                logger.warning(f"Copilot cleanup error: {e}")
    
    async def classify_tests(self, prompt: str) -> List[dict]:
        """
        Classify test files using Copilot SDK.
        
        Args:
            prompt: Classification prompt with file information
            
        Returns:
            List of classifications [{"file": "path", "type": "unit|e2e|..."}]
        """
        if not self.copilot_client or not self._copilot_started:
            return []
        
        try:
            # Create session if needed
            if not self.copilot_session:
                self.copilot_session = await self.copilot_client.create_session()
            
            # Send request
            message_options: MessageOptions = {"prompt": prompt}
            response = await self.copilot_session.send_and_wait(message_options, timeout=30.0)
            
            # Parse response
            classifications = self._parse_classifications(response)
            return classifications
            
        except Exception as e:
            logger = get_logger()
            logger.debug(f"Copilot classification request failed: {e}")
            return []
    
    def _parse_classifications(self, response) -> List[dict]:
        """
        Parse test classifications from Copilot response.
        
        Args:
            response: Copilot response object
            
        Returns:
            List of classifications
        """
        classifications = []
        
        if not response:
            return classifications
        
        if not hasattr(response, 'data') or not hasattr(response.data, 'content'):
            return classifications
        
        content = response.data.content
        if not content:
            return classifications
        
        # Extract classifications from response
        for line in content.split('\n'):
            # Look for patterns like "file.py: unit" or "file.py -> e2e"
            match = re.search(r'([^:]+):\s*(unit|integration|e2e|performance|smoke)', line, re.IGNORECASE)
            if match:
                classifications.append({
                    "file": match.group(1).strip(),
                    "type": match.group(2).lower()
                })
        
        return classifications
