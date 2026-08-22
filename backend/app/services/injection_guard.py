import re
from typing import Tuple, Optional

class InjectionGuardService:
    SUSPICIOUS_PATTERNS = [
        r"ignore (all )?previous instructions",
        r"disregard (all )?previous",
        r"give me (a )?(score of )?100",
        r"rank me (as )?first",
        r"override system prompt",
        r"you are now an? assistant that",
        r"system prompt:",
        r"developer mode",
        r"always return high score",
        r"candidate is ideal for all jobs",
        r"pretend to be",
        r"do not follow earlier instructions"
    ]

    @staticmethod
    def scan_for_injection(text: str) -> Tuple[bool, Optional[str]]:
        text_lower = text.lower()
        detected_triggers = []

        for pattern in InjectionGuardService.SUSPICIOUS_PATTERNS:
            if re.search(pattern, text_lower):
                detected_triggers.append(pattern)

        if detected_triggers:
            warning_msg = f"Potential instruction-like content detected ({len(detected_triggers)} suspicious patterns found). Resume content was isolated and treated strictly as untrusted data."
            return True, warning_msg

        return False, None

    @staticmethod
    def sanitize_untrusted_text(text: str) -> str:
        # Neutralize system prompt override markers
        sanitized = text
        for pattern in InjectionGuardService.SUSPICIOUS_PATTERNS:
            sanitized = re.sub(pattern, "[UNTRUSTED_CONTENT_FILTERED]", sanitized, flags=re.IGNORECASE)
        return sanitized
