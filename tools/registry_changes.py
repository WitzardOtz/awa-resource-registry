#!/usr/bin/env python3
"""Summarize and package the changes made to data/ since the last commit.

Stdlib only; needs git. Run from the repository root or pass --repo.

    python tools/registry_changes.py summary            # plain-language list (Italian)
    python tools/registry_changes.py package OUT.zip    # ZIP of changed data files
    python tools/registry_changes.py files              # changed data file names

The summary is computed from the data, not written by a model, so the person
who publishes the update sees exactly what changed.
"""
from __future__ import annotations

import argparse
import json
import subprocess
import sys
import zipfile
from pathlib import Path

FILES = ["models.json", "benchmarks.json", "results.json", "guidance.json", "manifest.json"]
FIXED_TIME = (2026, 1, 1, 0, 0, 0)


def committed(repo: Path, name: str):
    try:
        raw = subprocess.run(["git", "-C", str(repo), "show", f"HEAD:data/{name}"],
                             capture_output=True, check=True).stdout
    except subprocess.CalledProcessError:
        return None
    return json.loads(raw.decode("utf-8"))


def current(repo: Path, name: str):
    return json.loads((repo / "data" / name).read_text(encoding="utf-8"))


def changed_files(repo: Path) -> list[str]:
    return [n for n in FILES if committed(repo, n) != current(repo, n)]


def _price(p: dict) -> str:
    text = f"${p['input']:g} / ${p['output']:g} per milione di token"
    if p.get("valid_from"):
        text += f" dal {p['valid_from']}"
    if p.get("valid_until"):
        text += f" fino al {p['valid_until']}"
    return text


def _result_key(r: dict) -> tuple:
    cfg = r.get("config") or {}
    return (r.get("model_id"), r.get("benchmark_id"), r.get("benchmark_version"),
            cfg.get("effort"), cfg.get("harness"), r.get("reported_by"))


def _result_label(r: dict, names: dict) -> str:
    cfg = r.get("config") or {}
    extra = ", ".join(x for x in (cfg.get("effort") and f"effort {cfg['effort']}", cfg.get("harness")) if x)
    unit = "%" if r.get("unit") == "percent" else ""
    label = f"{names.get(r['model_id'], r['model_id'])} su {r['benchmark_id']} {r.get('benchmark_version')}: {r['score']:g}{unit}"
    return label + (f" ({extra})" if extra else "")


def summary(repo: Path) -> str:
    old = {n: committed(repo, n) or [] for n in FILES}
    new = {n: current(repo, n) for n in FILES}
    lines: list[str] = []
    names = {m["id"]: m["name"] for m in new["models.json"]}

    om = {m["id"]: m for m in old["models.json"]}
    nm = {m["id"]: m for m in new["models.json"]}
    for mid in sorted(set(nm) - set(om)):
        m = nm[mid]
        prices = "; ".join(_price(p) for p in m.get("pricing", []))
        lines.append(f"- Nuovo modello: {m['name']} ({m['vendor']}, uscito il {m['released']}, stato {m['status']}). Prezzo: {prices}.")
    for mid in sorted(set(om) - set(nm)):
        lines.append(f"- ATTENZIONE: il modello {om[mid]['name']} è stato rimosso, ma le regole vietano di cancellare voci.")
    for mid in sorted(set(om) & set(nm)):
        a, b = om[mid], nm[mid]
        if a.get("status") != b.get("status"):
            lines.append(f"- {b['name']}: stato da {a.get('status')} a {b.get('status')}.")
        if a.get("pricing") != b.get("pricing"):
            lines.append(f"- {b['name']}: prezzi aggiornati, ora {'; '.join(_price(p) for p in b.get('pricing', []))}.")
        if a.get("successor") != b.get("successor") and b.get("successor"):
            lines.append(f"- {b['name']}: indicato come successore {names.get(b['successor'], b['successor'])}.")
        if a.get("retirement_not_before") != b.get("retirement_not_before") and b.get("retirement_not_before"):
            lines.append(f"- {b['name']}: ritiro non prima del {b['retirement_not_before']}.")
        other = sorted(k for k in set(a) | set(b)
                       if k not in {"status", "pricing", "successor", "retirement_not_before", "verified_at", "sources"}
                       and a.get(k) != b.get(k))
        if other:
            lines.append(f"- {b['name']}: altri dati aggiornati ({', '.join(other)}).")

    ob = {x["id"]: x for x in old["benchmarks.json"]}
    nb = {x["id"]: x for x in new["benchmarks.json"]}
    for bid in sorted(set(nb) - set(ob)):
        lines.append(f"- Nuovo benchmark seguito: {nb[bid]['name']} (stato {nb[bid]['status']}).")
    for bid in sorted(set(ob) & set(nb)):
        if ob[bid].get("status") != nb[bid].get("status"):
            lines.append(f"- Benchmark {nb[bid]['name']}: stato da {ob[bid].get('status')} a {nb[bid].get('status')}.")
        if ob[bid].get("caveats") != nb[bid].get("caveats"):
            lines.append(f"- Benchmark {nb[bid]['name']}: note aggiornate: {nb[bid].get('caveats')}")
        if ob[bid].get("versions") != nb[bid].get("versions"):
            lines.append(f"- Benchmark {nb[bid]['name']}: versioni seguite ora {', '.join(nb[bid].get('versions') or []) or 'nessuna'}.")

    orr = {_result_key(r): r for r in old["results.json"]}
    nrr = {_result_key(r): r for r in new["results.json"]}
    added = [nrr[k] for k in nrr if k not in orr]
    changed = [(orr[k], nrr[k]) for k in nrr if k in orr and orr[k].get("score") != nrr[k].get("score")]
    for r in sorted(added, key=lambda r: (r["benchmark_id"], -float(r["score"]))):
        lines.append(f"- Nuovo punteggio: {_result_label(r, names)}.")
    for a, b in changed:
        lines.append(f"- Punteggio aggiornato: {_result_label(b, names)} (prima {a['score']:g}).")
    for k in orr:
        if k not in nrr:
            lines.append(f"- ATTENZIONE: rimosso il punteggio {_result_label(orr[k], names)}.")

    og = {x["id"]: x for x in old["guidance.json"]}
    ng = {x["id"]: x for x in new["guidance.json"]}
    for gid in sorted(set(ng) - set(og)):
        lines.append(f"- Nuova indicazione di {ng[gid]['vendor']}: {ng[gid]['statement']}")
    for gid in sorted(set(og) & set(ng)):
        if og[gid].get("statement") != ng[gid].get("statement"):
            lines.append(f"- Indicazione di {ng[gid]['vendor']} aggiornata: {ng[gid]['statement']}")

    head = f"Controllo del {new['manifest.json'].get('updated_at')}"
    if not lines:
        return head + ": nessuna novità, cambia solo la data dell'ultimo controllo."
    return head + f": {len(lines)} modifiche.\n" + "\n".join(lines)


def package(repo: Path, out: Path) -> list[str]:
    names = changed_files(repo)
    out.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(out, "w") as zf:
        for n in names:
            info = zipfile.ZipInfo(n, date_time=FIXED_TIME)
            info.compress_type = zipfile.ZIP_DEFLATED
            info.external_attr = 0o644 << 16
            zf.writestr(info, (repo / "data" / n).read_bytes())
    return names


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--repo", default=str(Path(__file__).resolve().parents[1]))
    sub = ap.add_subparsers(dest="cmd", required=True)
    sub.add_parser("summary")
    sub.add_parser("files")
    p = sub.add_parser("package")
    p.add_argument("out")
    args = ap.parse_args()
    repo = Path(args.repo)
    if args.cmd == "summary":
        print(summary(repo))
    elif args.cmd == "files":
        print("\n".join(changed_files(repo)))
    else:
        names = package(repo, Path(args.out))
        print(f"{len(names)} file nello ZIP: {', '.join(names) or 'nessuno'}")


if __name__ == "__main__":
    try:
        main()
    except (OSError, ValueError, subprocess.SubprocessError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        raise SystemExit(2)
