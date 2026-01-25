"""
Background flight monitoring service for FlightFinder.

This module provides a continuous monitoring service that checks price alerts
and sends notifications to Discord. Designed to run on Fly.io or any
container platform.

Usage:
    python -m flightfinder.monitor

Environment Variables:
    DISCORD_WEBHOOK_URL: Discord webhook URL (required)
    MONITOR_INTERVAL: Check interval in seconds (default: 300)
    MONITOR_DAYS_AHEAD: Days from now to search (default: 30)
    FLIGHTFINDER_ALERTS: JSON array of alert configurations

Example alert config:
    [
        {"origin": "SFO", "destination": "anywhere", "max_price": 300},
        {"origin": "SFO", "destination": "HNL", "max_price": 250, "round_trip": true}
    ]
"""

import json
import logging
import os
import signal
import sys
import time
from datetime import datetime, timedelta

from flightfinder.alerts import AlertMatch, DealAlertManager, PriceAlert
from flightfinder.config import get_config
from flightfinder.discord import DiscordNotifier

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)],
)
logger = logging.getLogger(__name__)


class FlightMonitor:
    """
    Continuous flight monitoring service.

    Periodically checks price alerts and sends matching deals to Discord.
    """

    def __init__(
        self,
        webhook_url: str | None = None,
        interval_seconds: int = 300,
        days_ahead: int = 30,
        search_window: int = 14,
        heartbeat_interval: int = 3600,
    ):
        """
        Initialize the flight monitor.

        Args:
            webhook_url: Discord webhook URL. Falls back to env var if not provided.
            interval_seconds: Seconds between alert checks (default: 5 minutes)
            days_ahead: Days from now to start searching (default: 30)
            search_window: Search window in days (default: 14)
            heartbeat_interval: Seconds between heartbeat messages (default: 1 hour)
        """
        self.webhook_url = webhook_url or os.getenv("DISCORD_WEBHOOK_URL", "")
        self.interval_seconds = interval_seconds
        self.days_ahead = days_ahead
        self.search_window = search_window
        self.heartbeat_interval = heartbeat_interval

        self._running = False
        self._last_heartbeat = datetime.min
        self._alert_manager: DealAlertManager | None = None
        self._notifier: DiscordNotifier | None = None

        # Load alerts from environment or config
        self._load_alerts_from_env()

    def _load_alerts_from_env(self) -> None:
        """Load alerts from environment variable if present."""
        alerts_json = os.getenv("FLIGHTFINDER_ALERTS")
        if alerts_json:
            try:
                alerts_data = json.loads(alerts_json)
                self._env_alerts = [PriceAlert.from_dict(a) for a in alerts_data]
                logger.info(f"Loaded {len(self._env_alerts)} alerts from environment")
            except Exception as e:
                logger.error(f"Failed to parse FLIGHTFINDER_ALERTS: {e}")
                self._env_alerts = []
        else:
            self._env_alerts = []

    @property
    def alert_manager(self) -> DealAlertManager:
        """Get or create the alert manager."""
        if self._alert_manager is None:
            self._alert_manager = DealAlertManager()

            # Add env alerts if file alerts are empty
            if not self._alert_manager.alerts and self._env_alerts:
                for alert in self._env_alerts:
                    self._alert_manager.alerts.append(alert)
                logger.info(f"Using {len(self._env_alerts)} alerts from environment")

            # Set up Discord callback
            self._alert_manager.on_match = self._on_alert_match

        return self._alert_manager

    @property
    def notifier(self) -> DiscordNotifier:
        """Get or create the Discord notifier."""
        if self._notifier is None:
            if not self.webhook_url:
                raise ValueError("Discord webhook URL not configured")
            self._notifier = DiscordNotifier(webhook_url=self.webhook_url)
        return self._notifier

    def _on_alert_match(self, match: AlertMatch) -> None:
        """Callback when an alert matches a flight."""
        logger.info(
            f"Deal found: {match.alert.origin} → {match.flight.destination} "
            f"${match.flight.price:.0f} (${match.price_delta:.0f} below target)"
        )
        try:
            self.notifier.send_deal_alert(match)
        except Exception as e:
            logger.error(f"Failed to send deal alert to Discord: {e}")

    def _send_heartbeat(self) -> None:
        """Send periodic heartbeat to Discord."""
        now = datetime.now()
        if (now - self._last_heartbeat).total_seconds() >= self.heartbeat_interval:
            try:
                alerts = self.alert_manager.alerts
                next_check = now + timedelta(seconds=self.interval_seconds)

                self.notifier.send_monitoring_status(
                    alerts=alerts,
                    last_check=now,
                    next_check=next_check,
                    matches_found=0,  # Reset per heartbeat period
                )
                self._last_heartbeat = now
                logger.info("Sent heartbeat to Discord")
            except Exception as e:
                logger.error(f"Failed to send heartbeat: {e}")

    def _check_alerts(self) -> int:
        """Check all alerts and return number of matches."""
        logger.info("Checking alerts...")

        try:
            matches = self.alert_manager.check_alerts(
                days_ahead=self.days_ahead,
                window=self.search_window,
            )
            logger.info(f"Found {len(matches)} matching deals")
            return len(matches)
        except Exception as e:
            logger.error(f"Error checking alerts: {e}")
            return 0

    def start(self) -> None:
        """Start the monitoring loop."""
        if not self.webhook_url:
            logger.error("Discord webhook URL not configured. Set DISCORD_WEBHOOK_URL env var.")
            sys.exit(1)

        if not self.alert_manager.alerts:
            logger.warning("No alerts configured. Set FLIGHTFINDER_ALERTS env var or add alerts to ~/.flightfinder/alerts.json")

        logger.info("Starting FlightFinder monitor...")
        logger.info(f"  Webhook: {self.webhook_url[:50]}...")
        logger.info(f"  Interval: {self.interval_seconds}s")
        logger.info(f"  Alerts: {len(self.alert_manager.alerts)}")

        # Send startup message
        try:
            self.notifier.send_heartbeat(
                f"FlightFinder monitor started! Monitoring {len(self.alert_manager.alerts)} alerts, "
                f"checking every {self.interval_seconds // 60} minutes."
            )
        except Exception as e:
            logger.error(f"Failed to send startup message: {e}")

        self._running = True
        self._last_heartbeat = datetime.now()

        # Set up signal handlers for graceful shutdown
        signal.signal(signal.SIGINT, self._handle_shutdown)
        signal.signal(signal.SIGTERM, self._handle_shutdown)

        # Main loop
        while self._running:
            try:
                self._check_alerts()
                self._send_heartbeat()
            except Exception as e:
                logger.error(f"Error in monitoring loop: {e}")

            # Sleep in small increments to allow for graceful shutdown
            for _ in range(self.interval_seconds):
                if not self._running:
                    break
                time.sleep(1)

        self._cleanup()

    def _handle_shutdown(self, signum, frame) -> None:
        """Handle shutdown signals."""
        logger.info(f"Received signal {signum}, shutting down...")
        self._running = False

    def _cleanup(self) -> None:
        """Clean up resources."""
        logger.info("Cleaning up...")

        try:
            self.notifier.send_heartbeat("FlightFinder monitor shutting down.")
        except Exception:
            pass

        if self._notifier:
            self._notifier.close()
        if self._alert_manager:
            self._alert_manager.close()

        logger.info("Monitor stopped.")

    def stop(self) -> None:
        """Stop the monitoring loop."""
        self._running = False


def main():
    """Main entry point for the monitor."""
    # Load config
    config = get_config()

    # Get settings from config or environment
    webhook_url = config.discord.webhook_url or os.getenv("DISCORD_WEBHOOK_URL")
    interval = int(os.getenv("MONITOR_INTERVAL", config.monitor.interval_seconds))
    days_ahead = int(os.getenv("MONITOR_DAYS_AHEAD", config.monitor.days_ahead))
    search_window = int(os.getenv("MONITOR_SEARCH_WINDOW", config.monitor.search_window))
    heartbeat_interval = int(os.getenv("MONITOR_HEARTBEAT_INTERVAL", config.monitor.heartbeat_interval))

    monitor = FlightMonitor(
        webhook_url=webhook_url,
        interval_seconds=interval,
        days_ahead=days_ahead,
        search_window=search_window,
        heartbeat_interval=heartbeat_interval,
    )

    monitor.start()


if __name__ == "__main__":
    main()
