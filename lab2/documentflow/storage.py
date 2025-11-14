from __future__ import annotations
from dataclasses import dataclass, field
from typing import Dict
from .exceptions import DocumentNotFoundError
from .documents import Document, DocumentAttachment
from .security import QuotaManager

@dataclass
class StorageLocation:
    name: str
    base_path: str

@dataclass
class DocumentStorage:
    location: StorageLocation
    quota: QuotaManager
    _docs: Dict[str, Document] = field(default_factory=dict)
    _attachments: Dict[str, DocumentAttachment] = field(default_factory=dict)

    def save(self, doc: Document) -> None:
        self._docs[doc.number] = doc

    def get(self, number: str) -> Document:
        try:
            return self._docs[number]
        except KeyError as e:
            raise DocumentNotFoundError(number) from e

    def exists(self, number: str) -> bool:
        return number in self._docs

    def store_attachment(self, doc: Document, att: DocumentAttachment) -> None:
        if not self.quota.can_allocate(att.size):
            self.quota.allocate(att.size)  # вызовет исключение
        self._attachments[f"{doc.number}:{att.filename}"] = att
        self.quota.allocate(att.size)

    def archive(self, doc: Document) -> None:
        doc.archive()

@dataclass
class ArchiveService:
    storage: DocumentStorage
    def archive_document(self, number: str) -> None:
        doc = self.storage.get(number)
        self.storage.archive(doc)
    def restore_document(self, number: str) -> None:
        doc = self.storage.get(number)
        doc.restore()
