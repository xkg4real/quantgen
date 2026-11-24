"""DIDM Stage 1 report: score a labelled gold set against the registered rules (DIDM-5).

    python -B -m tools.didm.stage1_report --dir <folder outside the repository>

The folder holds (JSON Lines unless noted):
    annotator_a.jsonl, annotator_b.jsonl, gold.jsonl   gold labels (core/didm/llm/schema.py validate_gold)
    scorers.json                                        {"llm": {"model_version": ..., "file": ...},
                                                         "baselines": {"loughran-mcdonald": {...}, "ProsusAI/finbert": {...}}}
    <file named in scorers.json>                        one didm-judgement-v0 object per line
    links.jsonl                                         predicted links: {"article_id": ..., "entity_id": ...}

Prints the criteria table and one line ``STAGE1: GO|REVISE|NO-GO|INVALID``. It reads local files only:
no network, no model calls. Gold labels and article text are licensed or private material and must
stay outside the repository, so a folder inside the repository is refused.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from core.didm.eval import stage1
from core.didm.llm.judgement import ScoreRequest, validate_judgement
from core.didm.llm.schema import SchemaError, validate_gold

ROOT = Path(__file__).resolve().parents[2]


def _lines(path: Path) -> list[dict]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def load(folder: Path) -> dict:
    gold = [validate_gold(row) for row in _lines(folder / "gold.jsonl")]
    by_key = {(g.article_id, g.entity_id): g for g in gold}
    by_pair: dict = {}

    def run(spec: dict) -> stage1.ScorerRun:
        judgements, rejected = {}, 0
        for raw in _lines(folder / spec["file"]):
            key = (raw.get("article_id"), raw.get("entity_id")) if isinstance(raw, dict) else None
            label = by_key.get(key)
            if label is None:
                raise stage1.Stage1Error(f"{spec['file']}: a judgement is for an item outside the gold set")
            request = ScoreRequest(label.article_id, "en" if label.market == "EN" else "ko", "(not needed)", None,
                                   label.target_kind, label.entity_id, None)
            try:
                judgements[key] = validate_judgement(raw, request)
            except SchemaError:
                rejected += 1                      # counted as a wrong answer by stage1.evaluate
        by_pair[spec["file"]] = rejected
        return stage1.ScorerRun(spec["model_version"], judgements)

    scorers = json.loads((folder / "scorers.json").read_text(encoding="utf-8"))
    return dict(
        annotator_a=[validate_gold(row) for row in _lines(folder / "annotator_a.jsonl")],
        annotator_b=[validate_gold(row) for row in _lines(folder / "annotator_b.jsonl")],
        gold=gold,
        llm=run(scorers["llm"]),
        baselines={name: run(spec) for name, spec in scorers["baselines"].items()},
        predicted_links={(row["article_id"], row["entity_id"]) for row in _lines(folder / "links.jsonl")},
    ), by_pair


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--dir", type=Path, required=True, help="input folder; must be outside the repository")
    parser.add_argument("--bootstrap-seed", type=int, default=0)
    args = parser.parse_args(argv)
    folder = args.dir.resolve()
    if folder == ROOT or ROOT in folder.parents:
        print("--dir must be a folder outside the repository", file=sys.stderr)
        return 2
    inputs, rejected = load(folder)
    report = stage1.evaluate(**inputs, bootstrap_seed=args.bootstrap_seed)
    sys.stdout.write(stage1.render(report))
    for name, count in sorted(rejected.items()):
        print(f"rejected judgements in {name}: {count}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
