"""
Guardrails Service - Content filtering and safety
"""

from typing import Optional
import structlog
import re

from core.config import settings

logger = structlog.get_logger()


class GuardrailsService:
    """Service for applying guardrails to inputs and outputs"""
    
    def __init__(self):
        self.pii_detection_enabled = settings.ENABLE_PII_DETECTION
        self.content_filter_enabled = settings.ENABLE_CONTENT_FILTER
        self.blocked_topics = settings.blocked_topics_list
        self.redaction_mode = settings.PII_REDACTION_MODE
        
        # PII patterns
        self.pii_patterns = {
            "ssn": r"\b\d{3}-\d{2}-\d{4}\b",
            "email": r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b",
            "phone": r"\b(?:\+?1[-.]?)?\(?([0-9]{3})\)?[-.]?([0-9]{3})[-.]?([0-9]{4})\b",
            "credit_card": r"\b\d{4}[-\s]?\d{4}[-\s]?\d{4}[-\s]?\d{4}\b",
        }
        
        logger.info(
            "guardrails_initialized",
            pii_detection=self.pii_detection_enabled,
            content_filter=self.content_filter_enabled,
        )
    
    async def validate_input(self, text: str) -> str:
        """
        Validate and sanitize user input
        
        Args:
            text: User input text
        
        Returns:
            Sanitized text
        """
        if not settings.ENABLE_GUARDRAILS:
            return text
        
        result = text
        
        # Check for blocked topics
        if self.content_filter_enabled:
            for topic in self.blocked_topics:
                if topic.lower() in result.lower():
                    logger.warning("blocked_topic_detected", topic=topic)
                    # Replace with warning message
                    return f"[Content filtered: This query contains restricted topic '{topic}']"
        
        # PII detection and redaction
        if self.pii_detection_enabled:
            result = self._redact_pii(result)
        
        # Length check
        if len(result) > 10000:
            logger.warning("input_too_long", length=len(result))
            result = result[:10000] + "... [truncated]"
        
        return result
    
    async def validate_output(self, text: str) -> str:
        """
        Validate and sanitize LLM output
        
        Args:
            text: LLM output text
        
        Returns:
            Sanitized text
        """
        if not settings.ENABLE_GUARDRAILS:
            return text
        
        result = text
        
        # PII detection in output
        if self.pii_detection_enabled:
            result = self._redact_pii(result)
        
        # Check for potential jailbreak attempts in output
        jailbreak_indicators = [
            "ignore previous instructions",
            "disregard",
            "system prompt",
            "you are now",
        ]
        
        for indicator in jailbreak_indicators:
            if indicator.lower() in result.lower():
                logger.warning("potential_jailbreak_in_output", indicator=indicator)
                # Don't modify output, just log for review
        
        return result
    
    def _redact_pii(self, text: str) -> str:
        """Redact PII from text"""
        result = text
        pii_found = False
        
        for pii_type, pattern in self.pii_patterns.items():
            matches = re.finditer(pattern, result, re.IGNORECASE)
            for match in matches:
                pii_found = True
                original = match.group(0)
                
                if self.redaction_mode == "mask":
                    # Mask with asterisks
                    redacted = "*" * len(original)
                elif self.redaction_mode == "remove":
                    # Remove completely
                    redacted = ""
                else:  # alert
                    # Replace with alert message
                    redacted = f"[{pii_type.upper()}_REDACTED]"
                
                result = result.replace(original, redacted)
                logger.info("pii_redacted", pii_type=pii_type, mode=self.redaction_mode)
        
        if pii_found and self.redaction_mode == "alert":
            result = "[⚠️ PII Detected and Redacted]\n\n" + result
        
        return result
    
    async def check_content_safety(self, text: str) -> dict:
        """
        Check content for safety issues
        
        Returns:
            Dict with safety assessment
        """
        issues = []
        
        # Check for harmful content indicators
        harmful_indicators = [
            "violence",
            "illegal",
            "classified",
            "confidential",
        ]
        
        for indicator in harmful_indicators:
            if indicator.lower() in text.lower():
                issues.append({
                    "type": "harmful_content",
                    "indicator": indicator,
                })
        
        # Check for PII
        for pii_type, pattern in self.pii_patterns.items():
            if re.search(pattern, text, re.IGNORECASE):
                issues.append({
                    "type": "pii",
                    "pii_type": pii_type,
                })
        
        return {
            "safe": len(issues) == 0,
            "issues": issues,
            "risk_level": "high" if len(issues) > 0 else "low",
        }
