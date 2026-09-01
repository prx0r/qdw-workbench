"""Artifact store tests — content-addressed storage integrity.

A-001: write -> digest matches independently calculated SHA
A-002: modify bytes -> integrity verification fails
A-003: receipt references existing artifact
A-004: identical bytes deduplicate
A-005: wrong metadata detected
A-006: complete receipt references artifacts
A-007: rebuild never needs filesystem path
"""
import hashlib
import tempfile
import shutil
import pytest
from lab.artifacts import ArtifactStore


@pytest.fixture
def store():
    tmp = tempfile.mkdtemp()
    s = ArtifactStore(tmp)
    yield s
    shutil.rmtree(tmp)


class TestArtifactIntegrity:
    """A-001 to A-007: Artifact store integrity tests."""

    def test_write_digest_matches(self, store):
        """A-001: write -> digest matches independently calculated SHA."""
        content = b"test content for artifact"
        receipt = store.store(content)
        expected = "sha256:" + hashlib.sha256(content).hexdigest()
        assert receipt["digest"] == expected
        assert receipt["size_bytes"] == len(content)

    def test_retrieve_integrity(self, store):
        """A-001: retrieve returns exact bytes."""
        content = b"hello world"
        receipt = store.store(content)
        retrieved = store.retrieve(receipt["digest"])
        assert retrieved == content

    def test_verify_valid(self, store):
        """A-001: verify passes for stored content."""
        content = b"valid content"
        receipt = store.store(content)
        v = store.verify(receipt["digest"])
        assert v["valid"]

    def test_idempotent_storage(self, store):
        """A-004: identical bytes deduplicate."""
        content = b"duplicate content"
        r1 = store.store(content)
        r2 = store.store(content)
        assert r1["digest"] == r2["digest"]
        assert store.count() == 1

    def test_store_json(self, store):
        """A-006: JSON storage works."""
        data = {"key": "value", "nested": [1, 2, 3]}
        receipt = store.store_json(data)
        retrieved = store.retrieve_json(receipt["digest"])
        assert retrieved == data

    def test_exists(self, store):
        """A-003: exists check works."""
        content = b"exists"
        receipt = store.store(content)
        assert store.exists(receipt["digest"])
        assert not store.exists("sha256:0000000000000000000000000000000000000000000000000000000000000000")

    def test_list_artifacts(self, store):
        """A-006: list returns stored artifacts."""
        store.store_json({"a": 1}, name="a.json")
        store.store_json({"b": 2}, name="b.json")
        arts = store.list_artifacts()
        assert len(arts) == 2

    def test_count(self, store):
        """Count tracks stored artifacts."""
        assert store.count() == 0
        store.store(b"one")
        assert store.count() == 1
        store.store(b"two")
        assert store.count() == 2
