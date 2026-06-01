from pathlib import Path

from backend.app.services import document_registry


def _mock_registry_fs(monkeypatch, initial_files: dict[str, str] | None = None):
    files = dict(initial_files or {})

    def _normalized(path: Path) -> str:
        return str(path)

    def _exists(self: Path) -> bool:
        path = _normalized(self)
        if path in files:
            return True
        return any(name.startswith(f"{path}\\") for name in files)

    def _mkdir(self: Path, parents: bool = False, exist_ok: bool = False) -> None:
        return None

    def _write_text(self: Path, data: str, encoding: str | None = None) -> int:
        files[_normalized(self)] = data
        return len(data)

    def _read_text(self: Path, encoding: str | None = None) -> str:
        return files[_normalized(self)]

    def _replace(self: Path, target: Path) -> Path:
        files[_normalized(target)] = files.pop(_normalized(self))
        return target

    monkeypatch.setattr(Path, "exists", _exists)
    monkeypatch.setattr(Path, "mkdir", _mkdir)
    monkeypatch.setattr(Path, "write_text", _write_text)
    monkeypatch.setattr(Path, "read_text", _read_text)
    monkeypatch.setattr(Path, "replace", _replace)
    return files


def test_load_documents_handles_corrupted_registry(monkeypatch):
    registry_path = Path("virtual-documents.json")
    _mock_registry_fs(monkeypatch, {str(registry_path): "{not-valid-json"})
    monkeypatch.setattr(document_registry, "REGISTRY_PATH", registry_path)

    assert document_registry.load_documents() == []


def test_add_document_record_recovers_after_corrupted_registry(monkeypatch):
    registry_path = Path("virtual-documents.json")
    files = _mock_registry_fs(monkeypatch, {str(registry_path): "[]"})
    monkeypatch.setattr(document_registry, "REGISTRY_PATH", registry_path)

    document_registry.save_documents(
        [
            {
                "document_id": "older-doc",
                "filename": "older.pdf",
                "chunks_created": 1,
                "created_at": "2026-01-01T08:00:00+00:00",
                "file_size_bytes": 128,
                "status": "ready",
            }
        ]
    )

    document_registry.add_document_record(
        {
            "document_id": "newer-doc",
            "filename": "newer.pdf",
            "chunks_created": 2,
            "created_at": "2026-01-02T08:00:00+00:00",
            "file_size_bytes": 256,
            "status": "ready",
        }
    )

    assert '"document_id": "newer-doc"' in files[str(registry_path)]
    assert document_registry.load_documents()[0]["document_id"] == "newer-doc"
