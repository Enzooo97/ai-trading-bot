"""
Trading scheduler for automated start/stop at specified times.
Handles timezone-aware scheduling (London time).
"""
import logging
from datetime import datetime, time
from typing import Callable, Optional
import pytz
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
from src.config import settings

logger = logging.getLogger(__name__)


class TradingScheduler:
    """
    Manages automated trading schedule.
    Starts and stops bot at configured times in London timezone.
    """

    def __init__(
        self,
        start_callback: Callable,
        stop_callback: Callable,
    ):
        """
        Initialize scheduler.

        Args:
            start_callback: Function to call when starting trading
            stop_callback: Function to call when stopping trading
        """
        self.start_callback = start_callback
        self.stop_callback = stop_callback
        self.scheduler = BackgroundScheduler(timezone=settings.timezone)
        self.is_trading_time = False

    def setup_schedule(self):
        """Setup automated trading schedule."""
        try:
            # Parse start and stop times
            start_time = settings.get_trading_start_time()
            stop_time = settings.get_trading_end_time()
            tz = settings.get_timezone()

            logger.info(
                f"Setting up trading schedule: "
                f"{start_time} - {stop_time} {settings.timezone}"
            )

            # Schedule start
            self.scheduler.add_job(
                self._handle_start,
                CronTrigger(
                    hour=start_time.hour,
                    minute=start_time.minute,
                    timezone=tz,
                ),
                id='trading_start',
                name='Trading Session Start',
                replace_existing=True,
            )

            # Schedule stop
            self.scheduler.add_job(
                self._handle_stop,
                CronTrigger(
                    hour=stop_time.hour,
                    minute=stop_time.minute,
                    timezone=tz,
                ),
                id='trading_stop',
                name='Trading Session Stop',
                replace_existing=True,
            )

            logger.info("Trading schedule configured successfully")

        except Exception as e:
            logger.error(f"Error setting up schedule: {e}")
            raise

    def start(self):
        """Start the scheduler."""
        try:
            if not self.scheduler.running:
                self.scheduler.start()
                logger.info("Scheduler started")

                # Check if we should be trading right now
                if self.is_market_hours():
                    logger.info("Currently within trading hours - starting immediately")
                    self._handle_start()
                else:
                    logger.info("Outside trading hours - waiting for next session")

        except Exception as e:
            logger.error(f"Error starting scheduler: {e}")
            raise

    def stop(self):
        """Stop the scheduler."""
        try:
            if self.scheduler.running:
                self.scheduler.shutdown()
                logger.info("Scheduler stopped")

                # Ensure trading is stopped
                if self.is_trading_time:
                    self._handle_stop()

        except Exception as e:
            logger.error(f"Error stopping scheduler: {e}")

    def _handle_start(self):
        """Handle trading session start."""
        try:
            logger.info("=" * 60)
            logger.info("TRADING SESSION STARTING")
            logger.info("=" * 60)

            self.is_trading_time = True
            self.start_callback()

            logger.info("Trading session started successfully")

        except Exception as e:
            logger.error(f"Error starting trading session: {e}")

    def _handle_stop(self):
        """Handle trading session stop."""
        try:
            logger.info("=" * 60)
            logger.info("TRADING SESSION STOPPING")
            logger.info("=" * 60)

            self.is_trading_time = False
            self.stop_callback()

            logger.info("Trading session stopped successfully")

        except Exception as e:
            logger.error(f"Error stopping trading session: {e}")

    def is_market_hours(self) -> bool:
        """
        Check if current time is within trading hours.

        Returns:
            True if within trading hours
        """
        try:
            tz = settings.get_timezone()
            now = datetime.now(tz).time()
            start_time = settings.get_trading_start_time()
            stop_time = settings.get_trading_end_time()

            return start_time <= now <= stop_time

        except Exception as e:
            logger.error(f"Error checking market hours: {e}")
            return False

    def get_next_run_times(self) -> dict:
        """
        Get next scheduled run times.

        Returns:
            Dictionary with next start and stop times
        """
        try:
            jobs = {job.id: job.next_run_time for job in self.scheduler.get_jobs()}
            return {
                'next_start': jobs.get('trading_start'),
                'next_stop': jobs.get('trading_stop'),
                'is_trading': self.is_trading_time,
            }

        except Exception as e:
            logger.error(f"Error getting next run times: {e}")
            return {}
