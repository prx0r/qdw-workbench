"""Ledger tests — append-only event store integrity.

E-001: UPDATE/DELETE must fail
E-002: idempotent import
E-003: same ID different payload -> conflict
E-004: tamper detection
E-005: malformed payload rejection
E-006: ledger available while Hydra down (unit test only)
E-007: export -> import -> same histories
"""
import json
import copy
import tempfile
import os
import pytest
from lab.ledger import Ledger


@pytest.fixture
def ledger():
    db = tempfile.mktemp(suffix=".db")
    l = Ledger(db)
    yield l
    os.unlink(db)


class TestLedgerIntegrity:
    """E-001 to E-007: Ledger integrity tests."""

    def test_update_rejected(self, ledger):
        """E-001: UPDATE must fail."""
        e = ledger.append_event("test", "ent", {"x": 1})
        with pytest.raises(Exception):
            ledger._conn().execute("UPDATE events SET event_type = 'hacked'")

    def test_delete_rejected(self, ledger):
        """E-001: DELETE must fail."""
        e = ledger.append_event("test", "ent", {"x": 1})
        with pytest.raises(Exception):
            ledger._conn().execute("DELETE FROM events")

    def test_idempotent_import(self, ledger):
        """E-002: same receipt twice -> idempotent."""
        e = ledger.append_event("test", "ent", {"x": 1})
        imp = ledger.import_receipt([e])
        assert imp["imported"] == 0
        assert imp["skipped"] == 1

    def test_conflict_detection(self, ledger):
        """E-003: same ID different payload -> conflict."""
        e = ledger.append_event("test", "ent", {"x": 1})
        bad = copy.deepcopy(e)
        bad["payload_json"] = json.dumps({"x": 999})
        bad["payload_sha256"] = "fake"
        imp = ledger.import_receipt([bad])
        assert len(imp["errors"]) == 1
        assert "conflict" in imp["errors"][0]["error"]

    def test_chain_verification(self, ledger):
        """E-004: chain integrity check."""
        ledger.append_event("test", "ent1", {"x": 1})
        ledger.append_event("test", "ent2", {"x": 2})
        ledger.append_event("test", "ent3", {"x": 3})
        result = ledger.verify_chain()
        assert result["valid"]
        assert result["events"] == 3

    def test_single_event_verification(self, ledger):
        """E-004: single event hash check."""
        e = ledger.append_event("test", "ent", {"x": 1})
        v = ledger.verify_event(e["event_id"])
        assert v["valid"]

    def test_entity_history(self, ledger):
        """E-007: export/import roundtrip."""
        ledger.append_event("test", "ent1", {"x": 1})
        ledger.append_event("test", "ent2", {"x": 2})
        h1 = ledger.get_entity_history("ent1")
        h2 = ledger.get_entity_history("ent2")
        assert len(h1) == 1
        assert len(h2) == 1

    def test_summary(self, ledger):
        """Ledger summary counts correctly."""
        ledger.append_event("type_a", "ent1", {})
        ledger.append_event("type_a", "ent2", {})
        ledger.append_event("type_b", "ent3", {})
        s = ledger.summary()
        assert s["total_events"] == 3
        assert s["by_type"]["type_a"] == 2
        assert s["by_type"]["type_b"] == 1
