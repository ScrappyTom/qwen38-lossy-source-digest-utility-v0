from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from apparatus.canonical import load_json, write_json
from apparatus.constants import ROOT


def analyze(run_root: Path) -> dict[str, Any]:
    run = load_json(run_root / "RUN_RESULT.json")
    calls = run["calls"]
    prompt_tokens = sum((row.get("provider_usage") or {}).get("prompt_tokens", 0) for row in calls)
    completion_tokens = sum((row.get("provider_usage") or {}).get("completion_tokens", 0) for row in calls)
    cached_tokens = sum((((row.get("provider_usage") or {}).get("prompt_tokens_details") or {}).get("cached_tokens", 0)) for row in calls)
    same_source_calls = [row["call"] for row in calls if row["classification"] == "same_source_raw_access"]
    mutations = [row["call"] for row in calls if row["classification"] == "mutation" and row["admitted"]]
    submissions = [row["call"] for row in calls if row["classification"] == "submission" and row["admitted"]]
    marginal = load_json(ROOT / "MARGINAL_VALUE_CONTRACT.json")["immediate_price"]
    result = {
        "schema_version": "lossy-source-digest-utility-analysis-v0", "run_id": run["run_id"],
        "endpoint": run["endpoint"], "model_calls": run["model_calls"],
        "first_action": calls[0]["action"] if calls else None,
        "first_action_classification": calls[0]["classification"] if calls else None,
        "first_same_source_access_call": min(same_source_calls) if same_source_calls else None,
        "same_source_access_subclasses": [row["same_source_access_subclass"] for row in calls if row["same_source_access_subclass"]],
        "action_sequence": [{"call": row["call"], "action": row["action"], "classification": row["classification"], "admitted": row["admitted"], "duplicate": row["duplicate_on_unchanged_candidate_basis"]} for row in calls],
        "mutations": mutations, "submissions": submissions,
        "candidate_changed": run["initial_candidate_id"] != run["final_candidate_id"],
        "result_deliveries_to_later_calls": sum(1 for row in calls if row["result_delivered_to_later_call"]),
        "pressure_events": len(run["pressure_events"]),
        "usage": {"prompt_tokens": prompt_tokens, "completion_tokens": completion_tokens, "cached_prompt_tokens": cached_tokens, "uncached_prompt_tokens": prompt_tokens - cached_tokens, "serialized_total_tokens": prompt_tokens + completion_tokens},
        "economic_accounting": {
            "resident_prompt_token_increment": marginal["resident_prompt_tokens"],
            "digest_content_tokens": marginal["digest_content_tokens"],
            "wrapper_and_template_tokens": marginal["wrapper_and_template_marginal_tokens"],
            "production_prompt_tokens": marginal["production_prompt_tokens"],
            "production_completion_tokens": marginal["production_completion_tokens"],
            "production_total_tokens": marginal["production_total_tokens"],
            "production_latency_ms": marginal["production_latency_ms"],
            "raw_source_bytes_recovered": sum(load_json(run_root / "results" / f"call-{row['call']:02d}.json")["result"].get("size_bytes", 0) for row in calls if row["classification"] == "same_source_raw_access"),
            "short_horizon_production_payback_established": False,
        },
        "historical_control_contemporaneous": False,
        "latency_cache_comparison_scope": "descriptive",
        "direct_semantic_utility_requires_audit": True,
    }
    write_json(run_root / "analysis" / "ANALYSIS.json", result)
    return result


def main() -> int:
    parser = argparse.ArgumentParser(); parser.add_argument("run_root", type=Path); args = parser.parse_args()
    result = analyze(args.run_root.resolve()); print(json.dumps(result, sort_keys=True)); return 0


if __name__ == "__main__": raise SystemExit(main())

