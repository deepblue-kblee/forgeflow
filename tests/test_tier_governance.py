#!/usr/bin/env python3
"""
Unit tests for Tier Governance & Dynamic Validation Rules
"""

import unittest
from forgeflow.validator import TierRules


class TestTierGovernance(unittest.TestCase):
    def test_tier_names(self):
        self.assertIn("Minor", TierRules.get_tier_name(1))
        self.assertIn("Standard", TierRules.get_tier_name(2))
        self.assertIn("Critical", TierRules.get_tier_name(3))

    def test_required_docs(self):
        # Tier 1 uses CHANGE_NOTE.md single artifact
        tier1_docs = TierRules.get_required_docs(1)
        self.assertEqual(tier1_docs, ["CHANGE_NOTE.md"])

        # Tier 2, 3, and default (None) use standard release artifacts
        for tier in [2, 3, None]:
            docs = TierRules.get_required_docs(tier)
            self.assertIn("PRD.md", docs)
            self.assertIn("DESIGN.md", docs)
            self.assertIn("QA_SIGNOFF.md", docs)
            self.assertIn("COMPLETION_REPORT.md", docs)


if __name__ == "__main__":
    unittest.main()
