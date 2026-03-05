"""
Security module for LM Studio Terminal Bridge.

Handles command filtering, sandbox rules, and security validation.
"""

import re
from typing import List, Tuple, Optional
from logger import get_logger, BridgeLogger

from config import (
    BLOCKED_COMMANDS,
    PROTECTED_PATHS,
    ALLOWED_COMMANDS
)


class SecurityValidator:
    """
    Validates PowerShell commands for security compliance.

    Implements a whitelist/blacklist system to protect the system
    from dangerous commands while allowing legitimate operations.
    """

    def __init__(self):
        """Initialize the security validator."""
        self.logger = get_logger("bridge.security")
        self._blocked_patterns = self._compile_blocked_patterns()
        self._allowed_prefixes = self._compile_allowed_prefixes()

    def _compile_blocked_patterns(self) -> List[re.Pattern]:
        """
        Compile regex patterns for blocked commands.

        Returns:
            List of compiled regex patterns
        """
        patterns = []
        for cmd in BLOCKED_COMMANDS:
            try:
                # Case-insensitive pattern matching
                pattern = re.compile(re.escape(cmd), re.IGNORECASE)
                patterns.append(pattern)
            except re.error as e:
                self.logger.warning(f"Failed to compile pattern for '{cmd}': {e}")
        return patterns

    def _compile_allowed_prefixes(self) -> List[str]:
        """
        Compile list of allowed command prefixes.

        Returns:
            List of lowercase command prefixes
        """
        return [prefix.lower() for prefix in ALLOWED_COMMANDS]

    def validate_command(self, command: str) -> Tuple[bool, Optional[str]]:
        """
        Validate a PowerShell command against security rules.

        Args:
            command: The PowerShell command to validate

        Returns:
            Tuple of (is_valid, error_message)
            - is_valid: True if command is allowed, False otherwise
            - error_message: Description of why command was blocked, or None
        """
        if not command or not command.strip():
            return False, "Empty command"

        command_lower = command.lower().strip()

        # Check for explicitly blocked commands
        for pattern in self._blocked_patterns:
            if pattern.search(command):
                blocked_cmd = pattern.pattern.replace('\\\\', '\\').replace('\\ ', ' ')
                BridgeLogger.log_security_event(
                    "blocked",
                    f"Command contains blocked pattern: {blocked_cmd}"
                )
                return False, f"Command contains blocked pattern: {blocked_cmd}"

        # Check for protected paths
        for protected_path in PROTECTED_PATHS:
            if protected_path.lower() in command_lower:
                BridgeLogger.log_security_event(
                    "blocked",
                    f"Command targets protected path: {protected_path}"
                )
                return False, f"Cannot target protected path: {protected_path}"

        # Check for suspicious patterns
        suspicious_patterns = [
            r'format\s+[a-z]:',           # format disk (drive letter)
            r'diskpart',                   # disk partition tool
            r'bootcfg',                    # boot configuration
            r'bcdedit',                    # boot editor
            r'reg\s+delete',              # registry delete
            r'sc\s+delete',               # service delete
            r'net\s+share\s+/delete',     # share deletion
        ]

        for pattern in suspicious_patterns:
            if re.search(pattern, command_lower):
                BridgeLogger.log_security_event(
                    "blocked",
                    f"Command contains suspicious pattern: {pattern}"
                )
                return False, f"Command contains suspicious pattern"

        # Check if command starts with allowed prefix
        has_allowed_prefix = any(
            command_lower.startswith(prefix)
            for prefix in self._allowed_prefixes
        )

        # Allow common informational commands even if not explicitly listed
        informational_patterns = [
            r'^echo\s',
            r'^pwd$',
            r'^get-',
            r'^test-',
            r'^select-',
            r'^where-',
            r'^foreach',
            r'^if\s',
            r'^\$',  # Variables
        ]

        is_informational = any(
            re.match(pattern, command_lower)
            for pattern in informational_patterns
        )

        if not (has_allowed_prefix or is_informational):
            BridgeLogger.log_security_event(
                "warning",
                f"Command does not match known safe patterns: {command[:50]}"
            )

        BridgeLogger.log_security_event("allowed", f"Command validated: {command[:50]}")
        return True, None

    def is_safe_path(self, path: str) -> bool:
        """
        Check if a file path is safe to access.

        Args:
            path: The file path to check

        Returns:
            True if path is safe, False otherwise
        """
        path_lower = path.lower()

        for protected_path in PROTECTED_PATHS:
            if protected_path.lower() in path_lower:
                return False

        return True

    def sanitize_command(self, command: str) -> str:
        """
        Sanitize a command by removing potentially dangerous elements.

        Note: This is a basic sanitization. Security primarily relies on
        validate_command() for blocking dangerous commands.

        Args:
            command: The command to sanitize

        Returns:
            Sanitized command string
        """
        # Remove multiple consecutive spaces
        command = re.sub(r'\s+', ' ', command)
        # Trim whitespace
        command = command.strip()
        return command


class SecurityError(Exception):
    """Exception raised when a security violation is detected."""

    def __init__(self, message: str):
        """
        Initialize the security error.

        Args:
            message: Description of the security violation
        """
        super().__init__(f"Security violation: {message}")
        self.message = message
