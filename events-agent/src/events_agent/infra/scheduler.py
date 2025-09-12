from __future__ import annotations

import asyncio
from datetime import datetime, timezone
from typing import Optional

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.interval import IntervalTrigger
from sqlalchemy import select, update

from .db import session_scope
from ..domain.models import Reminder
from .metrics import reminders_sent_total
from .logging import get_logger


logger = get_logger().bind(service="scheduler")


async def _process_due_reminders() -> None:
    now = datetime.now(timezone.utc)
    async with session_scope() as session:
        res = await session.execute(select(Reminder).where(Reminder.sent == False, Reminder.remind_at <= now))
        due = res.scalars().all()
        for r in due:
            try:
                # Placeholder: in real flow, post to Discord DM or channel
                logger.info("reminder_due", user_id=r.user_id, event_id=r.event_id)
                await session.execute(
                    update(Reminder)
                    .where(Reminder.id == r.id)
                    .values(sent=True, retries=r.retries)
                )
                await session.commit()
                reminders_sent_total.inc()
            except Exception as e:
                logger.warning("reminder_send_failed", reminder_id=r.id, error=str(e))


def start_scheduler() -> AsyncIOScheduler:
    scheduler = AsyncIOScheduler()
    scheduler.add_job(_process_due_reminders, IntervalTrigger(seconds=60))
    scheduler.start()
    return scheduler


