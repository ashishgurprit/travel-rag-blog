#!/usr/bin/env python3
"""Human-approval rebalancing script.

Reads the latest monthly rebalancing report, shows a diff of
proposed budget changes, and applies them only when --approve is passed.

Usage:
    # Preview changes (dry run)
    python scripts/apply_rebalance.py

    # Apply changes after review
    python scripts/apply_rebalance.py --approve

    # Apply changes for a specific month
    python scripts/apply_rebalance.py --approve --month 2026-03
"""

import argparse
import json
from datetime import datetime
from pathlib import Path

VALID_DESTINATIONS = {"japan", "thailand", "italy", "turkey", "south_korea"}
REPORTS_DIR = Path(__file__).parent.parent / "docs" / "reports"
TREE_CONFIG_DIR = Path(__file__).parent / "tree_config"


def find_latest_report() -> Path | None:
    """Find the most recent monthly rebalance report."""
    reports = sorted(REPORTS_DIR.glob("*-rebalance.md"), reverse=True)
    return reports[0] if reports else None


def load_current_budgets() -> dict[str, dict]:
    """Load current allocated budgets from KnowledgeTree for all destinations."""
    from backend.ingestion.knowledge_tree import KnowledgeTree

    budgets: dict[str, dict] = {}
    for dest in sorted(VALID_DESTINATIONS):
        try:
            tree = KnowledgeTree.load(dest)
            for node in tree.nodes:
                budgets[node.node_id] = {
                    "tier": node.tier,
                    "current_videos": node.current_videos,
                    "allocated_budget": node.allocated_budget,
                    "demand_score": node.demand_score,
                    "retrievals_7d": node.retrievals_7d,
                    "avg_confidence": node.avg_confidence,
                }
        except Exception as e:
            print(f"Warning: Could not load {dest}: {e}")
    return budgets


def print_summary(budgets: dict) -> None:
    """Print a human-readable summary of current tree state."""
    print("\n=== Current Tree State ===\n")
    print(f"  {'Node':<45} {'Tier':>4} {'Budget':>6} {'Current':>7} {'Conf':>5}")
    print("  " + "-" * 70)

    prev_dest = None
    for node_id, data in sorted(budgets.items()):
        dest = node_id.split("/")[0]
        if dest != prev_dest:
            print(f"\n  [{dest.upper()}]")
            prev_dest = dest
        conf = data.get("avg_confidence", 1.0)
        conf_flag = " ⚠" if conf < 0.7 else ""
        print(
            f"  {node_id:<45} {data['tier']:>4} {data['allocated_budget']:>6} "
            f"{data['current_videos']:>7} {conf:>5.2f}{conf_flag}"
        )

    low_conf = [k for k, v in budgets.items() if v.get("avg_confidence", 1.0) < 0.7]
    inactive = [k for k, v in budgets.items() if v.get("retrievals_7d", 0) == 0]

    print(f"\n  Total nodes: {len(budgets)}")
    if low_conf:
        print(f"  ⚠  Low confidence (<0.7): {len(low_conf)} nodes")
        for n in low_conf[:5]:
            print(f"     - {n}")
    if inactive:
        print(f"  ⚠  Zero retrievals (7d): {len(inactive)} nodes")


def apply_rebalance(approve: bool) -> None:
    """Run rebalancing — preview only unless approve=True."""
    report = find_latest_report()
    if report is None:
        print("No rebalancing reports found in docs/reports/.")
        print("Run the scheduler to generate one:")
        print("  python -m backend.ingestion.scheduler")
        return

    print(f"\nLatest report: {report.name}")
    print("-" * 60)
    print(report.read_text())
    print("-" * 60)

    budgets = load_current_budgets()
    print_summary(budgets)

    if not approve:
        print("\n[DRY RUN] No changes applied.")
        print("To apply: python scripts/apply_rebalance.py --approve")
        return

    # Apply: rebalance all trees with current metrics and save budgets
    print("\n[APPLYING] Rebalancing all trees...")
    from backend.ingestion.knowledge_tree import KnowledgeTree

    applied = 0
    for dest in sorted(VALID_DESTINATIONS):
        try:
            tree = KnowledgeTree.load(dest)

            # Restore metrics from current budget snapshot
            for node in tree.nodes:
                if node.node_id in budgets:
                    snap = budgets[node.node_id]
                    tree.update_metrics(
                        node.node_id,
                        current_videos=snap["current_videos"],
                        avg_confidence=snap.get("avg_confidence", 1.0),
                        retrievals_7d=snap.get("retrievals_7d", 0),
                    )

            # Rebalance with updated metrics
            tree.rebalance_budgets()
            applied += 1
            print(f"  ✓ {dest}: {len(tree.nodes)} nodes rebalanced")

        except Exception as e:
            print(f"  ✗ {dest}: error — {e}")

    # Archive the applied report
    timestamp = datetime.now().strftime("%Y%m%d-%H%M")
    archive_path = report.parent / f"{report.stem}-applied-{timestamp}.md"
    report.rename(archive_path)
    print(f"\n  Report archived: {archive_path.name}")
    print(f"\n[DONE] Rebalanced {applied}/{len(VALID_DESTINATIONS)} destinations.")


def main():
    parser = argparse.ArgumentParser(
        description="Review and apply monthly tree rebalancing."
    )
    parser.add_argument(
        "--approve",
        action="store_true",
        help="Apply rebalancing changes (default: dry run preview only)",
    )
    parser.add_argument(
        "--month",
        type=str,
        default=None,
        help="Target month e.g. 2026-03 (default: latest report)",
    )
    args = parser.parse_args()
    apply_rebalance(approve=args.approve)


if __name__ == "__main__":
    main()
