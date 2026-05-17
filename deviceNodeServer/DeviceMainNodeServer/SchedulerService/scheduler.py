# scheduler.py
import asyncio
import logging
import json
from typing import Dict, Any, List, Optional
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from datetime import datetime, time, timedelta
import pytz
import os

logger = logging.getLogger("scheduler")

WEEKDAY_MAP = {
    'mon': 'mon', 'tue': 'tue', 'wed': 'wed', 'thu': 'thu', 'fri': 'fri', 'sat': 'sat', 'sun': 'sun'
}

POLL_INTERVAL = int(os.getenv("SCHEDULER_DB_POLL_S", "30"))

class SchedulerService:
    def __init__(self, db, mqtt_client, default_tz='UTC'):
        self.db = db
        self.mqtt = mqtt_client
        self.scheduler = AsyncIOScheduler()
        self.default_tz = pytz.timezone(default_tz)
        self.scheduled_job_ids = set()
        # track rule_id -> updated_at for hot reload
        self.rule_versions: Dict[int, Optional[datetime]] = {}
        self._watch_task: Optional[asyncio.Task] = None

    async def start(self):
        logger.info("starting scheduler service")
        await self.db.init()
        self.scheduler.start()
        await self._reset_safe_states()
        await self._load_and_schedule_rules()
        # start DB watch loop
        self._watch_task = asyncio.create_task(self._watch_db_changes())

    async def stop(self):
        logger.info("stopping scheduler service")
        if self._watch_task:
            self._watch_task.cancel()
            try:
                await self._watch_task
            except asyncio.CancelledError:
                pass
        self.scheduler.shutdown(wait=False)
        await self.db.close()

    async def _reset_safe_states(self):
        rows = await self.db.fetch_rules()
        for r in rows:
            safe = r.get('safe_state')
            if safe:
                try:
                    topic = safe.get('topic')
                    payload = safe.get('payload')
                    if topic and payload is not None:
                        logger.info("resetting safe state for rule %s -> %s=%s", r['name'], topic, payload)
                        self._publish_mqtt(topic, payload)
                except Exception as e:
                    logger.exception("failed to apply safe_state for rule %s: %s", r['name'], e)

    async def _load_and_schedule_rules(self):
        rows = await self.db.fetch_rules()
        for r in rows:
            try:
                rule = r['rule_json']
                await self._schedule_rule(r['id'], r['name'], rule)
                self.rule_versions[r['id']] = r.get('updated_at')
            except Exception as e:
                logger.exception("failed to schedule rule %s: %s", r.get('name'), e)

    async def _watch_db_changes(self):
        """
        Periodically poll DB for changes (added/updated/deleted rules).
        On change: remove old jobs for that rule and re-schedule if enabled.
        """
        logger.info("starting DB watch loop (poll interval %s s)", POLL_INTERVAL)
        try:
            while True:
                try:
                    all_rules = await self.db.fetch_all_rules()
                    current_ids = set()
                    for r in all_rules:
                        rid = r['id']
                        current_ids.add(rid)
                        prev = self.rule_versions.get(rid)
                        updated_at = r.get('updated_at')
                        # New rule
                        if prev is None:
                            logger.info("detected new rule id=%s name=%s", rid, r.get('name'))
                            await self._apply_rule_change(r)
                            self.rule_versions[rid] = updated_at
                        # Updated rule
                        elif updated_at and prev and updated_at > prev:
                            logger.info("detected updated rule id=%s name=%s", rid, r.get('name'))
                            await self._apply_rule_change(r)
                            self.rule_versions[rid] = updated_at
                        # unchanged -> nothing
                    # Detect deleted rules (present before, not now)
                    removed = set(self.rule_versions.keys()) - current_ids
                    for rid in removed:
                        logger.info("detected removed rule id=%s, unscheduling", rid)
                        self._unschedule_rule_jobs(rid)
                        self.rule_versions.pop(rid, None)
                except Exception as e:
                    logger.exception("error while watching DB changes: %s", e)
                await asyncio.sleep(POLL_INTERVAL)
        except asyncio.CancelledError:
            logger.info("DB watch loop cancelled")

    async def _apply_rule_change(self, row: Dict[str, Any]):
        """
        Remove existing jobs for the rule, apply safe_state if rule disabled, then schedule if enabled.
        """
        rid = row['id']
        name = row.get('name')
        enabled = bool(row.get('enabled'))
        rule = row.get('rule_json')
        safe = row.get('safe_state')

        # unschedule existing jobs for this rule
        self._unschedule_rule_jobs(rid)

        # if disabled, apply safe_state if present and return
        if not enabled:
            if safe:
                try:
                    topic = safe.get('topic')
                    payload = safe.get('payload')
                    if topic and payload is not None:
                        logger.info("applying safe_state for disabled rule %s -> %s=%s", name, topic, payload)
                        self._publish_mqtt(topic, payload)
                except Exception:
                    logger.exception("failed to apply safe_state for disabled rule %s", name)
            return

        # schedule new rule
        try:
            await self._schedule_rule(rid, name, rule)
            logger.info("re-scheduled rule id=%s name=%s", rid, name)
        except Exception:
            logger.exception("failed to schedule updated rule id=%s name=%s", rid, name)

    def _unschedule_rule_jobs(self, rule_id: int):
        """
        Remove any jobs whose id starts with rule_{rule_id}_
        """
        to_remove = [jid for jid in list(self.scheduled_job_ids) if jid.startswith(f"rule_{rule_id}_")]
        for jid in to_remove:
            try:
                self.scheduler.remove_job(jid)
            except Exception:
                logger.debug("job %s not found when removing", jid)
            self.scheduled_job_ids.discard(jid)
            logger.info("removed scheduled job %s for rule %s", jid, rule_id)

    async def _schedule_rule(self, rule_id: int, name: str, rule: Dict[str, Any]):
        tzname = rule.get('timezone') or 'UTC'
        try:
            tz = pytz.timezone(tzname)
        except Exception:
            tz = self.default_tz

        # seasonal windows
        if 'seasonal' in rule and isinstance(rule['seasonal'], dict):
            for key, window in rule['seasonal'].items():
                months = window.get('months')
                start_time = window.get('start_time')
                end_time = window.get('end_time')
                await self._schedule_time_window(rule_id, name, rule, months, start_time, end_time, tz)
            return

        months = rule.get('months')
        start_time = rule.get('start_time')
        end_time = rule.get('end_time')
        await self._schedule_time_window(rule_id, name, rule, months, start_time, end_time, tz)

    async def _schedule_time_window(self, rule_id, name, rule, months, start_time, end_time, tz):
        weekdays = rule.get('weekdays') or []
        dow = None
        if weekdays:
            dow = ','.join([WEEKDAY_MAP.get(d.lower(), '') for d in weekdays if d.lower() in WEEKDAY_MAP])
            if not dow:
                dow = None

        months_expr = None
        if months:
            months_expr = ','.join(str(int(m)) for m in months)

        topic = rule.get('topic')
        on_payload = rule.get('on_payload') or rule.get('payload_on') or rule.get('on') or 'ON'
        off_payload = rule.get('off_payload') or rule.get('payload_off') or rule.get('off') or 'OFF'
        duration = rule.get('duration_minutes')

        if not start_time:
            logger.warning("rule %s missing start_time, skipping", name)
            return

        hh, mm, ss = [int(x) for x in start_time.split(':')]
        trigger_on = CronTrigger(hour=hh, minute=mm, second=ss, day_of_week=dow, month=months_expr, timezone=tz)
        job_id_on = f"rule_{rule_id}_on_{hh:02d}{mm:02d}_{name}"
        self.scheduler.add_job(self._job_publish, trigger_on, args=[topic, on_payload, name], id=job_id_on, replace_existing=True)
        self.scheduled_job_ids.add(job_id_on)
        logger.info("scheduled ON job %s for rule %s (topic=%s start=%s dow=%s months=%s tz=%s)", job_id_on, name, topic, start_time, dow, months_expr, tz)

        if duration:
            # compute off time (assumes duration < 24h)
            base_dt = datetime.combine(datetime.utcnow().date(), time(hh, mm, ss))
            off_dt = (base_dt + timedelta(minutes=int(duration))).time()
            off_h, off_m, off_s = off_dt.hour, off_dt.minute, off_dt.second
            trigger_off = CronTrigger(hour=off_h, minute=off_m, second=off_s, day_of_week=dow, month=months_expr, timezone=tz)
            job_id_off = f"rule_{rule_id}_off_{off_h:02d}{off_m:02d}_{name}"
            self.scheduler.add_job(self._job_publish, trigger_off, args=[topic, off_payload, name], id=job_id_off, replace_existing=True)
            self.scheduled_job_ids.add(job_id_off)
            logger.info("scheduled OFF job %s for rule %s (topic=%s off_time=%s dow=%s months=%s tz=%s)", job_id_off, name, topic, off_dt.isoformat(), dow, months_expr, tz)
        elif end_time:
            eh, em, es = [int(x) for x in end_time.split(':')]
            trigger_off = CronTrigger(hour=eh, minute=em, second=es, day_of_week=dow, month=months_expr, timezone=tz)
            job_id_off = f"rule_{rule_id}_off_{eh:02d}{em:02d}_{name}"
            self.scheduler.add_job(self._job_publish, trigger_off, args=[topic, off_payload, name], id=job_id_off, replace_existing=True)
            self.scheduled_job_ids.add(job_id_off)
            logger.info("scheduled OFF job %s for rule %s (topic=%s end_time=%s dow=%s months=%s tz=%s)", job_id_off, name, topic, end_time, dow, months_expr, tz)

    def _publish_mqtt(self, topic: str, payload: str):
        try:
            logger.debug("publishing mqtt %s -> %s", topic, payload)
            self.mqtt.publish(topic, payload)
        except Exception:
            logger.exception("mqtt publish failed for %s", topic)

    def _job_publish(self, topic: str, payload: str, rule_name: str):
        logger.info("job firing for rule %s: publish %s -> %s", rule_name, topic, payload)
        self._publish_mqtt(topic, payload)
