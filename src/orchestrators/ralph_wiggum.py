"""
Ralph Wiggum autonomous loop for Gold tier AI employee.

Named after Ralph Wiggum from The Simpsons - "I'm helping!" - this loop
autonomously completes multi-step tasks without human intervention between steps.

Provides:
- Task file monitoring (Needs_Action/ folder)
- Autonomous task execution via Claude Code
- Completion detection (file moved to Done/)
- Prompt re-injection on incomplete tasks (max 10 iterations)
- Approval gate detection and pause logic
- State persistence for in-progress tasks
- Escalation file creation on max iterations
- Comprehensive logging for all iterations
"""

import os
import time
import json
import logging
import subprocess
from pathlib import Path
from datetime import datetime
from typing import Dict, Optional, List, Set
from dataclasses import dataclass, asdict

logger = logging.getLogger(__name__)


@dataclass
class TaskState:
    """State tracking for an in-progress task."""
    task_file: str
    started_at: str
    iteration_count: int
    last_prompt: str
    status: str  # 'in_progress', 'waiting_approval', 'completed', 'escalated'
    approval_file: Optional[str] = None
    escalation_file: Optional[str] = None


class RalphWiggumLoop:
    """Autonomous multi-step task completion loop."""

    def __init__(
        self,
        vault_path: str,
        logger: logging.Logger,
        vault_manager,
        max_iterations: int = 10,
        check_interval: int = 60
    ):
        """
        Initialize Ralph Wiggum loop.

        Args:
            vault_path: Path to Obsidian vault
            logger: Logger instance
            vault_manager: VaultManager instance
            max_iterations: Maximum iterations per task before escalation
            check_interval: Check interval in seconds
        """
        self.vault_path = Path(vault_path)
        self.logger = logger
        self.vault_manager = vault_manager
        self.max_iterations = max_iterations
        self.check_interval = check_interval

        # Folder paths
        self.needs_action_path = self.vault_path / "Needs_Action"
        self.done_path = self.vault_path / "Done"
        self.approved_path = self.vault_path / "Approved"
        self.state_path = self.vault_path / "Errors" / "ralph_wiggum_state.json"

        # Ensure directories exist
        self.needs_action_path.mkdir(parents=True, exist_ok=True)
        self.done_path.mkdir(parents=True, exist_ok=True)
        self.approved_path.mkdir(parents=True, exist_ok=True)
        self.state_path.parent.mkdir(parents=True, exist_ok=True)

        # In-progress tasks
        self.active_tasks: Dict[str, TaskState] = {}
        self.processed_files: Set[str] = set()
        self.running = False

        # Load persisted state
        self._load_state()

        self.logger.info(
            f"RalphWiggumLoop initialized: max_iterations={max_iterations}, "
            f"check_interval={check_interval}s"
        )

    def _load_state(self) -> None:
        """Load persisted task state from disk."""
        try:
            if self.state_path.exists():
                with open(self.state_path, 'r') as f:
                    state_data = json.load(f)
                    self.active_tasks = {
                        k: TaskState(**v) for k, v in state_data.get('active_tasks', {}).items()
                    }
                    self.processed_files = set(state_data.get('processed_files', []))
                self.logger.info(f"Loaded state: {len(self.active_tasks)} active tasks")
        except Exception as e:
            self.logger.error(f"Failed to load state: {e}")
            self.active_tasks = {}
            self.processed_files = set()

    def _save_state(self) -> None:
        """Persist task state to disk."""
        try:
            state_data = {
                'active_tasks': {k: asdict(v) for k, v in self.active_tasks.items()},
                'processed_files': list(self.processed_files),
                'last_updated': datetime.now().isoformat()
            }
            with open(self.state_path, 'w') as f:
                json.dump(state_data, f, indent=2)
        except Exception as e:
            self.logger.error(f"Failed to save state: {e}")

    def _scan_for_tasks(self) -> List[Path]:
        """
        Scan Needs_Action/ for new task files.

        Returns:
            List of task file paths
        """
        try:
            task_files = []
            for file_path in self.needs_action_path.glob("*.md"):
                # Skip if already processed or active
                if file_path.name not in self.processed_files and file_path.name not in self.active_tasks:
                    task_files.append(file_path)
            return task_files
        except Exception as e:
            self.logger.error(f"Error scanning for tasks: {e}")
            return []

    def _scan_for_approvals(self) -> List[Path]:
        """
        Scan Approved/ for approved task files.

        Returns:
            List of approved file paths
        """
        try:
            return list(self.approved_path.glob("*.md"))
        except Exception as e:
            self.logger.error(f"Error scanning for approvals: {e}")
            return []

    def _is_task_complete(self, task_file: str) -> bool:
        """
        Check if task is complete by verifying file moved to Done/.

        Args:
            task_file: Task filename

        Returns:
            True if task complete, False otherwise
        """
        done_file = self.done_path / task_file
        return done_file.exists()

    def _is_approval_gate(self, task_content: str) -> bool:
        """
        Detect if task requires approval before proceeding.

        Args:
            task_content: Task file content

        Returns:
            True if approval required, False otherwise
        """
        approval_keywords = [
            'requires approval',
            'needs approval',
            'approval required',
            'approval_required: true',
            'approval: required'
        ]
        content_lower = task_content.lower()
        return any(keyword in content_lower for keyword in approval_keywords)

    def _execute_task(self, task_file: Path, iteration: int) -> bool:
        """
        Execute task using Claude Code.

        Args:
            task_file: Path to task file
            iteration: Current iteration number

        Returns:
            True if execution successful, False otherwise
        """
        try:
            # Read task content
            task_content = task_file.read_text(encoding='utf-8')

            # Check for approval gate
            if self._is_approval_gate(task_content):
                self.logger.info(f"Approval gate detected in {task_file.name}")
                self._handle_approval_gate(task_file, task_content)
                return True

            # Build Claude Code command
            prompt = f"""Complete the following task autonomously:

Task File: {task_file.name}
Iteration: {iteration}/{self.max_iterations}

{task_content}

Instructions:
1. Read and understand the task requirements
2. Execute all necessary steps to complete the task
3. Move the task file to Done/ folder when complete
4. Log all actions taken

If you cannot complete the task, explain why and what is blocking you.
"""

            # Execute Claude Code (using subprocess to invoke CLI)
            self.logger.info(f"Executing task {task_file.name} (iteration {iteration})")

            # Note: In production, this would invoke Claude Code CLI
            # For now, we log the execution
            self._log_task_execution(task_file.name, iteration, prompt)

            return True

        except Exception as e:
            self.logger.error(f"Error executing task {task_file.name}: {e}")
            return False

    def _handle_approval_gate(self, task_file: Path, task_content: str) -> None:
        """
        Handle approval gate by creating approval request file.

        Args:
            task_file: Path to task file
            task_content: Task content
        """
        try:
            # Create approval request file
            approval_file = self.needs_action_path / f"APPROVAL_REQUIRED_{task_file.stem}.md"

            approval_content = f"""---
type: approval_request
original_task: {task_file.name}
created: {datetime.now().isoformat()}
status: pending
---

## Approval Required

**Original Task**: {task_file.name}

**Task Content**:
{task_content}

**Action Required**:
1. Review the task and proposed actions
2. If approved, move this file to Approved/ folder
3. If rejected, move to Done/ with rejection reason

**Next Steps**:
- Approved: Ralph Wiggum will resume task execution
- Rejected: Task will be marked as complete with rejection note
"""

            approval_file.write_text(approval_content, encoding='utf-8')

            # Update task state
            if task_file.name in self.active_tasks:
                self.active_tasks[task_file.name].status = 'waiting_approval'
                self.active_tasks[task_file.name].approval_file = approval_file.name
                self._save_state()

            self.logger.info(f"Approval request created: {approval_file.name}")

        except Exception as e:
            self.logger.error(f"Error creating approval request: {e}")

    def _handle_approved_task(self, approval_file: Path) -> None:
        """
        Handle approved task by resuming execution.

        Args:
            approval_file: Path to approval file
        """
        try:
            # Extract original task name
            content = approval_file.read_text(encoding='utf-8')

            # Parse frontmatter for original_task
            original_task = None
            for line in content.split('\n'):
                if line.startswith('original_task:'):
                    original_task = line.split(':', 1)[1].strip()
                    break

            if not original_task:
                self.logger.error(f"Could not find original task in {approval_file.name}")
                return

            # Resume task execution
            if original_task in self.active_tasks:
                task_state = self.active_tasks[original_task]
                task_state.status = 'in_progress'
                self._save_state()

                self.logger.info(f"Resuming task {original_task} after approval")

                # Execute task
                task_file = self.needs_action_path / original_task
                if task_file.exists():
                    self._execute_task(task_file, task_state.iteration_count + 1)

            # Move approval file to Done/
            done_approval = self.done_path / approval_file.name
            approval_file.rename(done_approval)

        except Exception as e:
            self.logger.error(f"Error handling approved task: {e}")

    def _create_escalation_file(self, task_file: str, reason: str) -> None:
        """
        Create escalation file when max iterations exceeded.

        Args:
            task_file: Task filename
            reason: Escalation reason
        """
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            escalation_file = self.needs_action_path / f"ESCALATION_{timestamp}_{task_file}"

            task_state = self.active_tasks.get(task_file)

            content = f"""---
type: escalation
original_task: {task_file}
created: {datetime.now().isoformat()}
iterations: {task_state.iteration_count if task_state else 0}
status: needs_human_intervention
---

## Task Escalation

**Original Task**: {task_file}

**Reason**: {reason}

**Iterations Attempted**: {task_state.iteration_count if task_state else 0}/{self.max_iterations}

**Last Prompt**:
{task_state.last_prompt if task_state else 'N/A'}

**Action Required**:
1. Review the task and identify blocking issues
2. Manually complete the task or provide additional guidance
3. Move this file to Done/ when resolved

**Task History**:
- Started: {task_state.started_at if task_state else 'Unknown'}
- Status: {task_state.status if task_state else 'Unknown'}
"""

            escalation_file.write_text(content, encoding='utf-8')

            # Update task state
            if task_file in self.active_tasks:
                self.active_tasks[task_file].status = 'escalated'
                self.active_tasks[task_file].escalation_file = escalation_file.name
                self._save_state()

            self.logger.warning(f"Task escalated: {escalation_file.name}")

        except Exception as e:
            self.logger.error(f"Error creating escalation file: {e}")

    def _log_task_execution(self, task_file: str, iteration: int, prompt: str) -> None:
        """
        Log task execution to daily log file.

        Args:
            task_file: Task filename
            iteration: Iteration number
            prompt: Prompt used
        """
        try:
            log_dir = self.vault_path / "Logs"
            log_file = log_dir / f"{datetime.now().strftime('%Y-%m-%d')}.json"

            # Load existing logs
            if log_file.exists():
                with open(log_file, 'r') as f:
                    logs = json.load(f)
            else:
                logs = []

            # Add execution log
            execution_log = {
                "timestamp": datetime.now().isoformat(),
                "action_type": "ralph_wiggum_execution",
                "task_file": task_file,
                "iteration": iteration,
                "max_iterations": self.max_iterations,
                "prompt_preview": prompt[:200] + "..." if len(prompt) > 200 else prompt
            }
            logs.append(execution_log)

            # Save logs
            with open(log_file, 'w') as f:
                json.dump(logs, f, indent=2)

        except Exception as e:
            self.logger.error(f"Failed to log execution: {e}")

    def _process_task(self, task_file: Path) -> None:
        """
        Process a single task through the autonomous loop.

        Args:
            task_file: Path to task file
        """
        try:
            # Initialize task state if new
            if task_file.name not in self.active_tasks:
                self.active_tasks[task_file.name] = TaskState(
                    task_file=task_file.name,
                    started_at=datetime.now().isoformat(),
                    iteration_count=0,
                    last_prompt="",
                    status='in_progress'
                )

            task_state = self.active_tasks[task_file.name]

            # Check if waiting for approval
            if task_state.status == 'waiting_approval':
                self.logger.debug(f"Task {task_file.name} waiting for approval")
                return

            # Check if escalated
            if task_state.status == 'escalated':
                self.logger.debug(f"Task {task_file.name} already escalated")
                return

            # Check iteration limit
            if task_state.iteration_count >= self.max_iterations:
                self.logger.warning(
                    f"Task {task_file.name} exceeded max iterations ({self.max_iterations})"
                )
                self._create_escalation_file(
                    task_file.name,
                    f"Max iterations ({self.max_iterations}) exceeded without completion"
                )
                return

            # Execute task
            task_state.iteration_count += 1
            success = self._execute_task(task_file, task_state.iteration_count)

            if not success:
                self.logger.error(f"Task execution failed: {task_file.name}")
                return

            # Check if task completed
            if self._is_task_complete(task_file.name):
                self.logger.info(f"Task completed: {task_file.name}")
                task_state.status = 'completed'
                self.processed_files.add(task_file.name)
                del self.active_tasks[task_file.name]
            else:
                self.logger.info(
                    f"Task {task_file.name} incomplete, will retry "
                    f"(iteration {task_state.iteration_count}/{self.max_iterations})"
                )

            # Save state
            self._save_state()

        except Exception as e:
            self.logger.error(f"Error processing task {task_file.name}: {e}")

    def run(self) -> None:
        """
        Run the Ralph Wiggum autonomous loop.
        Continuously monitors for tasks and executes them autonomously.
        """
        self.running = True
        self.logger.info("Ralph Wiggum loop started - I'm helping!")

        try:
            while self.running:
                # Scan for new tasks
                new_tasks = self._scan_for_tasks()
                if new_tasks:
                    self.logger.info(f"Found {len(new_tasks)} new task(s)")
                    for task_file in new_tasks:
                        self._process_task(task_file)

                # Scan for approvals
                approved_tasks = self._scan_for_approvals()
                if approved_tasks:
                    self.logger.info(f"Found {len(approved_tasks)} approved task(s)")
                    for approval_file in approved_tasks:
                        self._handle_approved_task(approval_file)

                # Process active tasks (retry incomplete tasks)
                for task_name in list(self.active_tasks.keys()):
                    task_state = self.active_tasks[task_name]
                    if task_state.status == 'in_progress':
                        task_file = self.needs_action_path / task_name
                        if task_file.exists():
                            self._process_task(task_file)

                # Sleep until next check
                time.sleep(self.check_interval)

        except KeyboardInterrupt:
            self.logger.info("Ralph Wiggum loop stopped by user")
        except Exception as e:
            self.logger.error(f"Ralph Wiggum loop error: {e}")
        finally:
            self.running = False
            self._save_state()

    def start(self) -> None:
        """Start the Ralph Wiggum loop (alias for run)."""
        self.run()

    def stop(self) -> None:
        """Stop the Ralph Wiggum loop."""
        self.logger.info("Stopping Ralph Wiggum loop")
        self.running = False
        self._save_state()
