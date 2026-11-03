from datetime import datetime, timedelta, timezone


def now_iso() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def story_cutoff_iso() -> str:
    cutoff = datetime.now(timezone.utc) - timedelta(hours=24)
    return cutoff.strftime("%Y-%m-%dT%H:%M:%SZ")
