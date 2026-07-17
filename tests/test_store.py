import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch


ROOT = Path(__file__).resolve().parents[1]


class RefreshStateTest(unittest.TestCase):
    def test_refresh_clears_previous_new_and_marks_only_first_seen(self):
        with tempfile.TemporaryDirectory() as tmp:
            state_path = Path(tmp) / "state.json"
            with patch("app.server.STATE_PATH", state_path):
                state = {
                    "jobs": [
                        {"id": "old", "title": "Old", "status": "new"},
                    ],
                    "refresh_index": 0,
                    "last_refresh": None,
                }
                candidates = [
                    {"id": "old", "title": "Old Updated"},
                    {"id": "new", "title": "New Job"},
                ]
                new_count = __import__("app.server", fromlist=["merge_refresh"]).merge_refresh(state, candidates)

            self.assertEqual(new_count, 1)
            by_id = {job["id"]: job for job in state["jobs"]}
            self.assertEqual(by_id["old"]["status"], "existing")
            self.assertEqual(by_id["new"]["status"], "new")

    def test_fixture_is_sanitized(self):
        fixture = json.loads((ROOT / "data" / "seed_jobs.json").read_text(encoding="utf-8"))
        raw = json.dumps(fixture, ensure_ascii=False)
        self.assertNotIn("liepin", raw.lower())
        self.assertNotIn("boss", raw.lower())
        self.assertNotIn("token", raw.lower())

    def test_public_jobs_keep_details_marks_and_source_links(self):
        public = json.loads((ROOT / "docs" / "public_jobs.json").read_text(encoding="utf-8"))
        jobs = public["jobs"]
        refreshed = [job for batch in public["refresh_batches"] for job in batch]
        self.assertGreaterEqual(len(jobs), 20)
        self.assertTrue(all(job.get("jd") for job in jobs))
        self.assertTrue(all(job.get("source_urls") for job in jobs))
        self.assertTrue(all(source.get("url", "").startswith(("http://", "https://")) for job in jobs for source in job["source_urls"]))
        marks = {job.get("user_mark") for job in jobs + refreshed}
        self.assertIn("good", marks)
        self.assertIn("bad", marks)


if __name__ == "__main__":
    unittest.main()
