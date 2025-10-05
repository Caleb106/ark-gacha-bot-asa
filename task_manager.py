from __future__ import annotations
import heapq, json, os, sys, time
from pathlib import Path
from threading import Lock
import logs.gachalogs as logs

# resolve paths and import settings robustly
HERE = Path(__file__).resolve().parent
for p in (HERE, HERE.parent):
    s = str(p)
    if s not in sys.path:
        sys.path.insert(0, s)
import settings  # type: ignore

# optional render route runner
try:
    from bot import render_route
    _HAS_RENDER_ROUTE = True
except Exception:
    _HAS_RENDER_ROUTE = False

# -------- activity feed --------
class _Activity:
    def __init__(self, maxlen=200):
        self._buf = []
        self._mx = int(maxlen)
        self._lock = Lock()
    def add(self, s: str):
        with self._lock:
            ts = time.strftime("%H:%M:%S")
            self._buf.append(f"[{ts}] {s}")
            if len(self._buf) > self._mx:
                self._buf = self._buf[-self._mx:]
    def tail(self, n: int):
        with self._lock:
            return self._buf[-n:]

EVENT_LOG = _Activity()

# -------- queues --------
class priority_queue_exc:
    def __init__(self):
        self.queue: list[tuple[float,int,int,Task]] = []
        self._counter = 0
        self._lock = Lock()
    def add(self, task: "Task", priority: int, execution_time: float):
        with self._lock:
            heapq.heappush(self.queue, (float(execution_time), self._counter, int(priority), task))
            self._counter += 1
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
        self.queue: list[tuple[int,float,int,Task]] = []
        self._counter = 0
        self._lock = Lock()
    def add(self, task: "Task", priority: int, enqueue_time: float):
        with self._lock:
            heapq.heappush(self.queue, (int(priority), float(enqueue_time), self._counter, task))
            self._counter += 1
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

# -------- task base --------
class Task:
    name: str = "task"
    def __init__(self, priority: int = 3, interval_s: int = 0):
        self._priority = int(priority)
        self._interval_s = int(interval_s)
        self.has_run_before = False
    def execute(self):  # override
        raise NotImplementedError
    def get_requeue_delay(self) -> int:
        return max(0, self._interval_s)
    def get_priority_level(self) -> int:
        return self._priority

# -------- render task --------
class RenderRouteTask(Task):
    """One full render pass; returns to bed and rests; then requeues itself."""
    def __init__(self, route_json: str = "render_route.json", dwell_s: int | None = None, priority: int | None = None):
        dwell = dwell_s if dwell_s is not None else getattr(settings, "render_dwell_seconds", 25)
        prio  = priority if priority is not None else getattr(settings, "render_priority", 3)
        super().__init__(priority=int(prio), interval_s=int(getattr(settings, "render_rest_seconds", 2700)))
        self.name = "render"
        self._route_json = route_json
        self._dwell = int(dwell)

    def _load_route(self):
        env_path = os.environ.get("RENDER_ROUTE_JSON", "").strip()
        candidates = []
        if env_path:
            candidates.append(env_path)

        cwd = Path.cwd()
        repo_root = HERE.parent

        candidates += [
            str(cwd / "render_route.json"),
            str(cwd / "json_files" / "render_route.json"),
            str(repo_root / "render_route.json"),
            str(repo_root / "json_files" / "render_route.json"),
        ]

        tried = []
        for p in candidates:
            if not p:
                continue
            tried.append(p)
            if os.path.exists(p):
                try:
                    with open(p, "r", encoding="utf-8") as f:
                        return json.load(f)
                except Exception as e:
                    logs.logger.error(f"render route load failed reading {p}: {e}")
                    return []
        logs.logger.error(f"render route not found. tried: {tried}")
        return []

    def execute(self):
        if not _HAS_RENDER_ROUTE:
            logs.logger.error("bot.render_route not available")
            return
        route = self._load_route()
        if not route:
            msg = "render route empty"
            logs.logger.warning(msg)
            EVENT_LOG.add(msg)
            return
        EVENT_LOG.add(f"Render start [{len(route)} stops], dwell={self._dwell}s")
        render_route.run(route, dwell_s=self._dwell, loop=False, end_at_bed=True)
        EVENT_LOG.add("Render pass finished; resting")

# -------- scheduler --------
class task_scheduler:
    def __init__(self):
        self.active_queue = priority_queue_prio()
        self.waiting_queue = priority_queue_exc()
        self.prev_task_name = ""
    def add_task(self, task: Task):
        if not task.has_run_before:
            enqueue = time.time()
            task.has_run_before = True
        else:
            enqueue = time.time() + task.get_requeue_delay()
        self.waiting_queue.add(task, task.get_priority_level(), enqueue)
        EVENT_LOG.add(f"Queued: {task.name} (prio {task.get_priority_level()})")
        logs.logger.debug(f"added task {task.name} to waiting queue")
    def _requeue(self, task: Task):
        self.waiting_queue.add(task, task.get_priority_level(), time.time() + task.get_requeue_delay())
        EVENT_LOG.add(f"Re-queued: {task.name} (+{task.get_requeue_delay()}s)")
    def run(self):
        while True:
            now = time.time()
            for exec_time, _, prio, task in self.waiting_queue.pop_ready(now):
                self.active_queue.add(task, prio, exec_time)
                EVENT_LOG.add(f"Ready: {task.name}")
            if not self.active_queue.is_empty():
                prio, enq_ts, _, task = self.active_queue.pop()
                if enq_ts <= now:
                    if task.name != self.prev_task_name:
                        logs.logger.info(f"Executing task: {task.name}")
                    EVENT_LOG.add(f"Executing: {task.name}")
                    try:
                        task.execute()
                        EVENT_LOG.add(f"Completed: {task.name}")
                    except Exception as e:
                        logs.logger.error(f"Task '{task.name}' failed: {e}")
                        EVENT_LOG.add(f"Failed: {task.name} -> {e}")
                    self.prev_task_name = task.name
                    if task.name != "pause":
                        self._requeue(task)
                else:
                    self.active_queue.add(task, prio, enq_ts)
            else:
                peek = self.waiting_queue.peek()
                if peek:
                    sleep_for = max(0.2, peek[0] - now)
                    time.sleep(min(sleep_for, 10.0))
                else:
                    time.sleep(0.5)

# -------- entry --------
scheduler: task_scheduler | None = None
started = False

def main():
    global scheduler, started
    if scheduler is None:
        scheduler = task_scheduler()

    render_only   = bool(getattr(settings, "render_only", True))
    enable_render = bool(getattr(settings, "enable_render", True))

    if enable_render or render_only:
        scheduler.add_task(RenderRouteTask())

    logs.logger.info("scheduler running")
    started = True
    scheduler.run()

if __name__ == "__main__":
    time.sleep(1.0)
    main()


