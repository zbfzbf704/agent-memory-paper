#!/usr/bin/env python3
"""
sigma_access_check.py — measure the correlation between a salience signal and an
access counter in any SQLite table.

Companion tool to:
  "Salience, Ranking, and Metabolism: Three Conflated Signals in Long-Running
   Agent Memory Systems" — https://doi.org/10.5281/zenodo.23068931

Why this exists
---------------
The Silence Test proves a metric does not drift when retrieval is silenced.
A skeptical reader may still ask: "zero drift only shows the value didn't change —
it doesn't prove the metric is independent of access." This tool answers that with
two pieces of evidence:

  1. FORMULA (decisive): read your salience function and confirm the access counter
     never enters it. Constraining the *write path* is what invariant I1 is about.
  2. CORRELATION (honest): report σ vs. access correlation anyway — without assuming
     it is zero.

Our own run on a 38k-node production store gave Pearson r = 0.24 (not zero). That
residual is a shared-structural-cause artifact (structurally central items are also
more retrievable), not a write path. Reporting 0.24 honestly is more defensible than
claiming ~0.

Usage
-----
    python3 sigma_access_check.py --db path/to/your.db --table nodes \
        --salience-col cv_diversity --access-col recall_count

    # exclude rows by a status column:
    python3 sigma_access_check.py --db your.db --table nodes \
        --salience-col salience --access-col hits \
        --status-col status --exclude archived,retired

Read-only. Nothing is written to your database.
"""
import argparse
import math
import sqlite3
import sys


def pearson(xs, ys):
    n = len(xs)
    if n < 2:
        return float("nan")
    mx = sum(xs) / n
    my = sum(ys) / n
    num = sum((x - mx) * (y - my) for x, y in zip(xs, ys))
    dx = math.sqrt(sum((x - mx) ** 2 for x in xs))
    dy = math.sqrt(sum((y - my) ** 2 for y in ys))
    return num / (dx * dy) if dx > 0 and dy > 0 else float("nan")


def spearman(xs, ys):
    n = len(xs)

    def rank(v):
        order = sorted(range(n), key=lambda i: v[i])
        r = [0] * n
        i = 0
        while i < n:
            j = i
            while j + 1 < n and v[order[j + 1]] == v[order[i]]:
                j += 1
            for k in range(i, j + 1):
                r[order[k]] = (i + j) / 2 + 1
            i = j + 1
        return r

    return pearson(rank(xs), rank(ys))


def main():
    ap = argparse.ArgumentParser(description="σ–access correlation check (read-only).")
    ap.add_argument("--db", required=True, help="path to SQLite database")
    ap.add_argument("--table", required=True, help="table name")
    ap.add_argument("--salience-col", required=True, help="salience/importance column")
    ap.add_argument("--access-col", required=True, help="access/recall counter column")
    ap.add_argument("--status-col", default=None, help="optional status column to filter on")
    ap.add_argument("--exclude", default="", help="comma-separated status values to exclude")
    ap.add_argument("--group-col", default=None,
                    help="optional column; report within-group correlation (detects confounding)")
    ap.add_argument("--min-group", type=int, default=50,
                    help="minimum group size for group-col reporting (default 50)")
    args = ap.parse_args()

    conn = sqlite3.connect(f"file:{args.db}?mode=ro", uri=True)
    where, params = "", []
    if args.status_col and args.exclude:
        vals = [v.strip() for v in args.exclude.split(",") if v.strip()]
        where = f" WHERE {args.status_col} NOT IN ({','.join('?' * len(vals))})"
        params = vals

    cols = args.salience_col
    if args.group_col:
        cols += f", {args.group_col}"
    q = f"SELECT {cols}, {args.access_col} FROM {args.table}{where}"
    rows = conn.execute(q, params).fetchall()
    if not rows:
        print("No rows returned.", file=sys.stderr)
        return 1

    if args.group_col:
        sx = [r[0] or 0 for r in rows]
        ay = [r[2] or 0 for r in rows]
        groups = {}
        for r in rows:
            groups.setdefault(r[1], []).append((r[0] or 0, r[2] or 0))
    else:
        sx = [r[0] or 0 for r in rows]
        ay = [r[1] or 0 for r in rows]
        groups = None

    n = len(sx)
    nz = sum(1 for y in ay if y > 0)
    print("=" * 62)
    print("σ–access correlation check (read-only)")
    print("=" * 62)
    print(f"table={args.table}  rows={n}  access>0: {nz} ({100 * nz / n:.1f}%)")
    print(f"  Pearson  r(σ, access) = {pearson(sx, ay):+.4f}")
    print(f"  Spearman ρ(σ, access) = {spearman(sx, ay):+.4f}")

    # σ=0 vs σ>0 access rate — structure, not retrieval
    zero = [y for x, y in zip(sx, ay) if x == 0]
    pos = [y for x, y in zip(sx, ay) if x > 0]
    if zero and pos:
        print(f"\n  σ=0 group: n={len(zero)}, access>0 {100 * sum(1 for y in zero if y > 0) / len(zero):.1f}%")
        print(f"  σ>0 group: n={len(pos)}, access>0 {100 * sum(1 for y in pos if y > 0) / len(pos):.1f}%")

    if groups:
        print(f"\n  within-{args.group_col} correlation (range -> confounding signature):")
        vals = []
        for g, items in sorted(groups.items(), key=lambda kv: -len(kv[1])):
            if len(items) < args.min_group:
                continue
            gx = [a for a, b in items]
            gy = [b for a, b in items]
            r = pearson(gx, gy)
            if not math.isnan(r):
                vals.append(r)
            print(f"    {str(g)[:30]:<32} n={len(items):>6}  r={r:+.3f}")
        if vals:
            print(f"  range: {min(vals):+.3f} .. {max(vals):+.3f}")

    print("\n" + "-" * 62)
    print("Reading guide:")
    print("  • The decisive evidence is the FORMULA: does the access counter")
    print("    appear anywhere in how salience is computed? If not, there is no")
    print("    write path, and I1 holds regardless of correlation.")
    print("  • A non-zero correlation with widely varying within-group values")
    print("    is the signature of a shared structural cause, not a write-back.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
