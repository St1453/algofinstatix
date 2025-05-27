"""Audit logging for security and compliance events.

This module provides structured audit logging for security-sensitive operations
and compliance requirements. All logs are formatted as JSON for better parsing
and analysis.
"""

import json
import logging
import os
from datetime import datetime, timezone
from logging.handlers import RotatingFileHandler
from typing import Any, Dict, Optional, Union

from src.core.config import get_settings
from src.core.formatter import StructuredFormatter


class JSONFormatter(logging.Formatter):
    """Custom formatter that outputs JSON strings."""

    def format(self, record: logging.LogRecord) -> str:
        """Format log record as JSON."""
        log_record = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            **getattr(record, "context", {}),
        }
        return json.dumps(log_record, default=str)


class AuditLogger:
    """Centralized audit logging service with JSON output."""

    def __init__(self, settings):
        self.settings = settings or get_settings()
        self._setup_logger()

        # Define sensitive fields that should be redacted from logs
        self._sensitive_fields = {
            "password",
            "token",
            "secret",
            "api_key",
            "access_key",
            "private_key",
            "credit_card",
            "ssn",
            "social_security",
        }

    def _setup_logger(self) -> None:
        """Configure the audit logger with file handler and JSON formatter."""
        self._ensure_log_directories_exist()
        self.logger = logging.getLogger("audit")
        self.logger.setLevel(self.settings.LOG_LEVEL)

        # Clear any existing handlers to avoid duplicate logs
        if self.logger.handlers:
            self.logger.handlers.clear()

        # Ensure log directory exists
        log_dir = os.path.dirname(self.settings.LOG_AUDIT)
        if log_dir and not os.path.exists(log_dir):
            os.makedirs(log_dir, exist_ok=True)

        # Add file handler with rotation
        file_handler = RotatingFileHandler(
            filename=self.settings.LOG_AUDIT,
            maxBytes=10 * 1024 * 1024,  # 10MB
            backupCount=5,
            encoding="utf-8",
        )
        file_handler.setFormatter(JSONFormatter())
        self.logger.addHandler(file_handler)

    def _ensure_log_directories_exist(self) -> None:
        """Ensure all log directories exist."""
        log_dirs = [
            os.path.dirname(self.settings.LOG_AUDIT),
        ]
        for log_dir in log_dirs:
            if log_dir and not os.path.exists(log_dir):
                os.makedirs(log_dir, exist_ok=True)

    def _create_logger(self, name: str, log_file: str, level: int) -> logging.Logger:
        """Create and configure a logger with file handler."""
        logger = logging.getLogger(name)
        logger.setLevel(level)

        # Don't add handlers if they already exist
        if logger.handlers:
            return logger

        formatter = StructuredFormatter()

        # File handler
        file_handler = RotatingFileHandler(
            filename=log_file,
            maxBytes=10 * 1024 * 1024,  # 10MB
            backupCount=5,
            encoding="utf-8",
        )
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)

        # Console handler for development
        if self.settings.DEBUG:
            console_handler = logging.StreamHandler()
            console_handler.setFormatter(formatter)
            logger.addHandler(console_handler)

        return logger

    def _redact_sensitive_data(self, data: Any) -> Any:
        """Recursively redact sensitive data from dictionaries and lists.

        Args:
            data: The data to process (dict, list, or other types).

        Returns:
            The processed data with sensitive values redacted.
        """
        if isinstance(data, dict):
            return {
                k: "[REDACTED]"
                if any(s in k.lower() for s in self._sensitive_fields)
                else self._redact_sensitive_data(v)
                for k, v in data.items()
            }
        elif isinstance(data, list):
            return [self._redact_sensitive_data(item) for item in data]
        return data

    def _log_event(
        self, event_type: str, category: str, message: str, **context: Any
    ) -> None:
        """Internal method to log an event with structured context."""
        # Redact any sensitive data from context
        safe_context = self._redact_sensitive_data(context)

        log_context = {
            "event_type": event_type,
            "category": category,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            **safe_context,
        }
        self.logger.info(message, extra={"context": log_context})

    def log_security_event(
        self,
        event_type: str,
        user_id: Optional[Union[str, int]] = None,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
        **details: Any,
    ) -> None:
        """Log a security-related event.

        Args:
            event_type: Type of security event (e.g., 'login_attempt',
                'permission_denied').
            user_id: Optional ID of the user associated with the event.
            ip_address: Optional IP address of the client.
            user_agent: Optional user agent string of the client.
            **details: Additional details about the event.
        """
        context: Dict[str, Any] = {"category": "security", **details}

        if user_id is not None:
            context["user_id"] = str(user_id)
        if ip_address is not None:
            context["ip_address"] = ip_address
        if user_agent is not None:
            context["user_agent"] = user_agent

        self._log_event(
            event_type=event_type,
            category="security",
            message=f"Security event: {event_type}",
            **context,
        )

    def log_permission_change(
        self,
        permission: str,
        target_user_id: Union[str, int],
        changed_by: Optional[Union[str, int]] = None,
        old_value: Any = None,
        new_value: Any = None,
        **details: Any,
    ) -> None:
        """Log a permission change event.

        Args:
            permission: The permission that was changed.
            target_user_id: ID of the user whose permissions were changed.
            changed_by: Optional ID of the user who made the change.
            old_value: The previous value of the permission.
            new_value: The new value of the permission.
            **details: Additional details about the change.
        """
        context: Dict[str, Any] = {
            "permission": permission,
            "target_user_id": str(target_user_id),
            "old_value": old_value,
            "new_value": new_value,
            **details,
        }

        if changed_by is not None:
            context["changed_by"] = str(changed_by)

        self._log_event(
            event_type="permission_change",
            category="security",
            message=f"Permission changed: {permission} for user {target_user_id}",
            **context,
        )

    def log_data_access(
        self,
        resource_type: str,
        resource_id: Optional[Union[str, int]] = None,
        user_id: Optional[Union[str, int]] = None,
        action: str = "access",
        **details: Any,
    ) -> None:
        """Log data access events for sensitive data.

        Args:
            resource_type: Type of resource being accessed.
            resource_id: Optional ID of the specific resource.
            user_id: Optional ID of the user performing the action.
            action: Type of access (e.g., 'read', 'export', 'delete').
            **details: Additional details about the access.
        """
        context: Dict[str, Any] = {
            "resource_type": resource_type,
            "action": action,
            **details,
        }

        if resource_id is not None:
            context["resource_id"] = str(resource_id)
        if user_id is not None:
            context["user_id"] = str(user_id)

        self._log_event(
            event_type=f"data_{action}",
            category="data_access",
            message=f"Data {action}: {resource_type}",
            **context,
        )

    def log_system_event(
        self, component: str, event: str, status: str = "info", **details: Any
    ) -> None:
        """Log system-level events.

        Args:
            component: The system component generating the event.
            event: Description of the event.
            status: Event status (e.g., 'info', 'warning', 'error', 'critical').
            **details: Additional details about the event.
        """
        log_level = getattr(logging, status.upper(), logging.INFO)
        context: Dict[str, Any] = {
            "component": component,
            "event": event,
            "status": status,
            **details,
        }

        # Use the underlying logger directly to support different log levels
        log_context = {
            "event_type": "system_event",
            "category": "system",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            **context,
        }
        self.logger.log(
            log_level,
            f"System event: {component} - {event}",
            extra={"context": log_context},
        )


_audit_logger = AuditLogger(get_settings())


def get_audit_logger() -> AuditLogger:
    """Get the global audit logger instance."""
    return _audit_logger
