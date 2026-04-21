"""
Error recovery module for Gold tier autonomous AI employee.

Provides comprehensive error handling with:
- Error classification (transient vs permanent)
- Exponential backoff retry logic
- Operation queuing for failed operations
- Alert file creation for auth failures
"""

import os
import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Callable, Any, Optional, Dict, List
from enum import Enum
from tenacity import (
    retry,
    stop_after_attempt,
    wait_exponential,
    retry_if_exception_type,
    RetryError
)

logger = logging.getLogger(__name__)


class ErrorType(Enum):
    """Error classification for recovery strategy."""
    TRANSIENT = "transient"  # Network timeouts, rate limits - retry
    PERMANENT = "permanent"  # Auth failures, invalid data - escalate
    AUTH = "auth"  # Authentication/authorization failures
    VALIDATION = "validation"  # Data validation errors
    NETWORK = "network"  # Network connectivity issues
    RATE_LIMIT = "rate_limit"  # API rate limiting
    TIMEOUT = "timeout"  # Request timeout
    SERVICE_UNAVAILABLE = "service_unavailable"  # External service down
    DATA_CORRUPTION = "data_corruption"  # Data integrity issues
    CONFIGURATION = "configuration"  # Configuration errors


class TransientError(Exception):
    """Transient error that should be retried."""
    pass


class PermanentError(Exception):
    """Permanent error that should be escalated."""
    pass


class AuthError(Exception):
    """Authentication/authorization error."""
    pass


class ErrorRecovery:
    """Handles error recovery, retry logic, and operation queuing."""

    def __init__(self, vault_path: str, max_retries: int = 5, base_delay: int = 1):
        """
        Initialize error recovery system.

        Args:
            vault_path: Path to Obsidian vault
            max_retries: Maximum retry attempts for transient errors
            base_delay: Base delay in seconds for exponential backoff
        """
        self.vault_path = Path(vault_path)
        self.max_retries = max_retries
        self.base_delay = base_delay
        self.queue_path = self.vault_path / "Errors" / "operation_queue.json"
        self.alert_path = self.vault_path / "Needs_Action"

        # Ensure directories exist
        self.queue_path.parent.mkdir(parents=True, exist_ok=True)
        self.alert_path.mkdir(parents=True, exist_ok=True)

        logger.info(f"ErrorRecovery initialized: max_retries={max_retries}, base_delay={base_delay}s")

    def classify_error(self, error: Exception) -> ErrorType:
        """
        Classify error type for appropriate recovery strategy.

        Args:
            error: Exception to classify

        Returns:
            ErrorType enum value
        """
        error_str = str(error).lower()
        error_class = error.__class__.__name__.lower()

        # Auth errors (highest priority - don't retry)
        if isinstance(error, AuthError) or any(keyword in error_str for keyword in
            ['auth', 'token', 'credential', 'permission', 'unauthorized', '401', '403']):
            return ErrorType.AUTH

        # Configuration errors (permanent - don't retry)
        if any(keyword in error_str for keyword in
            ['config', 'configuration', 'missing env', 'environment variable']):
            return ErrorType.CONFIGURATION

        # Data corruption (permanent - don't retry)
        if any(keyword in error_str for keyword in
            ['corrupt', 'integrity', 'checksum', 'malformed json', 'parse error']):
            return ErrorType.DATA_CORRUPTION

        # Rate limit errors (transient - retry with backoff)
        if any(keyword in error_str for keyword in ['rate limit', '429', 'too many requests']):
            return ErrorType.RATE_LIMIT

        # Timeout errors (transient - retry)
        if any(keyword in error_str for keyword in
            ['timeout', 'timed out', 'deadline exceeded']) or 'timeout' in error_class:
            return ErrorType.TIMEOUT

        # Service unavailable (transient - retry)
        if any(keyword in error_str for keyword in
            ['503', 'service unavailable', 'temporarily unavailable', 'maintenance']):
            return ErrorType.SERVICE_UNAVAILABLE

        # Network errors (transient - retry)
        if any(keyword in error_str for keyword in
            ['connection', 'network', 'unreachable', 'dns', 'socket', 'refused']):
            return ErrorType.NETWORK

        # Validation errors (permanent - don't retry)
        if any(keyword in error_str for keyword in ['invalid', 'validation', '400', 'bad request']):
            return ErrorType.VALIDATION

        # Default to transient for unknown errors (safer to retry)
        return ErrorType.TRANSIENT

    def with_retry(self, func: Callable, *args, **kwargs) -> Any:
        """
        Execute function with exponential backoff retry for transient errors.

        Args:
            func: Function to execute
            *args: Positional arguments for function
            **kwargs: Keyword arguments for function

        Returns:
            Function result

        Raises:
            PermanentError: If error is permanent or max retries exceeded
        """
        @retry(
            stop=stop_after_attempt(self.max_retries),
            wait=wait_exponential(multiplier=self.base_delay, max=60),
            retry=retry_if_exception_type(TransientError),
            reraise=True
        )
        def _execute():
            try:
                return func(*args, **kwargs)
            except Exception as e:
                error_type = self.classify_error(e)

                # Transient errors - retry with backoff
                if error_type in [ErrorType.TRANSIENT, ErrorType.NETWORK, ErrorType.TIMEOUT,
                                  ErrorType.RATE_LIMIT, ErrorType.SERVICE_UNAVAILABLE]:
                    logger.warning(f"{error_type.value} error, will retry: {e}")
                    raise TransientError(str(e)) from e

                # Auth errors - escalate immediately
                elif error_type == ErrorType.AUTH:
                    logger.error(f"Auth error, escalating: {e}")
                    self.create_auth_alert(str(e))
                    raise PermanentError(f"Auth error: {e}") from e

                # Configuration errors - escalate immediately
                elif error_type == ErrorType.CONFIGURATION:
                    logger.error(f"Configuration error, escalating: {e}")
                    self.create_config_alert(str(e))
                    raise PermanentError(f"Configuration error: {e}") from e

                # Data corruption - escalate immediately
                elif error_type == ErrorType.DATA_CORRUPTION:
                    logger.error(f"Data corruption error, escalating: {e}")
                    self.create_data_alert(str(e))
                    raise PermanentError(f"Data corruption: {e}") from e

                # Validation errors - permanent, don't retry
                elif error_type == ErrorType.VALIDATION:
                    logger.error(f"Validation error, escalating: {e}")
                    raise PermanentError(f"Validation error: {e}") from e

                # Unknown errors - permanent
                else:
                    logger.error(f"Permanent error, escalating: {e}")
                    raise PermanentError(str(e)) from e

        try:
            return _execute()
        except RetryError as e:
            logger.error(f"Max retries ({self.max_retries}) exceeded: {e}")
            raise PermanentError(f"Max retries exceeded: {e}") from e

    def queue_operation(self, operation: Dict[str, Any]) -> None:
        """
        Queue failed operation for later retry.

        Args:
            operation: Operation details to queue
        """
        try:
            # Load existing queue
            if self.queue_path.exists():
                with open(self.queue_path, 'r') as f:
                    queue = json.load(f)
            else:
                queue = []

            # Add operation with timestamp
            operation['queued_at'] = datetime.now().isoformat()
            operation['retry_count'] = operation.get('retry_count', 0)
            queue.append(operation)

            # Save queue
            with open(self.queue_path, 'w') as f:
                json.dump(queue, f, indent=2)

            logger.info(f"Operation queued: {operation.get('type', 'unknown')}")
        except Exception as e:
            logger.error(f"Failed to queue operation: {e}")

    def get_queued_operations(self) -> List[Dict[str, Any]]:
        """
        Get all queued operations.

        Returns:
            List of queued operations
        """
        try:
            if self.queue_path.exists():
                with open(self.queue_path, 'r') as f:
                    return json.load(f)
            return []
        except Exception as e:
            logger.error(f"Failed to load queued operations: {e}")
            return []

    def remove_queued_operation(self, operation: Dict[str, Any]) -> None:
        """
        Remove operation from queue after successful execution.

        Args:
            operation: Operation to remove
        """
        try:
            queue = self.get_queued_operations()
            queue = [op for op in queue if op != operation]

            with open(self.queue_path, 'w') as f:
                json.dump(queue, f, indent=2)

            logger.info(f"Operation removed from queue: {operation.get('type', 'unknown')}")
        except Exception as e:
            logger.error(f"Failed to remove queued operation: {e}")

    def create_auth_alert(self, error_message: str) -> None:
        """
        Create alert file in Needs_Action/ for authentication failures.

        Args:
            error_message: Error message to include in alert
        """
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            alert_file = self.alert_path / f"AUTH_ALERT_{timestamp}.md"

            content = f"""---
type: auth_alert
created: {datetime.now().isoformat()}
priority: high
status: pending
---

## Authentication Error Alert

**Error**: {error_message}

**Action Required**:
1. Check credentials in .env file
2. Verify API tokens are valid and not expired
3. Refresh authentication if needed
4. Move this file to Done/ when resolved

**Services to Check**:
- Odoo (ODOO_USERNAME, ODOO_PASSWORD)
- Facebook (FACEBOOK_PAGE_ACCESS_TOKEN)
- Instagram (INSTAGRAM_ACCESS_TOKEN)
- Twitter (TWITTER_ACCESS_TOKEN, TWITTER_ACCESS_SECRET)
- Gmail (gmail_token.json)

**Next Steps**:
1. Update credentials in .env
2. Restart the AI employee system
3. Verify authentication works
"""

            with open(alert_file, 'w') as f:
                f.write(content)

            logger.warning(f"Auth alert created: {alert_file}")
        except Exception as e:
            logger.error(f"Failed to create auth alert: {e}")

    def create_config_alert(self, error_message: str) -> None:
        """
        Create alert file in Needs_Action/ for configuration errors.

        Args:
            error_message: Error message to include in alert
        """
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            alert_file = self.alert_path / f"CONFIG_ALERT_{timestamp}.md"

            content = f"""---
type: config_alert
created: {datetime.now().isoformat()}
priority: high
status: pending
---

## Configuration Error Alert

**Error**: {error_message}

**Action Required**:
1. Check .env file for missing or invalid configuration
2. Verify all required environment variables are set
3. Check configuration file syntax
4. Move this file to Done/ when resolved

**Configuration to Check**:
- .env file exists and is readable
- All required variables are set (see .env.example)
- No syntax errors in configuration files
- File paths are correct and accessible

**Next Steps**:
1. Review .env.example for required variables
2. Update .env with correct values
3. Restart the AI employee system
4. Verify configuration works
"""

            with open(alert_file, 'w') as f:
                f.write(content)

            logger.warning(f"Config alert created: {alert_file}")
        except Exception as e:
            logger.error(f"Failed to create config alert: {e}")

    def create_data_alert(self, error_message: str) -> None:
        """
        Create alert file in Needs_Action/ for data corruption errors.

        Args:
            error_message: Error message to include in alert
        """
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            alert_file = self.alert_path / f"DATA_ALERT_{timestamp}.md"

            content = f"""---
type: data_alert
created: {datetime.now().isoformat()}
priority: critical
status: pending
---

## Data Corruption Alert

**Error**: {error_message}

**Action Required**:
1. Identify corrupted data file
2. Restore from backup if available
3. Validate data integrity
4. Move this file to Done/ when resolved

**Common Causes**:
- Interrupted file write operations
- Disk errors or full disk
- Malformed JSON or YAML
- Encoding issues

**Recovery Steps**:
1. Check Logs/ for recent errors
2. Identify affected file from error message
3. Restore from backup or recreate
4. Validate file format and content
5. Restart affected component

**Prevention**:
- Ensure sufficient disk space
- Use atomic file writes
- Validate data before writing
- Maintain regular backups
"""

            with open(alert_file, 'w') as f:
                f.write(content)

            logger.warning(f"Data alert created: {alert_file}")
        except Exception as e:
            logger.error(f"Failed to create data alert: {e}")

    def log_error(self, error: Exception, context: Dict[str, Any]) -> None:
        """
        Log error with full context to daily log file in JSON format.

        Args:
            error: Exception that occurred
            context: Additional context about the error
        """
        try:
            log_dir = self.vault_path / "Logs" / "errors"
            log_dir.mkdir(parents=True, exist_ok=True)

            log_file = log_dir / f"{datetime.now().strftime('%Y-%m-%d')}.json"

            # Load existing logs
            if log_file.exists():
                with open(log_file, 'r') as f:
                    logs = json.load(f)
            else:
                logs = []

            # Add error log with enhanced details
            error_log = {
                "timestamp": datetime.now().isoformat(),
                "error_type": self.classify_error(error).value,
                "error_message": str(error),
                "error_class": error.__class__.__name__,
                "context": context,
                "stack_trace": self._get_stack_trace(error),
                "severity": self._get_severity(error),
                "retry_count": context.get('retry_count', 0),
                "component": context.get('component', 'unknown'),
                "operation": context.get('operation', 'unknown')
            }
            logs.append(error_log)

            # Save logs with pretty formatting
            with open(log_file, 'w') as f:
                json.dump(logs, f, indent=2, default=str)

            logger.debug(f"Error logged to {log_file}")

            # Cleanup old logs (90-day retention)
            self._cleanup_old_logs(log_dir)

        except Exception as e:
            logger.error(f"Failed to log error: {e}")

    def _get_stack_trace(self, error: Exception) -> str:
        """Get formatted stack trace from exception."""
        import traceback
        return ''.join(traceback.format_exception(type(error), error, error.__traceback__))

    def _get_severity(self, error: Exception) -> str:
        """Determine error severity level."""
        error_type = self.classify_error(error)

        if error_type in [ErrorType.AUTH, ErrorType.DATA_CORRUPTION, ErrorType.CONFIGURATION]:
            return "critical"
        elif error_type in [ErrorType.VALIDATION, ErrorType.PERMANENT]:
            return "high"
        elif error_type in [ErrorType.RATE_LIMIT, ErrorType.SERVICE_UNAVAILABLE]:
            return "medium"
        else:
            return "low"

    def _cleanup_old_logs(self, log_dir: Path, retention_days: int = 90) -> None:
        """
        Clean up log files older than retention period.

        Args:
            log_dir: Directory containing log files
            retention_days: Number of days to retain logs (default: 90)
        """
        try:
            from datetime import timedelta
            cutoff_date = datetime.now() - timedelta(days=retention_days)

            for log_file in log_dir.glob("*.json"):
                try:
                    # Parse date from filename (YYYY-MM-DD.json)
                    file_date_str = log_file.stem  # Remove .json extension
                    file_date = datetime.strptime(file_date_str, '%Y-%m-%d')

                    if file_date < cutoff_date:
                        log_file.unlink()
                        logger.info(f"Deleted old log file: {log_file.name}")
                except ValueError:
                    # Skip files that don't match date format
                    continue
                except Exception as e:
                    logger.error(f"Error deleting log file {log_file.name}: {e}")

        except Exception as e:
            logger.error(f"Failed to cleanup old logs: {e}")

    def enable_graceful_degradation(self) -> None:
        """
        Enable graceful degradation mode (read-only operations).

        In this mode:
        - Read operations continue normally
        - Write operations are queued for later
        - System remains operational but limited
        """
        try:
            degradation_file = self.vault_path / "Errors" / "graceful_degradation.json"

            degradation_state = {
                "enabled": True,
                "enabled_at": datetime.now().isoformat(),
                "reason": "Multiple component failures detected",
                "mode": "read_only",
                "queued_operations": 0
            }

            with open(degradation_file, 'w') as f:
                json.dump(degradation_state, f, indent=2)

            logger.warning("Graceful degradation mode enabled - system in read-only mode")

            # Create alert
            self._create_degradation_alert()

        except Exception as e:
            logger.error(f"Failed to enable graceful degradation: {e}")

    def disable_graceful_degradation(self) -> None:
        """Disable graceful degradation mode and resume normal operations."""
        try:
            degradation_file = self.vault_path / "Errors" / "graceful_degradation.json"

            if degradation_file.exists():
                degradation_file.unlink()
                logger.info("Graceful degradation mode disabled - resuming normal operations")

        except Exception as e:
            logger.error(f"Failed to disable graceful degradation: {e}")

    def is_degraded(self) -> bool:
        """Check if system is in graceful degradation mode."""
        degradation_file = self.vault_path / "Errors" / "graceful_degradation.json"
        return degradation_file.exists()

    def _create_degradation_alert(self) -> None:
        """Create alert for graceful degradation mode."""
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            alert_file = self.alert_path / f"DEGRADATION_ALERT_{timestamp}.md"

            content = f"""---
type: degradation_alert
created: {datetime.now().isoformat()}
priority: high
status: active
---

## System Degradation Alert

**Status**: System is operating in graceful degradation mode (read-only)

**What This Means**:
- Read operations continue normally
- Write operations are queued for later execution
- System remains operational but with limited functionality

**Action Required**:
1. Check Logs/errors/ for recent failures
2. Identify and resolve component failures
3. Verify external services are accessible
4. Restart failed components
5. System will automatically resume normal operations when components recover

**Common Causes**:
- Multiple external service failures
- Network connectivity issues
- Authentication failures across services
- Resource exhaustion (disk, memory)

**Recovery Steps**:
1. Review error logs for patterns
2. Check external service status
3. Verify network connectivity
4. Restart affected components
5. Monitor for recovery

**Queued Operations**:
- Check Errors/operation_queue.json for pending operations
- Operations will be retried automatically when system recovers
"""

            with open(alert_file, 'w') as f:
                f.write(content)

            logger.warning(f"Degradation alert created: {alert_file}")

        except Exception as e:
            logger.error(f"Failed to create degradation alert: {e}")


# Global error recovery instance (initialized by main.py)
_error_recovery: Optional[ErrorRecovery] = None


def initialize_error_recovery(vault_path: str, max_retries: int = 5, base_delay: int = 1) -> ErrorRecovery:
    """
    Initialize global error recovery instance.

    Args:
        vault_path: Path to Obsidian vault
        max_retries: Maximum retry attempts
        base_delay: Base delay for exponential backoff

    Returns:
        ErrorRecovery instance
    """
    global _error_recovery
    _error_recovery = ErrorRecovery(vault_path, max_retries, base_delay)
    return _error_recovery


def get_error_recovery() -> ErrorRecovery:
    """
    Get global error recovery instance.

    Returns:
        ErrorRecovery instance

    Raises:
        RuntimeError: If error recovery not initialized
    """
    if _error_recovery is None:
        raise RuntimeError("Error recovery not initialized. Call initialize_error_recovery() first.")
    return _error_recovery
