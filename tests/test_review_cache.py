#!/usr/bin/env python3
"""
Unit tests for ReviewCacheManager and incremental AST review caching.
"""

import json
import tempfile
import unittest
from pathlib import Path

from forgeflow.review_cache import ReviewCacheManager
from forgeflow.reviewer import ReviewEngine
from forgeflow.smell_detector import CodeSmell, SmellDetector


class TestReviewCacheManager(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.root = Path(self.temp_dir.name)
        self.cache_file = self.root / ".forgeflow" / "cache" / "review_cache.json"

    def tearDown(self):
        self.temp_dir.cleanup()

    def test_cache_miss_on_first_access(self):
        cache_mgr = ReviewCacheManager(repo_root=self.root, cache_file=self.cache_file)
        sample_path = self.root / "sample.py"
        content = "def add(a: int, b: int) -> int:\n    return a + b\n"

        res = cache_mgr.get(sample_path, content)
        self.assertIsNone(res)
        self.assertEqual(cache_mgr.misses, 1)
        self.assertEqual(cache_mgr.hits, 0)

    def test_cache_hit_after_put_and_save(self):
        cache_mgr = ReviewCacheManager(repo_root=self.root, cache_file=self.cache_file)
        sample_path = self.root / "sample.py"
        content = "def add(a: int, b: int) -> int:\n    return a + b\n"
        smells = [
            CodeSmell(
                file_path=str(sample_path),
                line_no=1,
                smell_type="TestSmell",
                severity="INFO",
                message="Test",
                suggestion="None",
            )
        ]

        cache_mgr.put(sample_path, content, smells)
        cache_mgr.save()
        self.assertTrue(self.cache_file.exists())

        # Reload cache from disk
        reloaded_cache = ReviewCacheManager(repo_root=self.root, cache_file=self.cache_file)
        cached_smells = reloaded_cache.get(sample_path, content)
        self.assertIsNotNone(cached_smells)
        self.assertEqual(len(cached_smells), 1)
        self.assertEqual(cached_smells[0].smell_type, "TestSmell")
        self.assertEqual(reloaded_cache.hits, 1)

    def test_cache_invalidated_when_content_changes(self):
        cache_mgr = ReviewCacheManager(repo_root=self.root, cache_file=self.cache_file)
        sample_path = self.root / "sample.py"
        content_v1 = "x = 1\n"
        content_v2 = "x = 2\n"

        cache_mgr.put(sample_path, content_v1, [])
        cache_mgr.save()

        cached = cache_mgr.get(sample_path, content_v2)
        self.assertIsNone(cached)
        self.assertEqual(cache_mgr.misses, 1)

    def test_cache_corrupted_file_fail_safe(self):
        self.cache_file.parent.mkdir(parents=True, exist_ok=True)
        self.cache_file.write_text("{corrupted json", encoding="utf-8")

        cache_mgr = ReviewCacheManager(repo_root=self.root, cache_file=self.cache_file)
        sample_path = self.root / "sample.py"
        res = cache_mgr.get(sample_path, "code")
        self.assertIsNone(res)
        self.assertEqual(cache_mgr.get_stats()["total_cached_files"], 0)

    def test_review_engine_integrates_cache(self):
        src_file = self.root / "src" / "sample.py"
        src_file.parent.mkdir(parents=True, exist_ok=True)
        src_file.write_text("def ok():\n    return 42\n", encoding="utf-8")

        engine = ReviewEngine(repo_root=self.root)
        # 1st run: Cache miss
        res1 = engine.run_review(targets=[src_file], no_cache=False)
        self.assertTrue(res1.passed)
        self.assertEqual(res1.cache_stats["misses"], 1)
        self.assertEqual(res1.cache_stats["hits"], 0)

        # 2nd run: Cache hit
        res2 = engine.run_review(targets=[src_file], no_cache=False)
        self.assertTrue(res2.passed)
        self.assertEqual(res2.cache_stats["hits"], 1)

        # 3rd run: with no_cache=True
        res3 = engine.run_review(targets=[src_file], no_cache=True)
        self.assertTrue(res3.passed)
        self.assertFalse(res3.cache_stats["enabled"])


if __name__ == "__main__":
    unittest.main()
