"""
Scheduler for Personal AI Employee (Silver Tier).

Manages scheduled tasks like daily briefings.
"""

import schedule
import time
from datetime import datetime
from typing import Callable, Dict, Any


class TaskScheduler:
    """Manages scheduled tasks."""

    def __init__(self, logger):
        """
        Initialize task scheduler.

        Args:
            logger: Logger instance
        """
        self.logger = logger
        self.running = False
        self.tasks = {}

    def register_daily_task(self, task_name: str, time_str: str, task_func: Callable, *args, **kwargs):
        """
        Register a daily task.

        Args:
            task_name: Name of the task
            time_str: Time in HH:MM format (24-hour)
            task_func: Function to execute
            *args: Arguments to pass to task_func
            **kwargs: Keyword arguments to pass to task_func
        """
        try:
            def wrapped_task():
                try:
                    self.logger.info(f"Executing scheduled task: {task_name}")
                    task_func(*args, **kwargs)
                    self.tasks[task_name]['last_run'] = datetime.now()
                    self.logger.info(f"Task '{task_name}' completed successfully")
                except Exception as e:
                    self.logger.error(f"Error executing task '{task_name}': {e}", exc_info=True)

            schedule.every().day.at(time_str).do(wrapped_task)
            self.tasks[task_name] = {
                'time': time_str,
                'function': task_func,
                'last_run': None
            }
            self.logger.info(f"Registered daily task '{task_name}' at {time_str}")
        except Exception as e:
            self.logger.error(f"Error registering task '{task_name}': {e}")

    def register_interval_task(self, task_name: str, interval_minutes: int, task_func: Callable):
        """
        Register a task that runs at regular intervals.

        Args:
            task_name: Name of the task
            interval_minutes: Interval in minutes
            task_func: Function to execute
        """
        try:
            schedule.every(interval_minutes).minutes.do(task_func)
            self.tasks[task_name] = {
                'interval': interval_minutes,
                'function': task_func,
                'last_run': None
            }
            self.logger.info(f"Registered interval task '{task_name}' every {interval_minutes} minutes")
        except Exception as e:
            self.logger.error(f"Error registering task '{task_name}': {e}")

    def start(self):
        """Start the scheduler."""
        self.running = True
        self.logger.info("Starting Task Scheduler")
        self.run()

    def stop(self):
        """Stop the scheduler."""
        self.running = False
        self.logger.info("Stopping Task Scheduler")

    def run(self):
        """Main scheduler loop."""
        while self.running:
            try:
                schedule.run_pending()
                time.sleep(60)  # Check every minute
            except Exception as e:
                self.logger.error(f"Error in scheduler loop: {e}", exc_info=True)
                time.sleep(60)

        self.logger.info("Task Scheduler stopped")

    def get_next_run_times(self) -> Dict[str, Any]:
        """
        Get next run times for all scheduled tasks.

        Returns:
            Dictionary of task names to next run times
        """
        next_runs = {}
        for job in schedule.jobs:
            next_runs[str(job)] = job.next_run
        return next_runs


def create_scheduler(logger) -> TaskScheduler:
    """
    Factory function to create a TaskScheduler instance.

    Args:
        logger: Logger instance

    Returns:
        TaskScheduler instance
    """
    return TaskScheduler(logger)
