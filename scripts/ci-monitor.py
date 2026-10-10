#!/usr/bin/env python3
"""Lightweight resource monitor for the Parrot Browser CI build.

Why this exists: a `signal: 9 (SIGKILL)` from rustc is *consistent with* the
kernel OOM killer but does not prove it. This script records enough to prove or
disprove it after the fact, without needing procps/dmesg/root inside the
build container (it only reads /proc and the cgroup files).

Usage:
    ci-monitor.py run     <outdir> [interval_seconds]   # sample until SIGTERM/SIGINT
    ci-monitor.py summary <outdir>                      # print a Markdown summary
"""
import json
import os
import shutil
import signal
import sys
import time

PAGE = os.sysconf("SC_PAGE_SIZE")
MIB = 1024 * 1024
CGROUP = "/sys/fs/cgroup"
CSV_HEADER = (
    "time_utc,mem_avail_mib,swap_used_mib,cgroup_current_mib,cgroup_oom_kill,"
    "disk_free_gib,top_process,top_rss_mib\n"
)


def read_meminfo():
    info = {}
    with open("/proc/meminfo") as fh:
        for line in fh:
            key, _, rest = line.partition(":")
            info[key] = int(rest.split()[0])  # kB
    return info


def read_int(path):
    try:
        with open(path) as fh:
            value = fh.read().strip()
        return None if value == "max" else int(value)
    except (OSError, ValueError):
        return None


def read_oom_kill():
    try:
        with open(os.path.join(CGROUP, "memory.events")) as fh:
            for line in fh:
                if line.startswith("oom_kill "):
                    return int(line.split()[1])
    except (OSError, ValueError):
        pass
    return None


def label_for(pid, comm):
    """Human-meaningful label, e.g. rustc[gkrust] or clang[Unified_cpp_dom0.cpp]."""
    try:
        with open(f"/proc/{pid}/cmdline", "rb") as fh:
            args = [a.decode("utf-8", "replace") for a in fh.read().split(b"\0") if a]
    except OSError:
        return comm
    if "--crate-name" in args:
        idx = args.index("--crate-name")
        if idx + 1 < len(args):
            return f"{comm}[{args[idx + 1]}]"
    for arg in reversed(args):
        if arg.endswith((".cpp", ".cc", ".c", ".rs")):
            return f"{comm}[{os.path.basename(arg)}]"
    if comm in ("lld-link", "ld.lld", "lld"):
        for arg in args:
            if arg.lower().startswith(("-out:", "/out:")):
                return f"{comm}[{os.path.basename(arg[5:])}]"
    return comm


def scan_processes(known_labels):
    """Return [(rss_bytes, pid, label)] for all visible processes."""
    result = []
    for entry in os.listdir("/proc"):
        if not entry.isdigit():
            continue
        try:
            with open(f"/proc/{entry}/statm") as fh:
                rss = int(fh.read().split()[1]) * PAGE
            if rss <= 0:
                continue
            pid = int(entry)
            if pid not in known_labels:
                with open(f"/proc/{entry}/comm") as fh:
                    comm = fh.read().strip()
                known_labels[pid] = label_for(pid, comm)
            result.append((rss, pid, known_labels[pid]))
        except (OSError, ValueError, IndexError):
            continue
    return result


def write_json_atomic(path, data):
    tmp = path + ".tmp"
    with open(tmp, "w") as fh:
        json.dump(data, fh, indent=1, sort_keys=True)
    os.replace(tmp, path)


def run(outdir, interval):
    os.makedirs(outdir, exist_ok=True)
    csv_path = os.path.join(outdir, "memory.csv")
    peaks_path = os.path.join(outdir, "peak-by-process.json")
    peaks = {}  # label -> {"peak_rss_mib": float, "seen_at": str}
    known = {}
    stop = {"flag": False}

    def _stop(*_):
        stop["flag"] = True

    signal.signal(signal.SIGTERM, _stop)
    signal.signal(signal.SIGINT, _stop)

    last_flush = 0.0
    with open(csv_path, "w", buffering=1) as csv:
        csv.write(CSV_HEADER)
        while not stop["flag"]:
            now = time.strftime("%H:%M:%S", time.gmtime())
            mem = read_meminfo()
            avail = mem.get("MemAvailable", 0) // 1024
            swap_used = (mem.get("SwapTotal", 0) - mem.get("SwapFree", 0)) // 1024
            cg_cur = read_int(os.path.join(CGROUP, "memory.current"))
            cg_cur = cg_cur // MIB if cg_cur is not None else -1
            oom = read_oom_kill()
            try:
                disk_free = shutil.disk_usage(os.getcwd()).free / 1024**3
            except OSError:
                disk_free = -1.0

            procs = scan_processes(known)
            procs.sort(reverse=True)
            top_label, top_rss = ("-", 0.0)
            if procs:
                top_label, top_rss = procs[0][2], procs[0][0] / MIB

            for rss, _pid, lbl in procs[:8]:
                rss_mib = rss / MIB
                if rss_mib > peaks.get(lbl, {}).get("peak_rss_mib", 0.0):
                    peaks[lbl] = {"peak_rss_mib": round(rss_mib, 1), "seen_at": now}

            csv.write(
                f"{now},{avail},{swap_used},{cg_cur},"
                f"{oom if oom is not None else -1},{disk_free:.1f},"
                f'"{top_label}",{top_rss:.0f}\n'
            )

            if time.monotonic() - last_flush > 30:
                write_json_atomic(peaks_path, peaks)
                last_flush = time.monotonic()
            if len(known) > 20000:
                known.clear()
            time.sleep(interval)
    write_json_atomic(peaks_path, peaks)


def summary(outdir):
    csv_path = os.path.join(outdir, "memory.csv")
    peaks_path = os.path.join(outdir, "peak-by-process.json")
    if not os.path.exists(csv_path):
        print("_No monitor data was recorded (the build step may not have started)._")
        return
    rows = []
    with open(csv_path) as fh:
        next(fh, None)
        for line in fh:
            parts = line.rstrip("\n").split(",", 6)
            if len(parts) < 7:
                continue
            try:
                rows.append((parts[0], int(parts[1]), int(parts[2]), int(parts[3]),
                             int(parts[4]), float(parts[5])))
            except ValueError:
                continue
    if not rows:
        print("_Monitor produced no samples._")
        return

    low = min(rows, key=lambda r: r[1])
    max_swap = max(r[2] for r in rows)
    max_cg = max(r[3] for r in rows)
    last_oom = rows[-1][4]
    min_disk = min(r[5] for r in rows if r[5] >= 0) if any(r[5] >= 0 for r in rows) else -1

    print("### Resource summary")
    print(f"- Samples: {len(rows)} ({rows[0][0]} -> {rows[-1][0]} UTC)")
    print(f"- Lowest MemAvailable: **{low[1]} MiB** at {low[0]} UTC")
    print(f"- Peak swap used: {max_swap} MiB")
    if max_cg >= 0:
        print(f"- Peak container cgroup memory.current (sampled): {max_cg} MiB")
    if last_oom >= 0:
        verdict = ("**the kernel OOM killer fired inside this container**"
                   if last_oom > 0 else "no OOM kills recorded for this container")
        print(f"- cgroup `oom_kill` counter: {last_oom} ({verdict})")
    else:
        print("- cgroup `oom_kill` counter: unavailable in this container")
    if min_disk >= 0:
        print(f"- Lowest free disk on the workspace filesystem: {min_disk:.1f} GiB")

    if os.path.exists(peaks_path):
        with open(peaks_path) as fh:
            peaks = json.load(fh)
        top = sorted(peaks.items(), key=lambda kv: kv[1]["peak_rss_mib"], reverse=True)[:10]
        print("\n| Process (peak RSS) | MiB | Seen at (UTC) |")
        print("|---|---:|---|")
        for lbl, data in top:
            print(f"| `{lbl}` | {data['peak_rss_mib']:.0f} | {data['seen_at']} |")


def main(argv):
    if len(argv) < 3 or argv[1] not in ("run", "summary"):
        print(__doc__)
        return 2
    if argv[1] == "run":
        interval = float(argv[3]) if len(argv) > 3 else 10.0
        run(argv[2], interval)
    else:
        summary(argv[2])
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
