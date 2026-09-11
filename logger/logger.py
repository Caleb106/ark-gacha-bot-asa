"""The app's one logger, importable from anywhere as `from logger.logger
import logger`.

Everything written through it lands in logger/logs.log, and - once the
dashboard is up - in the on-screen Event Log too. GUI-owned bot processes
send records over stdout for the parent to write and display. Standalone
processes write the file directly. Code in the bot does not
need to know which mode is active; it just logs.

Set up the moment this module is imported:

  - Each standalone/GUI launch starts a fresh logs.log, and the previous run
    is kept in archives/ under its date - logs_2026-07-28_14-52-31.log - back to
    KEPT_RUNS of them. A user who restarts the app before reporting a bug
    still has the log that matters, and can tell which one it is.
  - Crashes are logged, with their full traceback, from all three places
    this app can die: the main thread (sys.excepthook), a worker thread
    (threading.excepthook) and a Tk callback (Tk.report_callback_exception).
    Tk in particular catches exceptions itself and would otherwise swallow
    them, which covers every button press and every `after` job - so most of
    the app.

Ctrl-C is not treated as a crash; it goes to Python's own handler and is not
logged.
"""
import glob
import inspect
import json
import logging
import os
import sys
import threading
import time
import types
from datetime import datetime
from functools import wraps
from typing import Literal

# logs.log lives next to this file, not in whatever directory the app was
# launched from - so the log always lands in logger/ regardless of cwd.
LOG_DIR = os.path.dirname(os.path.abspath(__file__))
LOG_PATH = os.path.join(LOG_DIR, "logs.log")

# Previous runs are archived beside it as logs_2026-07-28_14-52-31.log. The
# timestamp is when that run last wrote a line, and the format sorts
# chronologically as plain text - which is what lets the pruning below just
# sort the names.
ARCHIVE_PATTERN = "logs_*.log"
ARCHIVE_STAMP = "%Y-%m-%d_%H-%M-%S"
ARCHIVE_DIR = os.path.join(LOG_DIR, "archives")
# How many previous runs to keep beside the current logs.log.
KEPT_RUNS = 3

# GUI-owned subprocesses send records to the parent, which owns the log file.
PIPE_ENV = "ASA_BOT_LOG_PIPE"
PIPE_PREFIX = "ASA_LOG_RECORD:"
TEMPLATE_LEVEL = 5
logging.addLevelName(TEMPLATE_LEVEL, "TEMPLATE")


class PipeFormatter(logging.Formatter):
    def format(self, record):
        data = {key: getattr(record, key) for key in (
            "name", "levelno", "pathname", "lineno", "funcName", "created", "msecs")}
        data["message"] = super().format(record)
        return PIPE_PREFIX + json.dumps(data, ensure_ascii=True)


class SharedLogHandler(logging.Handler):
    """Forward standard-library/dependency records to the application's logger."""

    def emit(self, record):
        if logger.isEnabledFor(record.levelno):
            logger.handle(record)


def archive_previous_run() -> None:
    """Move the last run's logs.log aside under a dated name and delete all
    but the newest KEPT_RUNS archives.

    Failures are swallowed on purpose. Another copy of the app holding the
    file open is the likely cause, and no amount of log housekeeping is worth
    refusing to start over - the handler opens in append mode, so the worst
    case is this run's lines landing at the end of the previous run's file.

    Windows will not rename a file that anyone still has open, which includes
    this process: build a second Logging without closing the first one's
    handler and the archive step quietly does nothing. One per process, as
    the class says."""
    os.makedirs(ARCHIVE_DIR, exist_ok=True)
    if os.path.exists(LOG_PATH):
        stamp = datetime.fromtimestamp(os.path.getmtime(LOG_PATH)).strftime(ARCHIVE_STAMP)
        try:
            # os.replace, not rename: two runs inside the same second would
            # otherwise collide on an existing name and raise on Windows.
            os.replace(LOG_PATH, os.path.join(ARCHIVE_DIR, f"logs_{stamp}.log"))
        except OSError:
            return

    archives = sorted(glob.glob(os.path.join(ARCHIVE_DIR, ARCHIVE_PATTERN)))
    stale = archives[:-KEPT_RUNS] if KEPT_RUNS > 0 else archives
    for path in stale:
        try:
            os.remove(path)
        except OSError:
            pass

# An argument whose parameter name contains one of these is written to the
# log as <redacted>. The Discord API key is deliberately kept out of the
# support snapshot (UI.SupportPage._collect_debug_info); a traced function
# taking it as an argument must not put it back in through the side door.
SENSITIVE_PARAMS = ("key", "token", "secret", "password", "auth")

# The function log_function is currently tracing, per thread. Thread-local so
# two bot routines traced at once can't take credit for each other's log
# lines - the previous approach attached a filter to the shared logger, which
# relabelled every thread's records for as long as it was on.
_traced = threading.local()


class FuncNameFilter(logging.Filter):
    """Stamps records with the name of the function log_function is tracing
    on this thread, so its lines are attributed to that function rather than
    to the decorator's wrapper.

    Installed once, permanently. It filters nothing - it only relabels, and
    only while a traced call is actually on the stack."""

    def filter(self, record: logging.LogRecord) -> bool:
        name = getattr(_traced, "name", None)
        if name:
            record.funcName = name
        return True


class Logging(logging.Logger):
    """A logging.Logger that writes to logs.log and catches whatever kills
    the process. Instantiated once at the bottom of this file as `logger`;
    there's no reason to build another - a second one would take the
    exception hooks over from the first."""

    _LOG_LEVEL = Literal["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]
    # The UI mirrors these five levels in its Event Log colors and legend
    # (UI.EVENT_COLORS / EVENT_LABELS) - adding a level here means adding it
    # there too, or it shows up on screen unstyled.
    _LOG_LEVEL_MAP: dict[_LOG_LEVEL, int] = {
        "DEBUG":    logging.DEBUG,
        "INFO":     logging.INFO,
        "WARNING":  logging.WARNING,
        "ERROR":    logging.ERROR,
        "CRITICAL": logging.CRITICAL,
    }

    def __init__(self, level: _LOG_LEVEL = "DEBUG"):
        super().__init__("logger", self._LOG_LEVEL_MAP[level])
        # Only the owning process archives/writes the shared file.
        piped = os.environ.get(PIPE_ENV) == "1"
        if not piped:
            archive_previous_run()
        # mode="a", though the file is expected to be gone by now: if
        # archiving failed, appending to the old log beats truncating it.
        # utf-8 explicitly: Windows otherwise opens the file as cp1252,
        # which raises UnicodeEncodeError on any non-latin-1 character in
        # a log message and silently drops the whole line.
        if piped:
            handler = logging.StreamHandler(sys.stdout)
            handler.setFormatter(PipeFormatter())
        else:
            handler = logging.FileHandler(LOG_PATH, mode="a", encoding="utf-8")
            handler.setFormatter(logging.Formatter(
                fmt="%(asctime)s | %(filename)-14s | %(levelname)-8s | %(funcName)s | %(message)s",
                datefmt="%Y-%m-%d %H:%M:%S"))
        self.addHandler(handler)
        self.propagate = False
        self.addFilter(FuncNameFilter())
        self._install_exception_hooks()

    def setLevel(self, level):
        super().setLevel(level)
        # This directly constructed logger is outside logging's name registry,
        # so the manager's cache clearing does not reach this instance.
        self._cache.clear()

    def template(self, message, *args, **kwargs):
        """Very noisy image-matching diagnostics; disabled at the default DEBUG level."""
        if self.isEnabledFor(TEMPLATE_LEVEL):
            kwargs.setdefault("stacklevel", 2)
            self._log(TEMPLATE_LEVEL, message, args, **kwargs)

    # -- crash reporting --------------------------------------------------------
    def _install_exception_hooks(self) -> None:
        """Point every crash path Python offers at _log_crash.

        sys.excepthook alone only covers the main thread, and only outside
        the Tk event loop - which in a GUI app is close to nowhere. The other
        two hooks are where the crashes actually turn up."""
        sys.excepthook = self._log_crash
        threading.excepthook = self._log_thread_crash
        try:
            import tkinter
        except ImportError:
            return  # no GUI here (the bot may run headless); nothing to hook

        # Tk catches exceptions raised inside callbacks and routes them here
        # instead of letting them reach sys.excepthook. Signature is Tk's,
        # not ours - it calls this as a method on the root widget, which the
        # traceback already identifies better than we could.
        def report_callback_exception(
            _root,
            exc_type: type[BaseException],
            exc_value: BaseException,
            exc_traceback: types.TracebackType | None,
        ) -> None:
            self._log_crash(exc_type, exc_value, exc_traceback, source="Tk callback")

        # Set on the class so it covers the CTk window too: Tk looks the
        # method up on whichever root widget owns the callback. Replacing a
        # method on a class is exactly what Tk documents this attribute for,
        # but it's still an assignment to a method, which type checkers
        # refuse on principle.
        tkinter.Tk.report_callback_exception = (  # pyright: ignore[reportAttributeAccessIssue]
            report_callback_exception
        )

    def _log_crash(
        self,
        exc_type: type[BaseException],
        # Optional because threading.excepthook declares it so: a thread can
        # report a type with no instance attached. sys.excepthook always has
        # one, and logging formats a None value fine either way.
        exc_value: BaseException | None,
        exc_traceback: types.TracebackType | None,
        source: str = "",
    ) -> None:
        """Write a crash to the log as CRITICAL, with its full traceback.

        The traceback is handed to logging via exc_info rather than being
        picked apart here: the whole call chain is what makes a crash report
        worth having, and an earlier version that kept only the innermost
        frame threw away the part that says how the code got there."""
        # Ctrl-C is how the app gets stopped from a terminal, not a fault.
        # Hand it to Python's own hook so it prints as usual and leaves no
        # CRITICAL behind.
        if issubclass(exc_type, KeyboardInterrupt):
            if exc_value is not None:
                sys.__excepthook__(exc_type, exc_value, exc_traceback)
            return

        where = f" in {source}" if source else ""
        if exc_value is None:
            # A type with no instance behind it - there's nothing to build a
            # traceback from, so the name is the whole report.
            self.critical(f"Uncaught {exc_type.__name__}{where}")
            return
        self.critical(f"Uncaught {exc_type.__name__}{where}: {exc_value}",
                      exc_info=(exc_type, exc_value, exc_traceback))

    def _log_thread_crash(self, args: threading.ExceptHookArgs) -> None:
        """threading.excepthook: a crash on a worker thread. Same handling,
        plus which thread died - the traceback alone doesn't say."""
        # Documented as the signal that a thread is shutting down normally.
        if issubclass(args.exc_type, SystemExit):
            return
        thread = args.thread.name if args.thread else "unknown thread"
        self._log_crash(args.exc_type, args.exc_value, args.exc_traceback,
                        source=f"thread {thread}")

    # -- function tracing -------------------------------------------------------
    def _truncate(self, obj: object) -> str:
        """Cap an object's string form at 120 characters, so one huge
        argument can't bury the rest of the log."""
        text = str(obj)
        return text if len(text) <= 120 else text[:120] + "..."

    def _render_argument(self, name: str, value: object) -> str:
        """One `name=value` pair, redacted if the name reads like a
        credential."""
        if any(word in name.lower() for word in SENSITIVE_PARAMS):
            return f"{name}=<redacted>"
        return f"{name}={self._truncate(value)}"

    def _describe_call(self, func, args, kwargs) -> str:
        """Render a call's arguments as `name=value`, with anything named
        like a credential replaced by <redacted>.

        Matching values to parameter names is what makes redaction possible
        at all - a bare tuple of values gives nothing to judge. Two cases
        can't be matched, and both are treated as unsafe rather than shown:
        arguments swallowed by *args, which have no names of their own, and
        calls whose arguments don't fit the signature (about to raise
        TypeError anyway). **kwargs is fine - its keys are real names."""
        try:
            signature = inspect.signature(func)
            bound = signature.bind(*args, **kwargs)
        except (TypeError, ValueError):
            return f"<{len(args) + len(kwargs)} unmatched arguments>"

        parts = []
        for name, value in bound.arguments.items():
            kind = signature.parameters[name].kind
            if kind is inspect.Parameter.VAR_POSITIONAL:
                # *args: nothing here can be shown to be safe, so none of it
                # is printed. The count still gives the call's shape.
                parts.append(f"*{name}=<{len(value)} unnamed>")
            elif kind is inspect.Parameter.VAR_KEYWORD:
                inner = ", ".join(self._render_argument(key, item)
                                  for key, item in value.items())
                parts.append(f"**{name}={{{inner}}}")
            else:
                parts.append(self._render_argument(name, value))
        return ", ".join(parts)

    def log_function(self, func):
        """Decorator: log a function's arguments, its result and how long it
        took, as two DEBUG lines around the call.

        Both lines are attributed to the traced function rather than to this
        wrapper. A call that raises is logged too - with the exception and
        the elapsed time - and then re-raised untouched; the tracing never
        changes what the caller sees.

        Arguments named like credentials are redacted (SENSITIVE_PARAMS)."""
        @wraps(func)
        def wrapper(*args, **kwargs):
            # Saved and restored rather than cleared, so a traced function
            # calling another one hands the label back on the way out
            # instead of leaving the inner name in place.
            previous = getattr(_traced, "name", None)
            _traced.name = f"log->{func.__name__}"
            start_time = time.perf_counter()
            try:
                self.debug(f"call({self._describe_call(func, args, kwargs)})")
                result = func(*args, **kwargs)
            except BaseException as error:
                # Deliberately BaseException: a KeyboardInterrupt mid-call is
                # exactly the kind of thing worth seeing in the trace. The
                # exception carries on regardless - this only observes it.
                elapsed = time.perf_counter() - start_time
                self.debug(f"raised({type(error).__name__}: {self._truncate(error)})"
                           f" time({elapsed:.6f}s)")
                raise
            else:
                elapsed = time.perf_counter() - start_time
                self.debug(f"return({type(result).__name__}, {self._truncate(result)})"
                           f" time({elapsed:.6f}s)")
                return result
            finally:
                # In a finally so an exception on the way out can't leave the
                # label attached. It used to be a filter added to the shared
                # logger and removed after the call - which never ran when the
                # call raised, leaving every later line in the app stamped
                # with the name of a function that had long since returned.
                _traced.name = previous

        return wrapper


logger = Logging("INFO")

# Dependency loggers (including discord.py) propagate here. Do not configure
# their own file handlers or send shared records back through this root.
logging.getLogger().addHandler(SharedLogHandler())
logging.getLogger().setLevel(logging.INFO)


def relay_output(line):
    """Receive one child line, preserving source/level and writing it exactly once."""
    if line.startswith(PIPE_PREFIX):
        try:
            data = json.loads(line[len(PIPE_PREFIX):])
            record = logging.LogRecord(
                str(data["name"]), int(data["levelno"]), str(data["pathname"]),
                int(data["lineno"]), str(data["message"]), (), None, str(data["funcName"]))
            record.created = float(data["created"])
            record.msecs = float(data["msecs"])
        except (ValueError, TypeError, KeyError):
            logger.warning("Malformed subprocess log record: %s", line)
        else:
            if logger.isEnabledFor(record.levelno):
                logger.handle(record)
    elif line.strip():
        logger.info("Subprocess output: %s", line.rstrip("\r\n"))
