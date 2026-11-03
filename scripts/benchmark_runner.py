#!/usr/bin/env python3
import argparse
import csv
import os
import statistics
import subprocess
import sys
import time
from typing import Dict, List, Optional, Tuple

def run_iteration(command: List[str]) -> Tuple[float, float]:
    """Runs a command once and returns (elapsed_time_sec, peak_memory)."""
    start = time.perf_counter()
    if sys.platform != "win32" and hasattr(os, "wait4"):
        pid = os.fork()
        if pid == 0:
            try:
                os.execvp(command[0], command)
            except Exception as e:
                print(f"Error: {e}", file=sys.stderr)
                os._exit(1)
        else:
            _, status, rusage = os.wait4(pid, 0)
            elapsed = time.perf_counter() - start
            if not os.WIFEXITED(status) or os.WEXITSTATUS(status) != 0:
                raise RuntimeError(f"Command failed with status {status}")
            return elapsed, float(rusage.ru_maxrss)
    else:
        subprocess.run(command, check=True)
        return time.perf_counter() - start, 0.0

def calculate_metrics(times: List[float], memories: List[float]) -> Dict[str, float]:
    """Calculates summary metrics from times and memory usages."""
    if not times:
        return {}
    return {
        "mean": statistics.mean(times),
        "median": statistics.median(times),
        "stdev": statistics.stdev(times) if len(times) > 1 else 0.0,
        "min": min(times),
        "max": max(times),
        "peak_memory": max(memories) if memories else 0.0,
    }

def output_results(metrics: Dict[str, float], csv_path: Optional[str]) -> None:
    """Outputs metrics to stdout or a CSV file."""
    if csv_path:
        with open(csv_path, mode="w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=list(metrics.keys()))
            writer.writeheader()
            writer.writerow(metrics)
    else:
        print("Metric summary:")
        for key, value in metrics.items():
            print(f"  {key}: {value:.4f}")

def main(args: Optional[List[str]] = None) -> None:
    """Main entry point for the benchmark runner."""
    parser = argparse.ArgumentParser(description="Benchmark runner")
    parser.add_argument("-n", "--iterations", type=int, default=5)
    parser.add_argument("--csv", type=str, help="Output CSV path")
    parser.add_argument("command", nargs=argparse.REMAINDER)
    parsed = parser.parse_args(args)
    cmd = parsed.command
    if cmd and cmd[0] == "--":
        cmd = cmd[1:]
    if not cmd:
        print("No command provided.", file=sys.stderr)
        sys.exit(1)

    times: List[float] = []
    memories: List[float] = []
    for _ in range(parsed.iterations):
        t, m = run_iteration(cmd)
        times.append(t)
        memories.append(m)
    metrics = calculate_metrics(times, memories)
    output_results(metrics, parsed.csv)

if __name__ == "__main__":
    main()
