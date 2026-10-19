"""
Unit tests for duplicate detection (exact and near duplicate grouping).
"""

import tempfile
from pathlib import Path
from backend.ai.duplicate_detector import DuplicateDetector
from backend.database.connection import init_db
from backend.database.repository import Repository


def test_exact_duplicate_detection():
    with tempfile.TemporaryDirectory(ignore_cleanup_errors=True) as tmpdir:
        db_path = Path(tmpdir) / "test_dup.db"
        init_db(db_path)
        repo = Repository(str(db_path))
        detector = DuplicateDetector(repository=repo)

        # 1. First event
        res1 = detector.check_duplicate(
            package_name="com.bank.app",
            title="Account Alert",
            text="Debited USD 20.00 at Store",
        )
        assert res1.is_duplicate is False
        assert res1.duplicate_group_id is not None

        # Seed this into repository as an ingested notification
        repo.create_notification({
            "event_id": "evt-dup-1",
            "package_name": "com.bank.app",
            "title": "Account Alert",
            "text": "Debited USD 20.00 at Store",
            "category": "transactional",
            "priority_score": 50.0,
            "duplicate_group_id": res1.duplicate_group_id,
            "is_duplicate": False,
            "received_at": "2026-10-19T10:00:00Z",
        })

        # 2. Second event with identical package, title, and text
        res2 = detector.check_duplicate(
            package_name="com.bank.app",
            title="Account Alert",
            text="Debited USD 20.00 at Store",
        )
        assert res2.is_duplicate is True
        assert res2.duplicate_group_id == res1.duplicate_group_id
        assert res2.grouping_method == "exact"
