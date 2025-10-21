from __future__ import annotations

import json
import threading
import time
from dataclasses import dataclass
from dataclasses import field
from pathlib import Path
from typing import Any

_global_tracer: PerformanceTracer | None = None
_global_lock = threading.Lock()


def set_global_tracer(tracer: PerformanceTracer) -> None:
    global _global_tracer
    with _global_lock:
        _global_tracer = tracer


def get_global_tracer() -> PerformanceTracer | None:
    with _global_lock:
        return _global_tracer


@dataclass
class PerformanceTracer:
    enabled: bool
    output: Path | None = None
    _lock: threading.Lock = field(default_factory=threading.Lock, init=False)
    _agg: dict[str, float] = field(default_factory=dict, init=False)

    def _now_ns(self) -> int:
        return time.perf_counter_ns()

    def section(self, name: str, **attrs: Any):
        tracer = self

        class _Ctx:
            def __enter__(self):
                self.t0 = tracer._now_ns()
                self.attrs = attrs
                return self

            def __exit__(self, exc_type, exc, tb):
                dt_ms = (tracer._now_ns() - self.t0) / 1e6
                tracer.emit({"section": name, "duration_ms": dt_ms, **attrs})

        return _Ctx()

    def emit(self, obj: dict[str, Any]) -> None:
        if not self.enabled:
            return

        # enrich duration text if present
        duration_ms = obj.get("duration_ms")
        duration_text = None
        if isinstance(duration_ms, (int, float)):
            total_seconds = float(duration_ms) / 1000.0
            minutes = int(total_seconds // 60)
            seconds = total_seconds - minutes * 60
            duration_text = f"{minutes}分{seconds:.1f}秒"

        payload = {
            "timestamp": time.strftime("%Y-%m-%dT%H:%M:%S", time.gmtime()),
            **obj,
        }
        if duration_text is not None:
            payload["duration_text"] = duration_text
        line = json.dumps(payload, ensure_ascii=False)
        if self.output is not None:
            self.output.parent.mkdir(parents=True, exist_ok=True)
            with self._lock:
                with self.output.open("a", encoding="utf-8") as f:
                    f.write(line + "\n")

        sec = payload.get("section")
        if isinstance(sec, str):
            self._agg.setdefault(sec, 0.0)
            self._agg[sec] += float(payload.get("duration_ms", 0.0))

    def summary_lines(self) -> list[str]:
        items = sorted(self._agg.items(), key=lambda x: -x[1])
        return [f"{name}: {ms:.1f} ms" for name, ms in items]
