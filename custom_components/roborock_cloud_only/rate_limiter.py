"""Rate limiter helper conforming to strict rate limiting rules."""
from __future__ import annotations

from datetime import datetime, timezone, timedelta

from .const import (
    RATE_LIMIT_API_CALLS_PER_HOUR,
    RATE_LIMIT_SAFETY_MARGIN_MINUTES,
    RATE_LIMIT_COMMAND_COOLDOWN_MINUTES,
    RATE_LIMIT_UPDATE_COOLDOWN_MINUTES,
    RATE_LIMIT_SAFETY_MARGIN_CALLS,
)


class RoborockRateLimiter:
    """Tracks API calls and enforces rate limits and dynamic cooldowns."""

    def __init__(self) -> None:
        """Initialize rate limiter with empty call history."""
        self._api_calls: list[datetime] = []
        self._last_command_time: datetime | None = None

    def _clean_old_calls(self, now: datetime) -> None:
        """Remove call timestamps older than the sliding window."""
        window_minutes = 60 + RATE_LIMIT_SAFETY_MARGIN_MINUTES
        cutoff = now - timedelta(minutes=window_minutes)
        self._api_calls = [t for t in self._api_calls if t > cutoff]

    def record_call(self, now: datetime | None = None) -> None:
        """Record a general API call execution time."""
        if now is None:
            now = datetime.now(timezone.utc)
        self._clean_old_calls(now)
        self._api_calls.append(now)

    def can_send_command(self, now: datetime | None = None) -> bool:
        """Check if a triggered command API call is allowed."""
        if now is None:
            now = datetime.now(timezone.utc)
        self._clean_old_calls(now)

        # Check command cooldown
        if self._last_command_time is not None:
            time_since_last_cmd = (now - self._last_command_time).total_seconds() / 60.0
            if time_since_last_cmd < RATE_LIMIT_COMMAND_COOLDOWN_MINUTES:
                return False

        # Check availability limit
        max_calls = RATE_LIMIT_API_CALLS_PER_HOUR - RATE_LIMIT_SAFETY_MARGIN_CALLS
        if len(self._api_calls) >= max_calls:
            return False

        return True

    def record_command(self, now: datetime | None = None) -> None:
        """Record execution of a triggered command."""
        if now is None:
            now = datetime.now(timezone.utc)
        self.record_call(now)
        self._last_command_time = now

    def get_update_cooldown(self, now: datetime | None = None) -> float:
        """Calculate dynamic update cooldown using the specified formula."""
        if now is None:
            now = datetime.now(timezone.utc)
        self._clean_old_calls(now)

        window_minutes = 60 + RATE_LIMIT_SAFETY_MARGIN_MINUTES
        max_calls = RATE_LIMIT_API_CALLS_PER_HOUR - RATE_LIMIT_SAFETY_MARGIN_CALLS
        recent_count = len(self._api_calls)

        count_of_available_calls = max(0, max_calls - recent_count)

        if recent_count >= max_calls and self._api_calls:
            oldest_call = min(self._api_calls)
            age_of_oldest = (now - oldest_call).total_seconds() / 60.0
            minutes_until_available = max(0.0, window_minutes - age_of_oldest)
        else:
            minutes_until_available = 0.0

        denominator = count_of_available_calls + 1
        calculated_cooldown = minutes_until_available / denominator

        update_cooldown = max(calculated_cooldown, RATE_LIMIT_UPDATE_COOLDOWN_MINUTES)
        return update_cooldown