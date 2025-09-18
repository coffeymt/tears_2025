"""CLI to import legacy JSON exports from Google Cloud Storage into the app DB.

This script provides a simple, idempotent, dry-run-capable scaffold. It does NOT
automatically run in CI — run locally with credentials set via environment or
with Google Application Default Credentials.

Usage examples:
  python scripts/import_from_gcs.py --bucket my-bucket --files teams.json,users.json --dry-run

If you run without `--dry-run`, the script will attempt to write to the database
using the application's `app.db` session. Use with care.
"""
from __future__ import annotations

import argparse
import json
import logging
import os
from typing import Iterable

from google.cloud import storage
from sqlalchemy.exc import IntegrityError

# Import DB session and models lazily when needed to avoid side-effects on import
def _import_db():
    from app.db import SessionLocal
    from app.models.team import Team
    from app.models.user import User
    return SessionLocal, Team, User

# Local imports kept lazy to avoid side effects on import


def make_gcs_client():
    # The google-cloud-storage client will pick up ADC or use credentials from
    # GOOGLE_APPLICATION_CREDENTIALS env var if set.
    return storage.Client()


def download_blob_to_text(client: storage.Client, bucket_name: str, blob_name: str) -> str:
    bucket = client.bucket(bucket_name)
    blob = bucket.blob(blob_name)
    return blob.download_as_text()


def parse_json_text(text: str):
    return json.loads(text)


def process_teams(data: Iterable[dict], dry_run: bool = True) -> dict:
    """Process teams list JSON objects. Returns summary dict."""
    created = 0
    updated = 0

    SessionLocal, Team, _ = _import_db()

    for obj in data:
        # basic validation
        abbr = obj.get("abbreviation")
        name = obj.get("name")
        if not abbr or not name:
            logging.warning("Skipping malformed team record: %s", obj)
            continue

        if dry_run:
            logging.info("DRY-RUN: Would upsert team %s (%s)", name, abbr)
            created += 1
            continue

        db = SessionLocal()
        try:
            existing = db.query(Team).filter(Team.abbreviation == abbr).one_or_none()
            if existing:
                # naive update of mutable fields
                if existing.name != name:
                    existing.name = name
                    db.add(existing)
                    db.commit()
                    updated += 1
                else:
                    # nothing to change
                    pass
            else:
                t = Team(abbreviation=abbr, name=name, city=obj.get("city"), conference=obj.get("conference"), division=obj.get("division"))
                db.add(t)
                db.commit()
                created += 1
        except Exception:
            db.rollback()
            logging.exception("Failed to upsert team %s", abbr)
        finally:
            db.close()

    return {"created": created, "updated": updated}


def process_users(data: Iterable[dict], dry_run: bool = True) -> dict:
    created = 0
    updated = 0

    SessionLocal, _, User = _import_db()

    for obj in data:
        email = obj.get("email")
        if not email:
            logging.warning("Skipping malformed user record: %s", obj)
            continue

        first_name = obj.get("first_name") or obj.get("firstName") or obj.get("given_name")
        last_name = obj.get("last_name") or obj.get("lastName") or obj.get("family_name")
        phone = obj.get("phone") or obj.get("phone_number")

        if dry_run:
            logging.info("DRY-RUN: Would upsert user %s (first=%s last=%s phone=%s)", email, first_name, last_name, phone)
            created += 1
            continue

        db = SessionLocal()
        try:
            existing = db.query(User).filter(User.email == email).one_or_none()
            if existing:
                changed = False
                if first_name and existing.first_name != first_name:
                    existing.first_name = first_name
                    changed = True
                if last_name and existing.last_name != last_name:
                    existing.last_name = last_name
                    changed = True
                if phone and existing.phone_number != phone:
                    existing.phone_number = phone
                    changed = True
                if changed:
                    db.add(existing)
                    db.commit()
                    updated += 1
            else:
                u = User(email=email, hashed_password=obj.get("hashed_password") or "", first_name=first_name, last_name=last_name, phone_number=phone)
                db.add(u)
                db.commit()
                created += 1
        except IntegrityError:
            db.rollback()
            logging.exception("Integrity error upserting user %s", email)
        except Exception:
            db.rollback()
            logging.exception("Failed to upsert user %s", email)
        finally:
            db.close()

    return {"created": created, "updated": updated}


def _parse_iso_to_utc(dt_str: str):
    """Parse various ISO-like strings to a timezone-aware UTC datetime.
    Returns None on parse failure.
    """
    from datetime import datetime, timezone
    if not dt_str:
        return None
    try:
        # Let Python parse common ISO formats; fallback to simple fromisoformat
        dt = datetime.fromisoformat(dt_str)
    except Exception:
        try:
            # Some strings may end with Z
            if dt_str.endswith("Z"):
                dt = datetime.fromisoformat(dt_str.replace("Z", "+00:00"))
            else:
                return None
        except Exception:
            return None

    # Ensure timezone-aware and converted to UTC
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(timezone.utc).replace(tzinfo=None)


def process_weeks(data: Iterable[dict], dry_run: bool = True) -> dict:
    created = 0
    updated = 0
    SessionLocal, Week, _ = None, None, None
    # lazy import of Week model
    try:
        from app.db import SessionLocal as _SessionLocal
        from app.models.week import Week
        SessionLocal = _SessionLocal
    except Exception:
        logging.exception("Failed to import Week model -- are app packages available?")
        return {"error": "import_failed"}

    for obj in data:
        season = obj.get("season_year") or obj.get("season")
        week_number = obj.get("week_number") or obj.get("week")
        if season is None or week_number is None:
            logging.warning("Skipping malformed week record: %s", obj)
            continue

        lock_time_raw = obj.get("lock_time") or obj.get("lockTime")
        lock_time = _parse_iso_to_utc(lock_time_raw)

        if dry_run:
            logging.info("DRY-RUN: Would upsert week season=%s week=%s lock_time=%s", season, week_number, lock_time)
            created += 1
            continue

        db = SessionLocal()
        try:
            existing = db.query(Week).filter(Week.season_year == season, Week.week_number == week_number).one_or_none()
            if existing:
                changed = False
                if lock_time and existing.lock_time != lock_time:
                    existing.lock_time = lock_time
                    changed = True
                if changed:
                    db.add(existing)
                    db.commit()
                    updated += 1
            else:
                w = Week(season_year=season, week_number=week_number, is_current=obj.get("is_current", False), lock_time=lock_time)
                db.add(w)
                db.commit()
                created += 1
        except Exception:
            db.rollback()
            logging.exception("Failed to upsert week %s-%s", season, week_number)
        finally:
            db.close()

    return {"created": created, "updated": updated}


def process_games(data: Iterable[dict], dry_run: bool = True) -> dict:
    created = 0
    updated = 0

    # Lazy import models
    try:
        from app.db import SessionLocal as _SessionLocal
        from app.models.game import Game
        from app.models.team import Team
        from app.models.week import Week
        SessionLocal = _SessionLocal
    except Exception:
        logging.exception("Failed to import Game/Team/Week models -- are app packages available?")
        return {"error": "import_failed"}

    for obj in data:
        # Expect fields: season_year, week_number, start_time, home_abbr, away_abbr
        season = obj.get("season_year") or obj.get("season")
        week_number = obj.get("week_number") or obj.get("week")
        if season is None or week_number is None:
            logging.warning("Skipping malformed game record (missing season/week): %s", obj)
            continue

        start_time = _parse_iso_to_utc(obj.get("start_time") or obj.get("startTime"))
        home_abbr = obj.get("home_team_abbr") or obj.get("home_abbr")
        away_abbr = obj.get("away_team_abbr") or obj.get("away_abbr")
        if not home_abbr or not away_abbr or not start_time:
            logging.warning("Skipping malformed game record (missing team or time): %s", obj)
            continue

        if dry_run:
            logging.info("DRY-RUN: Would upsert game %s vs %s at %s (season=%s week=%s)", home_abbr, away_abbr, start_time, season, week_number)
            created += 1
            continue

        db = SessionLocal()
        try:
            # Resolve week id
            week = db.query(Week).filter(Week.season_year == season, Week.week_number == week_number).one_or_none()
            if not week:
                logging.warning("Week not found for game: season=%s week=%s", season, week_number)
                continue

            # Resolve team ids
            home_team = db.query(Team).filter(Team.abbreviation == home_abbr).one_or_none()
            away_team = db.query(Team).filter(Team.abbreviation == away_abbr).one_or_none()

            g = db.query(Game).filter(Game.week_id == week.id, Game.start_time == start_time, Game.home_team_abbr == home_abbr, Game.away_team_abbr == away_abbr).one_or_none()
            if g:
                changed = False
                if g.start_time != start_time:
                    g.start_time = start_time
                    changed = True
                if home_team and g.home_team_id != home_team.id:
                    g.home_team_id = home_team.id
                    changed = True
                if away_team and g.away_team_id != away_team.id:
                    g.away_team_id = away_team.id
                    changed = True
                if changed:
                    db.add(g)
                    db.commit()
                    updated += 1
            else:
                newg = Game(week_id=week.id, start_time=start_time, home_team_abbr=home_abbr, away_team_abbr=away_abbr, home_team_id=(home_team.id if home_team else None), away_team_id=(away_team.id if away_team else None), status=obj.get("status", "scheduled"))
                db.add(newg)
                db.commit()
                created += 1
        except Exception:
            db.rollback()
            logging.exception("Failed to upsert game: %s", obj)
        finally:
            db.close()

    return {"created": created, "updated": updated}


def process_entries(data: Iterable[dict], dry_run: bool = True) -> dict:
    """Process entries.json which links users and weeks."""
    created = 0
    updated = 0

    # lazy imports
    try:
        from app.db import SessionLocal as _SessionLocal
        from app.models.entry import Entry
        from app.models.user import User
        from app.models.week import Week
        SessionLocal = _SessionLocal
    except Exception:
        logging.exception("Failed to import Entry/User/Week models -- are app packages available?")
        return {"error": "import_failed"}

    for obj in data:
        # expected fields: user_email, season_year, week_number, name, picks (json)
        user_email = obj.get("user_email") or obj.get("email")
        season = obj.get("season_year") or obj.get("season")
        week_number = obj.get("week_number") or obj.get("week")
        name = obj.get("name") or obj.get("entry_name")
        picks = obj.get("picks")

        if not user_email or season is None or week_number is None or not name:
            logging.warning("Skipping malformed entry record: %s", obj)
            continue

        if dry_run:
            logging.info("DRY-RUN: Would upsert entry %s for user %s season=%s week=%s", name, user_email, season, week_number)
            created += 1
            continue

        db = SessionLocal()
        try:
            user = db.query(User).filter(User.email == user_email).one_or_none()
            if not user:
                logging.warning("User not found for entry: %s", user_email)
                continue

            week = db.query(Week).filter(Week.season_year == season, Week.week_number == week_number).one_or_none()
            if not week:
                logging.warning("Week not found for entry: season=%s week=%s", season, week_number)
                continue

            existing = db.query(Entry).filter(Entry.user_id == user.id, Entry.season_year == season, Entry.name == name).one_or_none()
            if existing:
                changed = False
                if picks is not None and existing.picks != picks:
                    existing.picks = picks
                    changed = True
                if changed:
                    db.add(existing)
                    db.commit()
                    updated += 1
            else:
                e = Entry(user_id=user.id, week_id=week.id, name=name, season_year=season, picks=picks or [], is_eliminated=obj.get("is_eliminated", False), is_paid=obj.get("is_paid", False))
                db.add(e)
                db.commit()
                created += 1
        except Exception:
            db.rollback()
            logging.exception("Failed to upsert entry: %s", obj)
        finally:
            db.close()

    return {"created": created, "updated": updated}


def process_picks(data: Iterable[dict], dry_run: bool = True) -> dict:
    """Process picks.json linking entries, weeks, and teams/games."""
    created = 0
    updated = 0

    try:
        from app.db import SessionLocal as _SessionLocal
        from app.models.pick import Pick
        from app.models.entry import Entry
        from app.models.week import Week
        from app.models.team import Team
        from app.models.game import Game
        from app.models.user import User
        SessionLocal = _SessionLocal
    except Exception:
        logging.exception("Failed to import Pick/Entry/Week/Team/Game models -- are app packages available?")
        return {"error": "import_failed"}

    for obj in data:
        # expected: entry_name or entry_id, user_email, season_year, week_number, team_abbr or team_id
        entry_name = obj.get("entry_name")
        entry_id = obj.get("entry_id")
        user_email = obj.get("user_email") or obj.get("email")
        season = obj.get("season_year") or obj.get("season")
        week_number = obj.get("week_number") or obj.get("week")
        team_abbr = obj.get("team_abbr") or obj.get("team")

        if season is None or week_number is None or (not entry_id and not (entry_name and user_email)):
            logging.warning("Skipping malformed pick record: %s", obj)
            continue

        if dry_run:
            logging.info("DRY-RUN: Would upsert pick for entry=%s user=%s season=%s week=%s team=%s", entry_id or entry_name, user_email, season, week_number, team_abbr)
            created += 1
            continue

        db = SessionLocal()
        try:
            # resolve entry
            entry = None
            if entry_id:
                entry = db.query(Entry).filter(Entry.id == entry_id).one_or_none()
            else:
                user = db.query(User).filter(User.email == user_email).one_or_none()
                if user:
                    entry = db.query(Entry).filter(Entry.user_id == user.id, Entry.season_year == season, Entry.name == entry_name).one_or_none()

            if not entry:
                logging.warning("Entry not found for pick: %s", obj)
                continue

            week = db.query(Week).filter(Week.season_year == season, Week.week_number == week_number).one_or_none()
            if not week:
                logging.warning("Week not found for pick: season=%s week=%s", season, week_number)
                continue

            # resolve team
            team = None
            if team_abbr:
                team = db.query(Team).filter(Team.abbreviation == team_abbr).one_or_none()

            existing = db.query(Pick).filter(Pick.entry_id == entry.id, Pick.week_id == week.id).one_or_none()
            if existing:
                changed = False
                if team and existing.team_id != team.id:
                    existing.team_id = team.id
                    existing.team_abbr = team_abbr
                    changed = True
                if changed:
                    db.add(existing)
                    db.commit()
                    updated += 1
            else:
                p = Pick(entry_id=entry.id, week_id=week.id, team_id=(team.id if team else None), team_abbr=team_abbr)
                db.add(p)
                db.commit()
                created += 1
        except Exception:
            db.rollback()
            logging.exception("Failed to upsert pick: %s", obj)
        finally:
            db.close()

    return {"created": created, "updated": updated}


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Import legacy JSON exports from GCS")
    parser.add_argument("--bucket", required=True, help="GCS bucket name")
    parser.add_argument("--files", required=True, help="Comma-separated list of file names to import (e.g. teams.json,users.json)")
    parser.add_argument("--dry-run", action="store_true", help="Do not persist changes; only show summary")
    parser.add_argument("--verbose", action="store_true", help="Enable debug logging")

    args = parser.parse_args(argv)

    logging.basicConfig(level=logging.DEBUG if args.verbose else logging.INFO)

    client = make_gcs_client()

    summary = {}
    for fname in [f.strip() for f in args.files.split(",") if f.strip()]:
        logging.info("Downloading %s from bucket %s", fname, args.bucket)
        try:
            text = download_blob_to_text(client, args.bucket, fname)
        except Exception as exc:  # network/auth errors surface here
            logging.error("Failed to download %s: %s", fname, exc)
            summary[fname] = {"error": str(exc)}
            continue

        try:
            data = parse_json_text(text)
        except Exception as exc:
            logging.error("Failed to parse JSON for %s: %s", fname, exc)
            summary[fname] = {"error": "invalid_json"}
            continue

        # Dispatch by file name prefix
        if fname.lower().startswith("teams"):
            summary[fname] = process_teams(data, dry_run=args.dry_run)
        elif fname.lower().startswith("users"):
            summary[fname] = process_users(data, dry_run=args.dry_run)
        elif fname.lower().startswith("weeks"):
            summary[fname] = process_weeks(data, dry_run=args.dry_run)
        elif fname.lower().startswith("games"):
            summary[fname] = process_games(data, dry_run=args.dry_run)
        elif fname.lower().startswith("entries"):
            summary[fname] = process_entries(data, dry_run=args.dry_run)
        elif fname.lower().startswith("picks"):
            summary[fname] = process_picks(data, dry_run=args.dry_run)
        else:
            logging.warning("No handler for %s; skipping", fname)
            summary[fname] = {"skipped": True}

    logging.info("Import summary: %s", summary)
    if args.dry_run:
        logging.info("Dry-run mode: no DB changes were made")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
