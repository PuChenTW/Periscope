"""
Prompt validation patterns for security threat detection.

This module contains regex patterns used to detect various types of prompt injection
and security threats. Patterns are organized by threat category for easy maintenance.

Pattern Structure:
    Each pattern is a tuple of (regex_pattern, error_message)
    - regex_pattern: Compiled or string regex to match against user input
    - error_message: User-friendly error message when pattern matches
"""

from typing import Final

# Injection pattern categories
COMMAND_INJECTION_PATTERNS: Final[list[tuple[str, str]]] = [
    (
        r"\bignore\s+(previous|prior|all|above)\s+(instructions|commands|rules)",
        "Command injection attempt detected",
    ),
    (
        r"\bforget\s+(everything|all|previous|instructions)",
        "Memory manipulation attempt detected",
    ),
    (
        r"\boverride\s+(settings|rules|instructions|safety)",
        "Override attempt detected",
    ),
    (
        r"\bsystem\s*:",
        "System command attempt detected",
    ),
    (
        r"\brole\s*:",
        "Role manipulation attempt detected",
    ),
]

ROLE_HIJACKING_PATTERNS: Final[list[tuple[str, str]]] = [
    (
        r"\byou\s+are\s+now\s+",
        "Role hijacking attempt detected",
    ),
    (
        r"\bact\s+as\s+(a|an)\s+",
        "Role playing attempt detected",
    ),
    (
        r"\bpretend\s+to\s+be\s+",
        "Identity manipulation attempt detected",
    ),
    (
        r"\byou\s+must\s+(ignore|forget|override)",
        "Instruction override attempt detected",
    ),
]

DATA_EXTRACTION_PATTERNS: Final[list[tuple[str, str]]] = [
    (
        r"\b(print|reveal|show\s+me|tell\s+me\s+about)\s+(your|the)\s+(prompt|instructions|system)",
        "Data extraction attempt detected",
    ),
    (
        r"\bwhat\s+(are|were)\s+your\s+(instructions|rules)",
        "System information query detected",
    ),
]

CODE_EXECUTION_PATTERNS: Final[list[tuple[str, str]]] = [
    (
        r"\bexecute\s+",
        "Code execution attempt detected",
    ),
    (
        r"\brun\s+(command|code|script)",
        "Script execution attempt detected",
    ),
    (
        r"\beval\s*\(",
        "Code evaluation attempt detected",
    ),
]

# Combined injection patterns for convenience
INJECTION_PATTERNS: Final[list[tuple[str, str]]] = [
    *COMMAND_INJECTION_PATTERNS,
    *ROLE_HIJACKING_PATTERNS,
    *DATA_EXTRACTION_PATTERNS,
    *CODE_EXECUTION_PATTERNS,
]

# Blocklist patterns for off-topic requests
BLOCKLIST_PATTERNS: Final[list[tuple[str, str]]] = [
    (
        r"\b(write|generate|create)\s+(code|script|program)",
        "Code generation request detected",
    ),
    (
        r"\btranslate\s+(this|to|into)",
        "Translation request detected",
    ),
    (
        r"\bwrite\s+a\s+(poem|story|song|joke)",
        "Creative writing request detected",
    ),
    (
        r"\bcalculate\s+",
        "Calculation request detected",
    ),
    (
        r"\bfile\s+(system|path|directory)",
        "File system operation detected",
    ),
    (
        r"\bpasswords?\b",
        "Credential-related term detected",
    ),
    (
        r"\bcredentials?\b",
        "Credential-related term detected",
    ),
    (
        r"\b(api|client|access)\s*[-_]?keys?\b",
        "Credential-related term detected",
    ),
    (
        r"\b(access|refresh)\s*[-_]?tokens?\b",
        "Credential-related term detected",
    ),
    (
        r"\bsecret\s+(key|token|password|phrase)\b",
        "Credential-related term detected",
    ),
]


def get_all_security_patterns() -> list[tuple[str, str]]:
    """
    Get all security patterns combined (injection + blocklist).

    Returns:
        List of (pattern, error_message) tuples for validation
    """
    return [*INJECTION_PATTERNS, *BLOCKLIST_PATTERNS]
