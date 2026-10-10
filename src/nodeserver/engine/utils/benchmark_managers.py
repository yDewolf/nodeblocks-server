
import logging
import time
from typing import Optional

benchmark_logger = logging.getLogger("nds.benchmark")
BENCHMARKING_ACTIVE: bool = any(
    [handler.level == logging.DEBUG for handler in benchmark_logger.handlers]
)

class BenchmarkTimer:
    def __init__(
        self,
        name: str = "Benchmark",
        log_every: int = 0,
        expected_total: Optional[int] = None,
    ):
        self.name = name
        self.log_every = log_every
        self.expected_total = expected_total
        self.iteration = 0
        self.start_time = 0.0
        self.last_log_time = 0.0

    def __enter__(self):
        self.start_time = time.perf_counter()
        self.last_log_time = self.start_time
        self.iteration = 0
        if BENCHMARKING_ACTIVE:
            benchmark_logger.info("Starting %s benchmark timer.", self.name)
        
        return self

    def step(self, count: int = 1):
        if not BENCHMARKING_ACTIVE: return

        self.iteration += count
        now = time.perf_counter()

        if self.log_every > 0 and self.iteration % self.log_every == 0:
            elapsed_chunk = now - self.last_log_time
            avg_step = elapsed_chunk / self.log_every
            total_str = (
                f"/{self.expected_total}" if self.expected_total else ""
            )

            benchmark_logger.debug(
                f"[{self.name}] Step {self.iteration}{total_str} | "
                f"Last {self.log_every} iterations: {elapsed_chunk * 1000:.2f}ms "
                f"({avg_step * 1000:.4f}ms/iter)"
            )
            self.last_log_time = now

    def __exit__(self, exc_type, exc_val, exc_tb):
        if not BENCHMARKING_ACTIVE: return

        total_time = time.perf_counter() - self.start_time
        avg_time = total_time / self.iteration if self.iteration > 0 else 0.0

        benchmark_logger.debug(
            f"[{self.name}] Finished | Total Elapsed: {total_time * 1000:.2f}ms | "
            f"Iterações: {self.iteration} | Final Avg: {avg_time * 1000:.4f}ms/iter"
        )

class FramePacer:
    def __init__(
        self,
        target_fps: Optional[float] = None,
        target_time: Optional[float] = None,
        min_sleep: float = 0.002,
    ):
        if target_time is not None:
            self.target_time = target_time
        elif target_fps is not None and target_fps > 0:
            self.target_time = 1.0 / target_fps
        else:
            self.target_time = 0.0

        self.min_sleep = min_sleep
        self.elapsed = 0.0
        self.sleep_time = 0.0
        self._start_time = 0.0

    def __enter__(self):
        self._start_time = time.perf_counter()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.elapsed = time.perf_counter() - self._start_time
        self.sleep_time = self.target_time - self.elapsed

        if self.sleep_time > self.min_sleep:
            time.sleep(self.sleep_time)