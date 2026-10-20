"""Benchmark for RayCompute comparing CPU vs GPU performance.

This test benchmark writes a summary report to a timestamped file named
AA_MMDD_HHMMSS_bench_ray_compute_result.txt in the repository root.
"""

from __future__ import annotations

import argparse
import sys
import time
import statistics
import datetime
import os
from typing import Optional
from pathlib import Path

from swarm_rescue.maps.map_final_2024_25_01 import MapFinal_2024_25_01
from swarm_rescue.simulation.drone.drone_motionless import DroneMotionless


def run_benchmark(steps: int, repeats: int, use_shaders: bool) -> Optional[dict]:
    """Measure how long `MapIntermediate01.step()` spends rebuilding ray sensors.

    Returns a dict with summary statistics and the per-run mean (ms) list.
    """
    shader_mode = "GPU (shaders)" if use_shaders else "CPU"
    print(f"\n{'='*60}", file=sys.stderr, flush=True)
    print(f"Running benchmark with {shader_mode} mode", file=sys.stderr, flush=True)
    print(f"{'='*60}", file=sys.stderr, flush=True)

    try:
        # Create map with the specified use_shaders parameter
        the_map = MapFinal_2024_25_01(drone_type=DroneMotionless, use_shaders=use_shaders)
        playground = the_map.playground
        print(f"✓ Playground initialized [{shader_mode} mode]", file=sys.stderr, flush=True)
    except Exception as e:
        print(f"✗ ERROR: Failed to create map: {e}", file=sys.stderr)
        import traceback
        traceback.print_exc(file=sys.stderr)
        return None

    print(f"  steps per run: {steps}", file=sys.stderr, flush=True)
    print(f"  repeats: {repeats}\n", file=sys.stderr, flush=True)

    all_times_ms = []
    per_run_elapsed = []

    for run in range(repeats):
        print(f"  Run {run + 1}/{repeats}...", end="", file=sys.stderr, flush=True)
        sys.stderr.flush()

        try:
            start = time.perf_counter()
            for i in range(steps):
                playground.step()
            elapsed = time.perf_counter() - start
            avg_ms = (elapsed / steps) * 1000
            fps = steps / elapsed if elapsed > 0 else 0
            all_times_ms.append(avg_ms)
            per_run_elapsed.append({"total_s": elapsed, "avg_ms": avg_ms, "fps": fps})
            print(f" {elapsed:.3f}s total ({avg_ms:.2f} ms/step, {fps:.1f} FPS)", file=sys.stderr, flush=True)
        except Exception as e:
            print(f"\n✗ ERROR during run {run + 1}: {e}", file=sys.stderr)
            import traceback
            traceback.print_exc(file=sys.stderr)
            return None

        if run < repeats - 1:
            try:
                playground.reset()
            except Exception as e:
                print(f"⚠ WARNING: Failed to reset: {e}", file=sys.stderr)

    # Calculate statistics
    mean_ms = statistics.mean(all_times_ms)
    stdev_ms = statistics.stdev(all_times_ms) if len(all_times_ms) > 1 else 0
    min_ms = min(all_times_ms)
    max_ms = max(all_times_ms)
    mean_fps = 1000 / mean_ms if mean_ms > 0 else 0

    results = {
        "mode": shader_mode,
        "mean_ms": mean_ms,
        "stdev_ms": stdev_ms,
        "min_ms": min_ms,
        "max_ms": max_ms,
        "mean_fps": mean_fps,
        "per_run": per_run_elapsed,
    }

    return results


def _write_results_to_file(results_cpu: dict, results_gpu: dict, steps: int, repeats: int) -> str:
    """Write a formatted summary to a timestamped file in the repository root.

    Returns the path of the written file.
    """
    now = datetime.datetime.now()
    aa = now.year % 100
    filename = (
        f"{aa:02d}_{now.month:02d}{now.day:02d}_{now.hour:02d}{now.minute:02d}"
        f"{now.second:02d}_bench_ray_compute_result.txt"
    )

    # Compute repository root (two levels up from tests script)
    repo_root = Path(__file__).resolve().parent.parent
    out_path = repo_root / filename

    lines = []
    lines.append("BENCHMARK RAY COMPUTE RESULTS")
    lines.append(now.isoformat())
    lines.append("")

    # Metadata
    cmd = ' '.join(sys.argv)
    lines.append(f"Command: {cmd}")
    lines.append(f"Steps per run: {steps}")
    lines.append(f"Repeats: {repeats}")
    lines.append(f"Working dir: {os.getcwd()}")
    lines.append(f"Repository root: {repo_root}")
    lines.append(f"Env SWARM_RESCUE_USE_SHADERS: {os.environ.get('SWARM_RESCUE_USE_SHADERS', '')}")
    lines.append("")

    def _mode_block(r):
        block = []
        block.append(f"Mode: {r['mode']}")
        block.append(f"Mean: {r['mean_ms']:.2f} ms")
        block.append(f"StDev: {r['stdev_ms']:.2f} ms")
        block.append(f"Min: {r['min_ms']:.2f} ms")
        block.append(f"Max: {r['max_ms']:.2f} ms")
        block.append(f"FPS (mean): {r['mean_fps']:.1f}")
        block.append("")
        block.append("Per-run details:")
        for idx, run in enumerate(r.get('per_run', []), start=1):
            block.append(
                f"  Run {idx}: total_s={run['total_s']:.3f}, "
                f"avg_ms={run['avg_ms']:.2f}, fps={run['fps']:.1f}"
            )
        block.append("")
        return block

    lines.extend(_mode_block(results_cpu))
    lines.extend(_mode_block(results_gpu))

    # Comparison
    speedup = (
        results_cpu['mean_ms'] / results_gpu['mean_ms']
        if results_gpu['mean_ms'] > 0 else float('inf')
    )
    speedup_fps = (
        results_gpu['mean_fps'] / results_cpu['mean_fps']
        if results_cpu['mean_fps'] > 0 else float('inf')
    )
    lines.append("COMPARISON:")
    lines.append(f"Speedup (CPU time / GPU time): {speedup:.2f}x")
    lines.append(f"GPU is {speedup_fps:.2f}x faster than CPU in FPS")

    out_path.parent.mkdir(parents=True, exist_ok=True)
    with out_path.open("w", encoding="utf-8") as fh:
        fh.write("\n".join(lines))

    return str(out_path)


def benchmark(steps: int, repeats: int) -> None:
    """Run benchmarks for both CPU and GPU modes and compare."""
    print("\nBenchmarking RayCompute Performance", file=sys.stderr, flush=True)
    print(f"{'='*60}", file=sys.stderr, flush=True)

    # Test CPU mode
    results_cpu = run_benchmark(steps, repeats, use_shaders=False)

    # Test GPU mode
    results_gpu = run_benchmark(steps, repeats, use_shaders=True)

    # Display comparison
    if results_cpu and results_gpu:
        print(f"\n{'='*60}", file=sys.stderr, flush=True)
        print("BENCHMARK RESULTS COMPARISON", file=sys.stderr, flush=True)
        print(f"{'='*60}", file=sys.stderr, flush=True)

        print(f"\n{'Mode':<20} {'Mean':<12} {'StDev':<12} {'Min':<12} {'Max':<12} {'FPS':<10}", file=sys.stderr, flush=True)
        print(f"{'-'*78}", file=sys.stderr, flush=True)

        print(f"{'CPU':<20} {results_cpu['mean_ms']:>7.2f} ms {results_cpu['stdev_ms']:>7.2f} ms {results_cpu['min_ms']:>7.2f} ms {results_cpu['max_ms']:>7.2f} ms {results_cpu['mean_fps']:>7.1f}", file=sys.stderr, flush=True)
        print(f"{'GPU (shaders)':<20} {results_gpu['mean_ms']:>7.2f} ms {results_gpu['stdev_ms']:>7.2f} ms {results_gpu['min_ms']:>7.2f} ms {results_gpu['max_ms']:>7.2f} ms {results_gpu['mean_fps']:>7.1f}", file=sys.stderr, flush=True)

        # Calculate speedup
        speedup = results_cpu['mean_ms'] / results_gpu['mean_ms']
        speedup_fps = results_gpu['mean_fps'] / results_cpu['mean_fps']

        print(f"{'-'*78}", file=sys.stderr, flush=True)
        print(f"\nSpeedup (CPU time / GPU time): {speedup:.2f}x", file=sys.stderr, flush=True)
        print(f"GPU is {speedup_fps:.2f}x faster than CPU in FPS", file=sys.stderr, flush=True)

        # Save results to timestamped file
        out_path = _write_results_to_file(results_cpu, results_gpu, steps, repeats)
        print(f"\nResults saved to: {out_path}", file=sys.stderr, flush=True)

        print("\n✓ Benchmark complete", file=sys.stderr, flush=True)


def main() -> None:
    parser = argparse.ArgumentParser(description="Benchmark RayCompute comparing CPU vs GPU performance")
    parser.add_argument("--steps", type=int, default=50, help="number of steps per measurement")
    parser.add_argument("--repeats", type=int, default=4, help="how many times to repeat the loop")

    args = parser.parse_args()
    benchmark(args.steps, args.repeats)


if __name__ == "__main__":
    main()
