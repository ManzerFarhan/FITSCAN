"""PHI-safe logging (NFR-08): scrubs emails, phone numbers and numeric values from log messages."""
import logging
import re

_PATTERNS = [
    (re.compile(r"[\w.+-]+@[\w-]+\.[\w.]+"), "<email>"),
    (re.compile(r"\+?\d[\d\s-]{8,}\d"), "<phone>"),
    (re.compile(r"(?<![\w-])\d+(?:\.\d+)?(?![\w-])"), "<num>"),
]


def scrub(text: str) -> str:
    for pattern, repl in _PATTERNS:
        text = pattern.sub(repl, text)
    return text


class PHIScrubFilter(logging.Filter):
    def filter(self, record: logging.LogRecord) -> bool:
        record.msg = scrub(record.getMessage())
        record.args = ()
        return True


def setup_logging(level: int = logging.INFO) -> None:
    handler = logging.StreamHandler()
    handler.setFormatter(logging.Formatter("%(asctime)s %(levelname)s %(name)s: %(message)s"))
    handler.addFilter(PHIScrubFilter())
    root = logging.getLogger("fitscan")
    root.handlers = [handler]
    root.setLevel(level)
    root.propagate = False


def log_memory(stage: str) -> None:
    """LOG_MEMORY=1 (Linux): print current/peak resident memory. Printed, not logged, because the PHI filter
    above masks every number; these figures contain no patient data."""
    import os

    if os.environ.get("LOG_MEMORY") != "1":
        return
    try:
        with open("/proc/self/status") as f:
            fields = dict(line.split(":", 1) for line in f if line.startswith(("VmRSS", "VmHWM")))
        print(f"[memory] {stage}: rss={fields['VmRSS'].strip()} peak={fields['VmHWM'].strip()}", flush=True)
    except (OSError, KeyError):
        pass


def get_logger(name: str) -> logging.Logger:
    return logging.getLogger(f"fitscan.{name}")
