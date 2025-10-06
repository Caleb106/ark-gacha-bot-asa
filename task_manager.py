# task_manager.py
from __future__ import annotations
import heapq, json, time
from pathlib import Path
from threading import Lock

import logs.gachalogs as logs
import settings
import bot.stations as stations

# ---------------- Queues ----------------

class priority_queue_exc:
    def __init__(self):
        self.queue: list[tuple[float, int, int, object]] = []
        self._idx = 0
        self._lock = Lock()

    def add(self, task, priority: int, execution_time: float):
        with self._lock:
            heapq.heappush(self.queue, (float(execution_time), self._idx, int(priority), task))
            self._idx += 1

    def pop_ready(self, now: float):
        out = []
        with self._lock:
            while self.queue and self.queue[0][0] <= now:
                out.append(heapq.heappop(self.queue))
        return out

    def peek(self):
        with self._lock:
            return self.queue[0] if self.queue else None

    def is_empty(self):
        with self._lock:
            return not self.queue


class priority_queue_prio:
    def __init__(self):
        self.queue: list[tuple[int, float, int, object]] = []
        self._idx = 0
        self._lock = Lock()

    def add(self, task, priority: int, enqueue_time: float):
        with self._lock:
            heapq.heappush(self.queue, (int(priority), float(enqueue_time), self._idx, task))
            self._idx += 1

    def pop(self):
        with self._lock:
            if not self.queue:
                return None
            return heapq.heappop(self.queue)

    def peek(self):
        with self._lock:
            return self.queue[0] if self.queue else None

    def is_empty(self):
        with self._lock:
            return not self.queue

# ---------------- Scheduler ----------------

class task_scheduler:
    def __init__(self):
        self.active_queue = priority_queue_prio()
        self.waiting_queue = priority_queue_exc()
        self.prev_task_name = ""

    def add_task(self, task):
        if not getattr(task, "has_run_before", False):
            enqueue = time.time()
        else:
            enqueue = time.time() + int(getattr(task, "get_requeue_delay", lambda: 0)())
        task.has_run_before = True
        self.waiting_queue.add(task, int(getattr(task, "get_priority_level", lambda: 3)()), enqueue)
        logs.logger.debug(f"add_task - added task {getattr(task,'name',type(task).__name__)} to waiting queue")

    def run(self):
        logs.logger.info("main - scheduler running")
        while True:
            now = time.time()

            for exec_time, _, prio, task in self.waiting_queue.pop_ready(now):
                self.active_queue.add(task, prio, exec_time)

            if not self.active_queue.is_empty():
                prio, enq_ts, _, task = self.active_queue.pop()
                if enq_ts <= now:
                    try:
                        if getattr(task, "name", "") != self.prev_task_name:
                            logs.logger.info(f"run - Executing task: {getattr(task,'name',type(task).__name__)}")
                        task.execute()
                    except Exception as e:
                        logs.logger.error(f"Task '{getattr(task,'name',type(task).__name__)}' failed: {e}")
                    self.prev_task_name = getattr(task, "name", "")
                    delay = int(getattr(task, "get_requeue_delay", lambda: 0)())
                    if delay and getattr(task, "name", "") != "pause":
                        self.waiting_queue.add(task, int(getattr(task, "get_priority_level", lambda: 3)()), time.time() + delay)
                else:
                    self.active_queue.add(task, prio, enq_ts)
            else:
                peek = self.waiting_queue.peek()
                if peek:
                    sleep_for = max(0.2, peek[0] - now)
                    time.sleep(min(sleep_for, 10.0))
                else:
                    time.sleep(0.5)

# ---------------- Helpers ----------------

def _load_json_candidates(filename: str):
    roots = [Path.cwd(), Path.cwd() / "json_files", Path(__file__).resolve().parent.parent, Path(__file__).resolve().parent.parent / "json_files"]
    for root in roots:
        p = root / filename
        if p.exists():
            try:
                with open(p, "r", encoding="utf-8") as f:
                    return json.load(f)
            except Exception as e:
                logs.logger.error(f"failed reading {p}: {e}")
                return []
    return []

def _seed_gacha_tasks(sched: task_scheduler) -> int:
    data = _load_json_candidates("gacha.json")
    if not data:
        logs.logger.warning("no gacha.json found or empty")
        return 0
    added = 0
    for entry in data:
        try:
            name = entry["name"]
            tele = entry["teleporter"]
            side = entry["side"]
            resource = entry.get("resource_type", "")
            if resource == "collect":
                depo = entry["depo_tp"]
                task = stations.snail_pheonix(name, tele, side, depo)
            else:
                task = stations.gacha_station(name, tele, side)
            sched.add_task(task)
            added += 1
        except Exception as e:
            logs.logger.error(f"gacha entry add failed: {e}")
    return added

def _seed_pego_tasks(sched: task_scheduler) -> int:
    data = _load_json_candidates("pego.json")
    if not data:
        logs.logger.warning("no pego.json found or empty")
        return 0
    added = 0
    for entry in data:
        try:
            name = entry["name"]
            tele = entry["teleporter"]
            delay = entry["delay"]
            task = stations.pego_station(name, tele, delay)  # match original signature
            sched.add_task(task)
            added += 1
        except Exception as e:
            logs.logger.error(f"pego entry add failed: {e}")
    return added

def _seed_render_task(sched: task_scheduler) -> int:
    try:
        # Keep station wrapper so existing logic works
        task = stations.render_station()
        sched.add_task(task)
        return 1
    except Exception as e:
        logs.logger.error(f"render task add failed: {e}")
        return 0

# ---------------- Entry ----------------

scheduler: task_scheduler | None = None
started = False

def main():
    global scheduler, started
    logs.logger.debug("task_manager_start - task_manager_start initiated")
    scheduler = task_scheduler()

    render_only   = bool(getattr(settings, "render_only", False))
    enable_render = bool(getattr(settings, "enable_render", False))
    enable_gacha  = bool(getattr(settings, "enable_gacha", False))
    enable_pego   = bool(getattr(settings, "enable_pego", False))

    added = 0
    if render_only:
        added += _seed_render_task(scheduler)
    else:
        if enable_gacha:
            added += _seed_gacha_tasks(scheduler)
        if enable_pego:
            added += _seed_pego_tasks(scheduler)
        if enable_render:
            added += _seed_render_task(scheduler)

    if added == 0:
        logs.logger.warning("no tasks queued; check settings and JSON config")

    started = True
    scheduler.run()

if __name__ == "__main__":
    time.sleep(1.0)
    main()
