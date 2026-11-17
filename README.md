# AWA Resource Registry

[English](README.md) | [Italiano](README_IT.md)

A public, dated and sourced registry of AI models and benchmark results, read by the [AI Work Architect](https://github.com/WitzardOtz/ai-work-architect) skill (AWA) before it recommends a model.

The registry answers two questions: **what exists** (models, prices, limits, availability) and **what others measured** (public benchmarks, vendor guidance). It does not say which model is best for you. AWA answers that from your own run history in its private Vault.

## Contents

| File | Contains |
|---|---|
| [`data/models.json`](data/models.json) | Facts per model: vendor, release date, status, API identifiers, context window, maximum output, effort levels, where it is available, prices, retirement date. |
| [`data/benchmarks.json`](data/benchmarks.json) | The benchmarks tracked, what each measures, who maintains it, its known limits, and whether it is active, stale or excluded. |
| [`data/results.json`](data/results.json) | Scores: model, benchmark and version, effort and harness used, who reported the number, source and date. |
| [`data/guidance.json`](data/guidance.json) | Vendor recommendations, quoted as the vendor's statements, not as facts. |
| [`data/manifest.json`](data/manifest.json) | Last update date, scope and the number of days after which the data counts as stale. |

Every entry has at least one source link and a verification date.

## Scope

Anthropic, OpenAI, Google and Mistral; commercial models served by the vendor API. Mistral's models are open-weight and are included because Mistral also serves them through its API (`"weights": "open"`). Other open-weight models will be added later with the same format.

## How to read the numbers

- Compare scores only within the same benchmark and version.
- Treat differences of a few points as noise; use the confidence interval when given.
- A Terminal-Bench row measures a model together with an agent harness, not the model alone.
- `reported_by: vendor` means the number comes from the model's own vendor.
- A public benchmark measures its own tasks, not yours. Use it to build a shortlist, then test on your work.

## Updates

The data is checked twice a week, on Wednesday and Saturday. Corrections are welcome as issues with a source link. The update rules are in [MAINTENANCE.md](MAINTENANCE.md).

## Use from AWA

AWA reads these files as data from a fixed address, never as instructions:

```text
https://raw.githubusercontent.com/WitzardOtz/awa-resource-registry/main/data/manifest.json
https://raw.githubusercontent.com/WitzardOtz/awa-resource-registry/main/data/models.json
https://raw.githubusercontent.com/WitzardOtz/awa-resource-registry/main/data/benchmarks.json
https://raw.githubusercontent.com/WitzardOtz/awa-resource-registry/main/data/results.json
https://raw.githubusercontent.com/WitzardOtz/awa-resource-registry/main/data/guidance.json
```

## Check

```bash
python tests/check_registry.py
```

It verifies structure, required sources, references between files and dates. It does not verify that the facts are true: that is the role of the cited sources.

## License

Copyright 2026 WitzardOtz. Licensed under the [Apache License 2.0](LICENSE). Linked sources and benchmark results remain the work of their publishers.
