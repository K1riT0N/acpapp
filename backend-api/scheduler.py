"""Background jobs, run every 30 seconds by APScheduler inside the API process.

app.py starts the scheduler when the API starts and stops it on shutdown. uvicorn runs with ONE
worker, so the jobs run once; with several workers each would start its own copy.

The rules never depend on these jobs having run: an expired hold already stops counting the moment
its time passes (see core/status.py). The jobs tidy the data and send scheduled messages.
"""
import logging

from apscheduler.schedulers.background import BackgroundScheduler

from core.bookings import expire_holds
from core.notify import send_due
from core.plans import expire_pro_subscriptions
from database import SessionLocal

log = logging.getLogger("nadd.scheduler")
INTERVAL_SECONDS = 30


def run_jobs() -> None:
    """One round of all three jobs, in one transaction."""
    with SessionLocal() as db:
        try:
            expired = expire_holds(db)
            sent = send_due(db)
            subs = expire_pro_subscriptions(db)
            db.commit()
            if expired or sent or subs:
                log.info("jobs: %d holds expired, %d messages sent, %d Pro plans ended", expired, sent, subs)
        except Exception:
            db.rollback()
            log.exception("background jobs failed; will try again next round")


def start() -> BackgroundScheduler:
    scheduler = BackgroundScheduler(timezone="Asia/Bangkok")
    # coalesce + max_instances=1: if a round is slow, don't pile up overlapping runs
    scheduler.add_job(run_jobs, "interval", seconds=INTERVAL_SECONDS, id="nadd-jobs",
                      coalesce=True, max_instances=1)
    scheduler.start()
    run_jobs()  # catch up once right away, for example after the API was stopped for a while
    return scheduler
