"""Knowledge tree — 3-tier destination taxonomy with budget management.

Loads static taxonomy from scripts/tree_config/{destination}.json and
provides tier-based budget allocation with floor/cap enforcement and
log-scale demand scoring to prevent any single node dominating coverage.
"""

import json
import math
from pathlib import Path
from typing import Optional

# Budget constraints
MAX_NODE_BUDGET_FRACTION = 0.20   # No node may exceed 20% of total budget
MIN_VIDEOS_PER_NODE = 3           # Every node guaranteed minimum 3 videos

# Tier video budget fractions (must sum to 1.0)
TIER_BUDGET_FRACTIONS = {1: 0.40, 2: 0.35, 3: 0.25}


class TreeNode:
    """Represents a single node in the knowledge tree: destination/city/category."""

    def __init__(
        self,
        node_id: str,
        destination: str,
        city: str,
        category: str,
        tier: int,
        min_videos: int = MIN_VIDEOS_PER_NODE,
        max_videos: int = 20,
    ) -> None:
        if tier not in (1, 2, 3):
            raise ValueError(f"Tier must be 1, 2, or 3 — got {tier}")
        self.node_id = node_id          # e.g. "japan/tokyo/cuisine"
        self.destination = destination  # e.g. "japan"
        self.city = city                # e.g. "tokyo"
        self.category = category        # e.g. "cuisine"
        self.tier = tier
        self.min_videos = min_videos
        self.max_videos = max_videos
        self.current_videos: int = 0
        self.demand_score: float = 0.5  # 0.0-1.0, starts neutral
        self.allocated_budget: int = min_videos
        self.retrievals_7d: int = 0
        self.retrievals_30d: int = 0
        self.avg_confidence: float = 1.0

    def to_dict(self) -> dict:
        return {
            "node_id": self.node_id,
            "destination": self.destination,
            "city": self.city,
            "category": self.category,
            "tier": self.tier,
            "min_videos": self.min_videos,
            "max_videos": self.max_videos,
            "current_videos": self.current_videos,
            "demand_score": self.demand_score,
            "allocated_budget": self.allocated_budget,
            "retrievals_7d": self.retrievals_7d,
            "retrievals_30d": self.retrievals_30d,
            "avg_confidence": self.avg_confidence,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "TreeNode":
        node = cls(
            node_id=data["node_id"],
            destination=data["destination"],
            city=data["city"],
            category=data["category"],
            tier=data["tier"],
            min_videos=data.get("min_videos", MIN_VIDEOS_PER_NODE),
            max_videos=data.get("max_videos", 20),
        )
        node.current_videos = data.get("current_videos", 0)
        node.demand_score = data.get("demand_score", 0.5)
        node.allocated_budget = data.get("allocated_budget", node.min_videos)
        node.retrievals_7d = data.get("retrievals_7d", 0)
        node.retrievals_30d = data.get("retrievals_30d", 0)
        node.avg_confidence = data.get("avg_confidence", 1.0)
        return node

    @property
    def needs_more_content(self) -> bool:
        return self.current_videos < self.allocated_budget

    @property
    def videos_needed(self) -> int:
        return max(0, self.allocated_budget - self.current_videos)


class KnowledgeTree:
    """Manages the 3-tier destination taxonomy and video budget allocation.

    Loads base taxonomy from ``scripts/tree_config/{destination}.json``.
    Budget is allocated using log-scaled demand scores to prevent the
    80/20 skew where popular nodes monopolise all content.

    Usage::

        tree = KnowledgeTree.load("japan")
        nodes = tree.get_nodes_needing_content()
        for node in nodes:
            print(node.node_id, node.videos_needed)
        tree.save()
    """

    def __init__(self, destination: str, nodes: list[TreeNode]) -> None:
        self.destination = destination
        self._nodes: dict[str, TreeNode] = {n.node_id: n for n in nodes}

    # ── Loading ────────────────────────────────────────────────────────────────

    @classmethod
    def load(cls, destination: str, config_dir: Optional[Path] = None) -> "KnowledgeTree":
        """Load tree from static config, merging runtime state if saved previously.

        Args:
            destination: e.g. "japan"
            config_dir:  Override path to tree_config directory.
        """
        if config_dir is None:
            config_dir = Path(__file__).parent.parent.parent / "scripts" / "tree_config"

        config_path = config_dir / f"{destination}.json"
        if not config_path.exists():
            raise FileNotFoundError(f"Tree config not found: {config_path}")

        config = json.loads(config_path.read_text())
        nodes: list[TreeNode] = []

        for city_data in config.get("cities", []):
            city = city_data["name"]
            tier = city_data["tier"]
            for category in city_data.get("categories", []):
                node_id = f"{destination}/{city}/{category}"
                node = TreeNode(
                    node_id=node_id,
                    destination=destination,
                    city=city,
                    category=category,
                    tier=tier,
                    min_videos=city_data.get("min_videos", MIN_VIDEOS_PER_NODE),
                    max_videos=city_data.get("max_videos", 20),
                )
                nodes.append(node)

        tree = cls(destination=destination, nodes=nodes)
        tree.rebalance_budgets()
        return tree

    # ── Accessors ──────────────────────────────────────────────────────────────

    @property
    def nodes(self) -> list[TreeNode]:
        return list(self._nodes.values())

    def get_node(self, node_id: str) -> Optional[TreeNode]:
        return self._nodes.get(node_id)

    def get_nodes_by_tier(self, tier: int) -> list[TreeNode]:
        return [n for n in self._nodes.values() if n.tier == tier]

    def get_nodes_needing_content(self) -> list[TreeNode]:
        """Return nodes where current_videos < allocated_budget, sorted by deficit."""
        needing = [n for n in self._nodes.values() if n.needs_more_content]
        return sorted(needing, key=lambda n: n.videos_needed, reverse=True)

    def get_low_confidence_nodes(self, threshold: float = 0.7) -> list[TreeNode]:
        """Return nodes with avg retrieval confidence below threshold."""
        return [n for n in self._nodes.values() if n.avg_confidence < threshold]

    def get_inactive_nodes(self, days: int = 7) -> list[TreeNode]:
        """Return nodes with zero retrievals in the past N days."""
        if days == 7:
            return [n for n in self._nodes.values() if n.retrievals_7d == 0]
        return [n for n in self._nodes.values() if n.retrievals_30d == 0]

    # ── Budget allocation ──────────────────────────────────────────────────────

    def rebalance_budgets(self) -> None:
        """Recalculate allocated_budget for all nodes using log-scaled demand scores.

        Enforces:
        - No node exceeds MAX_NODE_BUDGET_FRACTION of total budget
        - Every node gets at least MIN_VIDEOS_PER_NODE
        - Tier budget fractions are respected (40% T1, 35% T2, 25% T3)
        """
        total_budget = sum(n.max_videos for n in self._nodes.values())

        for tier in (1, 2, 3):
            tier_nodes = self.get_nodes_by_tier(tier)
            if not tier_nodes:
                continue

            tier_budget = int(total_budget * TIER_BUDGET_FRACTIONS[tier])
            max_per_node = int(total_budget * MAX_NODE_BUDGET_FRACTION)

            # Log-scale demand scores to flatten the long tail
            log_scores = [math.log1p(n.demand_score * 10) for n in tier_nodes]
            total_log = sum(log_scores) or 1.0

            for node, log_score in zip(tier_nodes, log_scores):
                raw = int(tier_budget * (log_score / total_log))
                # Apply floor and cap
                node.allocated_budget = max(node.min_videos, min(raw, max_per_node))

    def update_demand_score(self, node_id: str, score: float) -> None:
        """Update demand score for a node and rebalance budgets."""
        node = self._nodes.get(node_id)
        if node:
            node.demand_score = max(0.0, min(1.0, score))
            self.rebalance_budgets()

    def update_metrics(
        self,
        node_id: str,
        retrievals_7d: Optional[int] = None,
        retrievals_30d: Optional[int] = None,
        avg_confidence: Optional[float] = None,
        current_videos: Optional[int] = None,
    ) -> None:
        """Update performance metrics for a node."""
        node = self._nodes.get(node_id)
        if not node:
            return
        if retrievals_7d is not None:
            node.retrievals_7d = retrievals_7d
        if retrievals_30d is not None:
            node.retrievals_30d = retrievals_30d
        if avg_confidence is not None:
            node.avg_confidence = avg_confidence
        if current_videos is not None:
            node.current_videos = current_videos

    def add_node(self, node: TreeNode) -> None:
        """Add a dynamically discovered node (e.g. from trending topics)."""
        self._nodes[node.node_id] = node
        self.rebalance_budgets()

    def retire_node(self, node_id: str) -> bool:
        """Remove a node with zero activity. Returns True if removed."""
        if node_id in self._nodes:
            del self._nodes[node_id]
            return True
        return False

    # ── Serialisation ──────────────────────────────────────────────────────────

    def to_dict(self) -> dict:
        return {
            "destination": self.destination,
            "nodes": [n.to_dict() for n in self._nodes.values()],
        }

    def generate_rebalancing_report(self) -> str:
        """Generate a human-readable monthly rebalancing report."""
        lines = [f"## Rebalancing Report — {self.destination}\n"]

        low_conf = self.get_low_confidence_nodes()
        if low_conf:
            lines.append("### Nodes needing more content (confidence < 0.7):")
            for n in low_conf:
                lines.append(f"  - {n.node_id} (confidence={n.avg_confidence:.2f})")

        inactive = self.get_inactive_nodes(days=30)
        if inactive:
            lines.append("\n### Inactive nodes (0 retrievals in 30d — candidates to retire):")
            for n in inactive:
                lines.append(f"  - {n.node_id}")

        lines.append("\n### Budget allocation:")
        lines.append(f"  {'Node':<45} {'Tier':>4} {'Budget':>6} {'Current':>7} {'Demand':>6}")
        lines.append("  " + "-" * 72)
        for n in sorted(self._nodes.values(), key=lambda x: (x.tier, x.node_id)):
            lines.append(
                f"  {n.node_id:<45} {n.tier:>4} {n.allocated_budget:>6} "
                f"{n.current_videos:>7} {n.demand_score:>6.2f}"
            )

        return "\n".join(lines)
