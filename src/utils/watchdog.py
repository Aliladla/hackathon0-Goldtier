"""
Watchdog module for Gold tier autonomous AI employee.

Monitors component health and automatically restarts crashed processes.
Provides:
- PID monitoring for all components
- Auto-restart on crash detection
- Health check logging
- Dashboard notifications
- MCP server health monitoring
- Component status tracking
"""

import os
import sys
import time
import psutil
import logging
import subprocess
import requests
from pathlib import Path
from datetime import datetime
from typing import Dict, Optional, List
import json

logger = logging.getLogger(__name__)


class ComponentWatchdog:
    """Monitors and restarts crashed components."""

    def __init__(self, vault_path: str, check_interval: int = 60):
        """
        Initialize watchdog.

        Args:
            vault_path: Path to Obsidian vault
            check_interval: Health check interval in seconds
        """
        self.vault_path = Path(vault_path)
        self.check_interval = check_interval
        self.components: Dict[str, Dict] = {}
        self.mcp_servers: Dict[str, Dict] = {}
        self.log_path = self.vault_path / "Logs" / "watchdog"
        self.dashboard_path = self.vault_path / "Dashboard.md"
        self.alert_path = self.vault_path / "Needs_Action"

        # Ensure directories exist
        self.log_path.mkdir(parents=True, exist_ok=True)
        self.alert_path.mkdir(parents=True, exist_ok=True)

        logger.info(f"ComponentWatchdog initialized: check_interval={check_interval}s")

    def register_component(self, name: str, pid: int, command: str, critical: bool = True) -> None:
        """
        Register component for monitoring.

        Args:
            name: Component name
            pid: Process ID
            command: Command to restart component
            critical: Whether component is critical (restart on failure)
        """
        self.components[name] = {
            'pid': pid,
            'command': command,
            'critical': critical,
            'last_check': datetime.now(),
            'restart_count': 0,
            'status': 'running'
        }
        logger.info(f"Registered component: {name} (PID: {pid})")

    def register_mcp_server(self, name: str, health_url: str, critical: bool = True) -> None:
        """
        Register MCP server for health monitoring.

        Args:
            name: MCP server name (e.g., 'odoo', 'facebook', 'instagram')
            health_url: Health check endpoint URL
            critical: Whether server is critical for operations
        """
        self.mcp_servers[name] = {
            'health_url': health_url,
            'critical': critical,
            'last_check': datetime.now(),
            'status': 'unknown',
            'consecutive_failures': 0,
            'last_success': None,
            'last_failure': None
        }
        logger.info(f"Registered MCP server: {name} (health: {health_url})")

    def check_mcp_server_health(self, name: str) -> bool:
        """
        Check health of MCP server via HTTP endpoint.

        Args:
            name: MCP server name

        Returns:
            True if healthy, False otherwise
        """
        if name not in self.mcp_servers:
            return False

        server = self.mcp_servers[name]
        health_url = server['health_url']

        try:
            response = requests.get(health_url, timeout=5)
            is_healthy = response.status_code == 200

            if is_healthy:
                server['status'] = 'healthy'
                server['consecutive_failures'] = 0
                server['last_success'] = datetime.now()
                server['last_check'] = datetime.now()
                return True
            else:
                server['status'] = 'unhealthy'
                server['consecutive_failures'] += 1
                server['last_failure'] = datetime.now()
                server['last_check'] = datetime.now()
                logger.warning(f"MCP server {name} unhealthy: HTTP {response.status_code}")
                return False

        except requests.exceptions.Timeout:
            server['status'] = 'timeout'
            server['consecutive_failures'] += 1
            server['last_failure'] = datetime.now()
            server['last_check'] = datetime.now()
            logger.error(f"MCP server {name} health check timeout")
            return False

        except requests.exceptions.ConnectionError:
            server['status'] = 'unreachable'
            server['consecutive_failures'] += 1
            server['last_failure'] = datetime.now()
            server['last_check'] = datetime.now()
            logger.error(f"MCP server {name} unreachable")
            return False

        except Exception as e:
            server['status'] = 'error'
            server['consecutive_failures'] += 1
            server['last_failure'] = datetime.now()
            server['last_check'] = datetime.now()
            logger.error(f"MCP server {name} health check error: {e}")
            return False

    def check_all_mcp_servers(self) -> Dict[str, str]:
        """
        Check health of all registered MCP servers.

        Returns:
            Dict mapping server names to status
        """
        status_report = {}

        for name in self.mcp_servers.keys():
            is_healthy = self.check_mcp_server_health(name)
            server = self.mcp_servers[name]

            status_report[name] = server['status']

            # Alert if critical server has multiple consecutive failures
            if server['critical'] and server['consecutive_failures'] >= 3:
                self._create_mcp_server_alert(name, server)

        return status_report

    def _create_mcp_server_alert(self, server_name: str, server_info: Dict) -> None:
        """
        Create alert for MCP server failures.

        Args:
            server_name: MCP server name
            server_info: Server status information
        """
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            alert_file = self.alert_path / f"MCP_SERVER_ALERT_{server_name}_{timestamp}.md"

            # Skip if recent alert exists (within last hour)
            recent_alerts = list(self.alert_path.glob(f"MCP_SERVER_ALERT_{server_name}_*.md"))
            if recent_alerts:
                latest_alert = max(recent_alerts, key=lambda p: p.stat().st_mtime)
                alert_age = datetime.now().timestamp() - latest_alert.stat().st_mtime
                if alert_age < 3600:  # 1 hour
                    return

            content = f"""---
type: mcp_server_alert
server: {server_name}
created: {datetime.now().isoformat()}
priority: high
status: pending
---

## MCP Server Failure Alert

**Server**: {server_name}
**Status**: {server_info['status']}
**Consecutive Failures**: {server_info['consecutive_failures']}
**Last Success**: {server_info['last_success'].isoformat() if server_info['last_success'] else 'Never'}
**Last Failure**: {server_info['last_failure'].isoformat() if server_info['last_failure'] else 'Unknown'}

**Action Required**:
1. Check if MCP server process is running
2. Verify server configuration in .claude/mcp.json
3. Check server logs for errors
4. Verify network connectivity
5. Restart MCP server if needed

**Common Issues**:
- Server process crashed or not started
- Port already in use
- Configuration errors in mcp.json
- Missing environment variables
- Network connectivity issues

**Recovery Steps**:
1. Check MCP server logs: `mcp-servers/{server_name}/logs/`
2. Verify environment variables in .env
3. Restart MCP server: `node mcp-servers/{server_name}/index.js`
4. Verify health endpoint: `curl {server_info['health_url']}`
5. Check Claude Code MCP configuration

**Impact**:
- {server_name.title()} integration unavailable
- Related operations will fail or be queued
- System may enter graceful degradation mode

Move this file to Done/ when resolved.
"""

            with open(alert_file, 'w') as f:
                f.write(content)

            logger.warning(f"MCP server alert created: {alert_file.name}")

        except Exception as e:
            logger.error(f"Failed to create MCP server alert: {e}")

    def get_component_health_summary(self) -> Dict[str, any]:
        """
        Get comprehensive health summary for all components and MCP servers.

        Returns:
            Dict with health summary
        """
        summary = {
            'timestamp': datetime.now().isoformat(),
            'components': {},
            'mcp_servers': {},
            'overall_health': 'healthy'
        }

        # Component health
        for name, component in self.components.items():
            is_running = self.is_process_running(component['pid'])
            summary['components'][name] = {
                'status': 'running' if is_running else 'crashed',
                'pid': component['pid'],
                'restart_count': component['restart_count'],
                'critical': component['critical']
            }

            if not is_running and component['critical']:
                summary['overall_health'] = 'degraded'

        # MCP server health
        for name, server in self.mcp_servers.items():
            summary['mcp_servers'][name] = {
                'status': server['status'],
                'consecutive_failures': server['consecutive_failures'],
                'critical': server['critical']
            }

            if server['status'] != 'healthy' and server['critical']:
                summary['overall_health'] = 'degraded'

        # Check if multiple critical components/servers are down
        critical_failures = sum(
            1 for c in summary['components'].values()
            if c['status'] == 'crashed' and c['critical']
        ) + sum(
            1 for s in summary['mcp_servers'].values()
            if s['status'] != 'healthy' and s['critical']
        )

        if critical_failures >= 2:
            summary['overall_health'] = 'critical'

        return summary

    def log_health_check(self, summary: Dict) -> None:
        """
        Log health check results to daily log file.

        Args:
            summary: Health summary from get_component_health_summary()
        """
        try:
            log_file = self.log_path / f"{datetime.now().strftime('%Y-%m-%d')}.json"

            # Load existing logs
            if log_file.exists():
                with open(log_file, 'r') as f:
                    logs = json.load(f)
            else:
                logs = []

            # Add health check log
            logs.append(summary)

            # Save logs
            with open(log_file, 'w') as f:
                json.dump(logs, f, indent=2, default=str)

        except Exception as e:
            logger.error(f"Failed to log health check: {e}")

    def is_process_running(self, pid: int) -> bool:
        """
        Check if process is running.

        Args:
            pid: Process ID to check

        Returns:
            True if process is running, False otherwise
        """
        try:
            process = psutil.Process(pid)
            return process.is_running() and process.status() != psutil.STATUS_ZOMBIE
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            return False

    def restart_component(self, name: str) -> Optional[int]:
        """
        Restart crashed component.

        Args:
            name: Component name

        Returns:
            New PID if restart successful, None otherwise
        """
        component = self.components[name]
        command = component['command']

        try:
            logger.warning(f"Restarting component: {name}")

            # Start new process
            if sys.platform == 'win32':
                # Windows
                process = subprocess.Popen(
                    command,
                    shell=True,
                    creationflags=subprocess.CREATE_NEW_PROCESS_GROUP
                )
            else:
                # Unix-like
                process = subprocess.Popen(
                    command,
                    shell=True,
                    preexec_fn=os.setpgrp
                )

            new_pid = process.pid
            component['pid'] = new_pid
            component['restart_count'] += 1
            component['status'] = 'running'
            component['last_restart'] = datetime.now()

            logger.info(f"Component restarted: {name} (New PID: {new_pid})")
            self.log_restart(name, new_pid)
            self.notify_dashboard(name, 'restarted')

            return new_pid

        except Exception as e:
            logger.error(f"Failed to restart component {name}: {e}")
            component['status'] = 'failed'
            self.notify_dashboard(name, 'failed')
            return None

    def check_components(self) -> Dict[str, str]:
        """
        Check health of all registered components.

        Returns:
            Dict mapping component names to status
        """
        status_report = {}

        for name, component in self.components.items():
            pid = component['pid']
            is_running = self.is_process_running(pid)

            if is_running:
                component['status'] = 'running'
                component['last_check'] = datetime.now()
                status_report[name] = 'running'
            else:
                logger.error(f"Component crashed: {name} (PID: {pid})")
                component['status'] = 'crashed'
                status_report[name] = 'crashed'

                # Create crash alert
                self._create_crash_alert(name, component)

                # Restart if critical
                if component['critical']:
                    new_pid = self.restart_component(name)
                    if new_pid:
                        status_report[name] = 'restarted'
                    else:
                        status_report[name] = 'failed'

        return status_report

    def _create_crash_alert(self, component_name: str, component_info: Dict) -> None:
        """
        Create alert for component crash.

        Args:
            component_name: Component name
            component_info: Component status information
        """
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            alert_file = self.alert_path / f"CRASH_ALERT_{component_name}_{timestamp}.md"

            content = f"""---
type: crash_alert
component: {component_name}
created: {datetime.now().isoformat()}
priority: critical
status: pending
---

## Component Crash Alert

**Component**: {component_name}
**PID**: {component_info['pid']}
**Restart Count**: {component_info['restart_count']}
**Status**: {component_info['status']}

**Action Required**:
1. Check component logs for crash reason
2. Verify system resources (memory, disk space)
3. Check for configuration errors
4. Review recent changes that may have caused crash
5. Manually restart if auto-restart failed

**Common Causes**:
- Unhandled exceptions
- Memory exhaustion
- Resource conflicts
- Configuration errors
- External service failures

**Recovery Steps**:
1. Check Logs/ for error messages
2. Verify .env configuration
3. Check system resources: `top` or Task Manager
4. Review recent code changes
5. Restart component manually if needed

**Impact**:
- {component_name} functionality unavailable
- Related operations will fail or be queued
- System may enter graceful degradation mode

**Auto-Restart**: {'Attempted' if component_info['critical'] else 'Not configured (non-critical component)'}

Move this file to Done/ when resolved.
"""

            with open(alert_file, 'w') as f:
                f.write(content)

            logger.warning(f"Crash alert created: {alert_file.name}")

        except Exception as e:
            logger.error(f"Failed to create crash alert: {e}")

    def log_restart(self, component_name: str, new_pid: int) -> None:
        """
        Log component restart to daily log file.

        Args:
            component_name: Name of restarted component
            new_pid: New process ID
        """
        try:
            log_file = self.log_path / f"{datetime.now().strftime('%Y-%m-%d')}.json"

            # Load existing logs
            if log_file.exists():
                with open(log_file, 'r') as f:
                    logs = json.load(f)
            else:
                logs = []

            # Add restart log
            restart_log = {
                "timestamp": datetime.now().isoformat(),
                "action_type": "component_restart",
                "component": component_name,
                "new_pid": new_pid,
                "restart_count": self.components[component_name]['restart_count']
            }
            logs.append(restart_log)

            # Save logs
            with open(log_file, 'w') as f:
                json.dump(logs, f, indent=2)

        except Exception as e:
            logger.error(f"Failed to log restart: {e}")

    def notify_dashboard(self, component_name: str, status: str) -> None:
        """
        Update Dashboard.md with component status notification.

        Args:
            component_name: Component name
            status: Status (restarted, failed, etc.)
        """
        try:
            if not self.dashboard_path.exists():
                return

            # Read current dashboard
            with open(self.dashboard_path, 'r') as f:
                content = f.read()

            # Add notification at top
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            notification = f"\n**[{timestamp}]** Component `{component_name}` {status}\n"

            # Insert after first heading
            lines = content.split('\n')
            for i, line in enumerate(lines):
                if line.startswith('#'):
                    lines.insert(i + 1, notification)
                    break

            # Write updated dashboard
            with open(self.dashboard_path, 'w') as f:
                f.write('\n'.join(lines))

            logger.info(f"Dashboard updated: {component_name} {status}")

        except Exception as e:
            logger.error(f"Failed to update dashboard: {e}")

    def run(self) -> None:
        """
        Run watchdog monitoring loop.
        Continuously checks component health and restarts crashed components.
        Also monitors MCP server health.
        """
        logger.info("Watchdog monitoring started")

        try:
            while True:
                # Check component health
                component_status = self.check_components()

                # Check MCP server health
                mcp_status = self.check_all_mcp_servers()

                # Get comprehensive health summary
                health_summary = self.get_component_health_summary()

                # Log health check
                self.log_health_check(health_summary)

                # Log status
                running = sum(1 for s in component_status.values() if s == 'running')
                crashed = sum(1 for s in component_status.values() if s in ['crashed', 'failed'])
                healthy_mcp = sum(1 for s in mcp_status.values() if s == 'healthy')
                unhealthy_mcp = len(mcp_status) - healthy_mcp

                if crashed > 0 or unhealthy_mcp > 0:
                    logger.warning(
                        f"Health check: {running} components running, {crashed} crashed/failed, "
                        f"{healthy_mcp} MCP servers healthy, {unhealthy_mcp} unhealthy"
                    )
                else:
                    logger.debug(
                        f"Health check: {running} components running, {healthy_mcp} MCP servers healthy"
                    )

                # Update dashboard with overall health
                self._update_dashboard_health(health_summary['overall_health'])

                # Check if graceful degradation needed
                if health_summary['overall_health'] == 'critical':
                    logger.error("Multiple critical failures detected - system may need graceful degradation")
                    # Trigger graceful degradation via error recovery
                    try:
                        from utils.error_recovery import get_error_recovery
                        error_recovery = get_error_recovery()
                        if not error_recovery.is_degraded():
                            error_recovery.enable_graceful_degradation()
                    except Exception as e:
                        logger.error(f"Failed to enable graceful degradation: {e}")

                # Sleep until next check
                time.sleep(self.check_interval)

        except KeyboardInterrupt:
            logger.info("Watchdog monitoring stopped by user")
        except Exception as e:
            logger.error(f"Watchdog monitoring error: {e}")

    def _update_dashboard_health(self, overall_health: str) -> None:
        """
        Update Dashboard.md with overall system health status.

        Args:
            overall_health: Overall health status (healthy, degraded, critical)
        """
        try:
            if not self.dashboard_path.exists():
                return

            # Read current dashboard
            content = self.dashboard_path.read_text(encoding='utf-8')

            # Update health status
            health_emoji = {
                'healthy': '✅',
                'degraded': '⚠️',
                'critical': '🔴'
            }

            emoji = health_emoji.get(overall_health, '❓')
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            health_line = f"**System Health**: {emoji} {overall_health.title()} (Last check: {timestamp})"

            # Replace existing health line or add new one
            lines = content.split('\n')
            health_found = False

            for i, line in enumerate(lines):
                if line.startswith('**System Health**:'):
                    lines[i] = health_line
                    health_found = True
                    break

            if not health_found:
                # Add after first heading
                for i, line in enumerate(lines):
                    if line.startswith('#'):
                        lines.insert(i + 1, f"\n{health_line}\n")
                        break

            # Write updated dashboard
            self.dashboard_path.write_text('\n'.join(lines), encoding='utf-8')

        except Exception as e:
            logger.error(f"Failed to update dashboard health: {e}")

    def get_status_report(self) -> Dict[str, Dict]:
        """
        Get detailed status report for all components.

        Returns:
            Dict mapping component names to status details
        """
        report = {}
        for name, component in self.components.items():
            report[name] = {
                'status': component['status'],
                'pid': component['pid'],
                'restart_count': component['restart_count'],
                'last_check': component['last_check'].isoformat(),
                'is_running': self.is_process_running(component['pid'])
            }
        return report


# Global watchdog instance (initialized by main.py)
_watchdog: Optional[ComponentWatchdog] = None


def initialize_watchdog(vault_path: str, check_interval: int = 60) -> ComponentWatchdog:
    """
    Initialize global watchdog instance.

    Args:
        vault_path: Path to Obsidian vault
        check_interval: Health check interval in seconds

    Returns:
        ComponentWatchdog instance
    """
    global _watchdog
    _watchdog = ComponentWatchdog(vault_path, check_interval)
    return _watchdog


def get_watchdog() -> ComponentWatchdog:
    """
    Get global watchdog instance.

    Returns:
        ComponentWatchdog instance

    Raises:
        RuntimeError: If watchdog not initialized
    """
    if _watchdog is None:
        raise RuntimeError("Watchdog not initialized. Call initialize_watchdog() first.")
    return _watchdog
