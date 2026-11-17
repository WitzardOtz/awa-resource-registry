#!/usr/bin/env python3
"""Structural check of the AWA resource registry. Stdlib only.

Rejects malformed data, entries without sources, broken references between
files and free text that is too long. It checks structure, not truth: facts
must still be verified against the cited sources.
"""
import json
import re
import sys
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data"
ID = re.compile(r"^[a-z0-9]+(?:[.-][a-z0-9]+)*$")
DAY = re.compile(r"^\d{4}-\d{2}-\d{2}$")
VENDORS = {"anthropic", "openai", "google", "mistral"}
STATUS = {"ga", "preview", "limited", "deprecated", "retired"}
WEIGHTS = {"closed", "open"}
SURFACES = {"api", "claude_apps", "chatgpt", "chatgpt_work", "codex", "gemini_app", "antigravity"}
SOURCE_TYPES = {"vendor", "secondary", "benchmark"}
BENCH_STATUS = {"active", "stale_board", "excluded"}
INDEPENDENCE = {"independent", "mixed", "vendor"}
REPORTED_BY = {"benchmark_maintainer", "independent", "vendor"}
UNITS = {"index", "percent", "elo"}
MAX_TEXT = 600
errors = []


def err(msg):
    errors.append(msg)


def load(name):
    try:
        return json.loads((DATA / name).read_text(encoding="utf-8"))
    except (OSError, ValueError) as exc:
        err(f"{name}: cannot read ({exc})")
        return None


def is_day(value, where, optional=False):
    if value is None and optional:
        return True
    if not isinstance(value, str) or not DAY.match(value):
        err(f"{where}: expected YYYY-MM-DD, got {value!r}")
        return False
    try:
        if date.fromisoformat(value) > date.today():
            err(f"{where}: date {value} is in the future")
            return False
    except ValueError:
        err(f"{where}: invalid date {value!r}")
        return False
    return True


def text(value, where, required=True):
    if value in (None, "") and not required:
        return
    if not isinstance(value, str) or not value.strip():
        err(f"{where}: missing text")
    elif len(value) > MAX_TEXT:
        err(f"{where}: text longer than {MAX_TEXT} characters")


def url(value, where):
    if not isinstance(value, str) or not value.startswith("https://"):
        err(f"{where}: expected an https URL, got {value!r}")


def check_source(s, where):
    if not isinstance(s, dict):
        return err(f"{where}: source must be an object")
    url(s.get("url"), f"{where}.url")
    if s.get("type") not in SOURCE_TYPES:
        err(f"{where}.type: must be one of {sorted(SOURCE_TYPES)}")
    text(s.get("title"), f"{where}.title")


def unique(items, where):
    ids = [i.get("id") for i in items if isinstance(i, dict)]
    for dup in {i for i in ids if ids.count(i) > 1}:
        err(f"{where}: duplicate id {dup}")
    for i in ids:
        if not isinstance(i, str) or not ID.match(i):
            err(f"{where}: invalid id {i!r} (lowercase, digits, '.' and '-')")
    return set(ids)


def check_models(models):
    ids = unique(models, "models.json")
    for m in models:
        w = f"models.json:{m.get('id')}"
        text(m.get("name"), f"{w}.name")
        if m.get("vendor") not in VENDORS:
            err(f"{w}.vendor: must be one of {sorted(VENDORS)}")
        if m.get("status") not in STATUS:
            err(f"{w}.status: must be one of {sorted(STATUS)}")
        if m.get("weights") not in WEIGHTS:
            err(f"{w}.weights: must be one of {sorted(WEIGHTS)}")
        is_day(m.get("released"), f"{w}.released")
        is_day(m.get("verified_at"), f"{w}.verified_at")
        if m.get("retirement_not_before") is not None and not DAY.match(str(m["retirement_not_before"])):
            err(f"{w}.retirement_not_before: expected YYYY-MM-DD")
        if not m.get("api_ids") or not all(isinstance(a, str) and a for a in m["api_ids"]):
            err(f"{w}.api_ids: at least one identifier")
        for k in ("context_window", "max_output"):
            if m.get(k) is not None and (not isinstance(m[k], int) or m[k] <= 0):
                err(f"{w}.{k}: positive integer or null")
        bad = set(m.get("surfaces", [])) - SURFACES
        if bad:
            err(f"{w}.surfaces: unknown {sorted(bad)}")
        if m.get("default_effort") and m.get("effort_levels") and m["default_effort"] not in m["effort_levels"]:
            err(f"{w}.default_effort: not among effort_levels")
        if m.get("successor") is not None and m["successor"] not in ids:
            err(f"{w}.successor: unknown model {m['successor']}")
        prices = m.get("pricing")
        if not prices:
            err(f"{w}.pricing: at least one price")
        for i, p in enumerate(prices or []):
            pw = f"{w}.pricing[{i}]"
            if p.get("currency") != "USD" or p.get("unit") != "per_1m_tokens":
                err(f"{pw}: currency USD and unit per_1m_tokens")
            for k in ("input", "output", "cached_input"):
                if k in p and (not isinstance(p[k], (int, float)) or p[k] < 0):
                    err(f"{pw}.{k}: non-negative number")
            if "input" not in p or "output" not in p:
                err(f"{pw}: input and output are required")
            for k in ("valid_from", "valid_until"):
                if k in p and not DAY.match(str(p[k])):
                    err(f"{pw}.{k}: expected YYYY-MM-DD")
            text(p.get("note"), f"{pw}.note", required=False)
        text(m.get("notes"), f"{w}.notes", required=False)
        sources = m.get("sources") or []
        if not sources:
            err(f"{w}.sources: at least one source")
        for i, s in enumerate(sources):
            check_source(s, f"{w}.sources[{i}]")
        if sources and not any(s.get("type") == "vendor" for s in sources) and "secondary source" not in m.get("notes", ""):
            err(f"{w}: no vendor source; say 'secondary source' in notes when the vendor page does not confirm the facts")
    return ids


def check_benchmarks(benchmarks):
    ids = unique(benchmarks, "benchmarks.json")
    status = {}
    for b in benchmarks:
        w = f"benchmarks.json:{b.get('id')}"
        text(b.get("name"), f"{w}.name")
        text(b.get("measures"), f"{w}.measures")
        text(b.get("maintainer"), f"{w}.maintainer")
        text(b.get("caveats"), f"{w}.caveats")
        if b.get("status") not in BENCH_STATUS:
            err(f"{w}.status: must be one of {sorted(BENCH_STATUS)}")
        if b.get("independence") not in INDEPENDENCE:
            err(f"{w}.independence: must be one of {sorted(INDEPENDENCE)}")
        if not isinstance(b.get("versions"), list):
            err(f"{w}.versions: list")
        url(b.get("url"), f"{w}.url")
        is_day(b.get("verified_at"), f"{w}.verified_at")
        status[b.get("id")] = (b.get("status"), b.get("versions") or [])
    return ids, status


def check_results(results, model_ids, bench_status):
    seen = set()
    for i, r in enumerate(results):
        w = f"results.json[{i}]"
        if r.get("model_id") not in model_ids:
            err(f"{w}.model_id: unknown model {r.get('model_id')}")
        st = bench_status.get(r.get("benchmark_id"))
        if st is None:
            err(f"{w}.benchmark_id: unknown benchmark {r.get('benchmark_id')}")
        else:
            if st[0] == "excluded":
                err(f"{w}: benchmark {r['benchmark_id']} is excluded; do not record scores")
            if st[1] and r.get("benchmark_version") not in st[1]:
                err(f"{w}.benchmark_version: {r.get('benchmark_version')!r} not in {st[1]}")
        if not isinstance(r.get("score"), (int, float)):
            err(f"{w}.score: number")
        if r.get("unit") not in UNITS:
            err(f"{w}.unit: must be one of {sorted(UNITS)}")
        if r.get("unit") == "percent" and isinstance(r.get("score"), (int, float)) and not 0 <= r["score"] <= 100:
            err(f"{w}.score: percent outside 0..100")
        if r.get("reported_by") not in REPORTED_BY:
            err(f"{w}.reported_by: must be one of {sorted(REPORTED_BY)}")
        cfg = r.get("config")
        if not isinstance(cfg, dict) or "effort" not in cfg or "harness" not in cfg:
            err(f"{w}.config: object with effort and harness (null when unknown)")
        url(r.get("source_url"), f"{w}.source_url")
        is_day(r.get("measured_at"), f"{w}.measured_at", optional=True)
        is_day(r.get("retrieved_at"), f"{w}.retrieved_at")
        text(r.get("note"), f"{w}.note", required=False)
        key = (r.get("model_id"), r.get("benchmark_id"), r.get("benchmark_version"),
               json.dumps(cfg, sort_keys=True), r.get("reported_by"))
        if key in seen:
            err(f"{w}: duplicate result for the same model, benchmark, version, configuration and reporter")
        seen.add(key)


def check_guidance(guidance, model_ids):
    unique(guidance, "guidance.json")
    for g in guidance:
        w = f"guidance.json:{g.get('id')}"
        if g.get("vendor") not in VENDORS:
            err(f"{w}.vendor: must be one of {sorted(VENDORS)}")
        for mid in g.get("models") or []:
            if mid not in model_ids:
                err(f"{w}.models: unknown model {mid}")
        text(g.get("statement"), f"{w}.statement")
        check_source(g.get("source"), f"{w}.source")
        is_day(g.get("verified_at"), f"{w}.verified_at")


def check_manifest(manifest, dates):
    if not isinstance(manifest, dict):
        return err("manifest.json: object expected")
    is_day(manifest.get("updated_at"), "manifest.json.updated_at")
    if dates and isinstance(manifest.get("updated_at"), str) and manifest["updated_at"] < max(dates):
        err(f"manifest.json.updated_at: older than the newest verified_at ({max(dates)})")
    if not isinstance(manifest.get("stale_after_days"), int):
        err("manifest.json.stale_after_days: integer")
    for f in manifest.get("files", []):
        if not (DATA / f).is_file():
            err(f"manifest.json.files: missing {f}")


def main():
    models = load("models.json") or []
    benchmarks = load("benchmarks.json") or []
    results = load("results.json") or []
    guidance = load("guidance.json") or []
    manifest = load("manifest.json")
    model_ids = check_models(models)
    _, bench_status = check_benchmarks(benchmarks)
    check_results(results, model_ids, bench_status)
    check_guidance(guidance, model_ids)
    dates = [x.get("verified_at") for x in models + benchmarks + guidance if isinstance(x.get("verified_at"), str)]
    dates += [r.get("retrieved_at") for r in results if isinstance(r.get("retrieved_at"), str)]
    check_manifest(manifest, dates)
    if errors:
        for e in errors:
            print(f"FAIL {e}")
        raise SystemExit(1)
    print(f"registry check: PASS ({len(models)} models, {len(benchmarks)} benchmarks, "
          f"{len(results)} results, {len(guidance)} guidance)")


if __name__ == "__main__":
    main()
