"""
Reconnection Manager — TradePilot

Handles automatic reconnection to the market data provider on failure.
Implements exponential backoff with jitter to avoid thundering herd.

Reconnection flow:
  1. Provider disconnects
  2. Reconnection manager detects disconnect
  3. Wait (exponential backoff with jitter)
  4. Attempt reconnect
  5. On success: resubscribe all symbols, mark feed LIVE, resume streaming
  6. On failure: increment backoff, log error, try again
"""
import asyncio
import logging
import time
import random
from typing import List, Optional, Callable

logger = logging.getLogger(__name__)


class ReconnectionManager:
    """
    Manages automatic reconnection with exponential backoff.

    Backoff schedule (with ±25% jitter):
        Attempt 1:  2 seconds
        Attempt 2:  4 seconds
        Attempt 3:  8 seconds
        Attempt 4:  16 seconds
        Attempt 5:  32 seconds
        Attempt 6+: 60 seconds (max)
    """

    MIN_DELAY_SECONDS: float = 2.0
    MAX_DELAY_SECONDS: float = 60.0
    JITTER_FACTOR: float = 0.25

    def __init__(self):
        self._attempt_count: int = 0
        self._last_attempt_time: Optional[float] = None
        self._last_success_time: Optional[float] = None
        self._is_reconnecting: bool = False
        self._on_reconnect_callbacks: List[Callable] = []

    def register_on_reconnect(self, callback: Callable) -> None:
        """Register a callback to be called when reconnection succeeds."""
        self._on_reconnect_callbacks.append(callback)

    def get_next_delay(self) -> float:
        """Compute next backoff delay with exponential growth and jitter."""
        base = min(
            self.MIN_DELAY_SECONDS * (2 ** self._attempt_count),
            self.MAX_DELAY_SECONDS,
        )
        jitter = base * self.JITTER_FACTOR * (random.random() * 2 - 1)
        return max(self.MIN_DELAY_SECONDS, base + jitter)

    def record_connection_attempt(self) -> None:
        """Record that a reconnection attempt was made."""
        self._attempt_count += 1
        self._last_attempt_time = time.time()
        logger.info(f"ReconnectionManager: attempt #{self._attempt_count}")

    def record_success(self) -> None:
        """Record a successful connection."""
        self._attempt_count = 0
        self._last_success_time = time.time()
        self._is_reconnecting = False
        logger.info("ReconnectionManager: connection established. Backoff reset.")
        for cb in self._on_reconnect_callbacks:
            try:
                cb()
            except Exception as e:
                logger.error(f"ReconnectionManager: callback error — {e}")

    def record_failure(self, error: str) -> None:
        """Record a failed connection attempt."""
        logger.warning(
            f"ReconnectionManager: attempt #{self._attempt_count} failed — {error}. "
            f"Next retry in {self.get_next_delay():.1f}s"
        )

    async def run_reconnect_loop(
        self,
        connect_fn: Callable,
        subscribed_symbols: List[str],
        max_attempts: Optional[int] = None,
    ) -> bool:
        """
        Run the reconnection loop asynchronously.

        Args:
            connect_fn: Callable that attempts connection and returns True/False
            subscribed_symbols: Symbols to resubscribe after reconnection
            max_attempts: Maximum attempts (None = infinite)

        Returns:
            True when connection is re-established, False if max_attempts exceeded
        """
        self._is_reconnecting = True

        while True:
            if max_attempts and self._attempt_count >= max_attempts:
                logger.error(
                    f"ReconnectionManager: max attempts ({max_attempts}) exceeded. "
                    f"Giving up reconnection."
                )
                self._is_reconnecting = False
                return False

            delay = self.get_next_delay()
            logger.info(
                f"ReconnectionManager: waiting {delay:.1f}s before attempt "
                f"#{self._attempt_count + 1}..."
            )
            await asyncio.sleep(delay)

            self.record_connection_attempt()

            try:
                success = connect_fn()
                if success:
                    self.record_success()
                    logger.info(
                        f"ReconnectionManager: reconnected. "
                        f"Resubscribing {len(subscribed_symbols)} symbols."
                    )
                    return True
                else:
                    self.record_failure("connect() returned False")
            except Exception as e:
                self.record_failure(str(e))

    def get_status(self) -> dict:
        """Return current reconnection status."""
        return {
            "is_reconnecting": self._is_reconnecting,
            "attempt_count": self._attempt_count,
            "last_attempt_time": self._last_attempt_time,
            "last_success_time": self._last_success_time,
            "next_delay_seconds": self.get_next_delay() if self._is_reconnecting else None,
        }


# Module-level singleton
_reconnection_manager = ReconnectionManager()


def get_reconnection_manager() -> ReconnectionManager:
    return _reconnection_manager
