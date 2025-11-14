import unittest
from datetime import datetime, timedelta
from documentflow.storage import StorageLocation, DocumentStorage, ArchiveService
from documentflow.security import QuotaManager
from documentflow.documents import Document, DocumentAttachment, DocumentMetadata
from documentflow.users import User
from documentflow.workflow import WorkflowState
from documentflow.exceptions import DocumentNotFoundError


class TestStorage(unittest.TestCase):
    def setUp(self):
        """Set up test fixtures"""
        self.user = User(id="u1", login="testuser", display_name="Test User")
    
    def test_storage_location_validate(self):
        """Test storage location path validation"""
        loc1 = StorageLocation(name="valid", base_path="/tmp/storage")
        self.assertTrue(loc1.validate_path())
        
        loc2 = StorageLocation(name="empty", base_path="")
        self.assertFalse(loc2.validate_path())
    
    def test_storage_location_get_full_path(self):
        """Test getting full path to file"""
        loc = StorageLocation(name="test", base_path="/var/storage")
        full_path = loc.get_full_path("document.pdf")
        self.assertEqual(full_path, "/var/storage/document.pdf")
    
    def test_document_storage_save_and_get(self):
        """Test saving and retrieving documents"""
        loc = StorageLocation(name="test", base_path="/tmp")
        quota = QuotaManager(max_bytes=1_000_000)
        storage = DocumentStorage(location=loc, quota=quota)
        
        doc = Document(
            id="d1",
            number="DOC-001",
            title="Test Document",
            author=self.user,
            status=WorkflowState.NEW,
            metadata=DocumentMetadata()
        )
        
        storage.save(doc)
        retrieved = storage.get("DOC-001")
        self.assertEqual(retrieved.number, "DOC-001")
        self.assertEqual(retrieved.title, "Test Document")
    
    def test_document_storage_exists(self):
        """Test checking if document exists"""
        loc = StorageLocation(name="test", base_path="/tmp")
        quota = QuotaManager(max_bytes=1_000_000)
        storage = DocumentStorage(location=loc, quota=quota)
        
        doc = Document(
            id="d2",
            number="DOC-002",
            title="Test Document",
            author=self.user,
            status=WorkflowState.NEW,
            metadata=DocumentMetadata()
        )
        
        self.assertFalse(storage.exists("DOC-002"))
        storage.save(doc)
        self.assertTrue(storage.exists("DOC-002"))
    
    def test_document_storage_not_found(self):
        """Test getting non-existent document"""
        loc = StorageLocation(name="test", base_path="/tmp")
        quota = QuotaManager(max_bytes=1_000_000)
        storage = DocumentStorage(location=loc, quota=quota)
        
        with self.assertRaises(DocumentNotFoundError):
            storage.get("NON-EXISTENT")
    
    def test_document_storage_delete(self):
        """Test deleting documents"""
        loc = StorageLocation(name="test", base_path="/tmp")
        quota = QuotaManager(max_bytes=1_000_000)
        storage = DocumentStorage(location=loc, quota=quota)
        
        doc = Document(
            id="d3",
            number="DOC-003",
            title="Test Document",
            author=self.user,
            status=WorkflowState.NEW,
            metadata=DocumentMetadata()
        )
        
        storage.save(doc)
        self.assertTrue(storage.exists("DOC-003"))
        
        storage.delete("DOC-003")
        self.assertFalse(storage.exists("DOC-003"))
        
        # Test deleting non-existent document (should not raise)
        storage.delete("NON-EXISTENT")
    
    def test_document_storage_count(self):
        """Test counting documents"""
        loc = StorageLocation(name="test", base_path="/tmp")
        quota = QuotaManager(max_bytes=1_000_000)
        storage = DocumentStorage(location=loc, quota=quota)
        
        self.assertEqual(storage.count_documents(), 0)
        
        for i in range(3):
            doc = Document(
                id=f"d{i}",
                number=f"DOC-{i:03d}",
                title=f"Document {i}",
                author=self.user,
                status=WorkflowState.NEW,
                metadata=DocumentMetadata()
            )
            storage.save(doc)
        
        self.assertEqual(storage.count_documents(), 3)
    
    def test_document_storage_get_all_numbers(self):
        """Test getting all document numbers"""
        loc = StorageLocation(name="test", base_path="/tmp")
        quota = QuotaManager(max_bytes=1_000_000)
        storage = DocumentStorage(location=loc, quota=quota)
        
        numbers = ["DOC-100", "DOC-200", "DOC-300"]
        for num in numbers:
            doc = Document(
                id=num,
                number=num,
                title="Test",
                author=self.user,
                status=WorkflowState.NEW,
                metadata=DocumentMetadata()
            )
            storage.save(doc)
        
        all_numbers = storage.get_all_numbers()
        self.assertEqual(len(all_numbers), 3)
        for num in numbers:
            self.assertIn(num, all_numbers)
    
    def test_document_storage_clear(self):
        """Test clearing all documents"""
        loc = StorageLocation(name="test", base_path="/tmp")
        quota = QuotaManager(max_bytes=1_000_000)
        storage = DocumentStorage(location=loc, quota=quota)
        
        doc = Document(
            id="d1",
            number="DOC-001",
            title="Test",
            author=self.user,
            status=WorkflowState.NEW,
            metadata=DocumentMetadata()
        )
        storage.save(doc)
        
        self.assertEqual(storage.count_documents(), 1)
        storage.clear()
        self.assertEqual(storage.count_documents(), 0)
    
    def test_archive_service_archive(self):
        """Test archiving a document"""
        loc = StorageLocation(name="test", base_path="/tmp")
        quota = QuotaManager(max_bytes=1_000_000)
        storage = DocumentStorage(location=loc, quota=quota)
        
        doc = Document(
            id="d1",
            number="DOC-001",
            title="Test",
            author=self.user,
            status=WorkflowState.APPROVED,
            metadata=DocumentMetadata()
        )
        storage.save(doc)
        
        archive_service = ArchiveService(storage=storage)
        archive_service.archive_document("DOC-001")
        
        retrieved = storage.get("DOC-001")
        self.assertEqual(retrieved.status, WorkflowState.ARCHIVED)
    
    def test_archive_service_restore(self):
        """Test restoring an archived document"""
        loc = StorageLocation(name="test", base_path="/tmp")
        quota = QuotaManager(max_bytes=1_000_000)
        storage = DocumentStorage(location=loc, quota=quota)
        
        doc = Document(
            id="d2",
            number="DOC-002",
            title="Test",
            author=self.user,
            status=WorkflowState.ARCHIVED,
            metadata=DocumentMetadata()
        )
        storage.save(doc)
        
        archive_service = ArchiveService(storage=storage)
        archive_service.restore_document("DOC-002")
        
        retrieved = storage.get("DOC-002")
        self.assertEqual(retrieved.status, WorkflowState.NEW)
    
    def test_archive_service_get_archived(self):
        """Test getting all archived documents"""
        loc = StorageLocation(name="test", base_path="/tmp")
        quota = QuotaManager(max_bytes=1_000_000)
        storage = DocumentStorage(location=loc, quota=quota)
        
        # Create mix of archived and non-archived documents
        doc1 = Document(
            id="d1",
            number="DOC-001",
            title="Test",
            author=self.user,
            status=WorkflowState.ARCHIVED,
            metadata=DocumentMetadata()
        )
        doc2 = Document(
            id="d2",
            number="DOC-002",
            title="Test",
            author=self.user,
            status=WorkflowState.NEW,
            metadata=DocumentMetadata()
        )
        doc3 = Document(
            id="d3",
            number="DOC-003",
            title="Test",
            author=self.user,
            status=WorkflowState.ARCHIVED,
            metadata=DocumentMetadata()
        )
        
        storage.save(doc1)
        storage.save(doc2)
        storage.save(doc3)
        
        archive_service = ArchiveService(storage=storage)
        archived_docs = archive_service.get_archived_documents()
        
        self.assertEqual(len(archived_docs), 2)
        archived_numbers = [doc.number for doc in archived_docs]
        self.assertIn("DOC-001", archived_numbers)
        self.assertIn("DOC-003", archived_numbers)
        self.assertNotIn("DOC-002", archived_numbers)
    
    def test_archive_service_can_delete(self):
        """Test checking if archived document can be deleted"""
        loc = StorageLocation(name="test", base_path="/tmp")
        quota = QuotaManager(max_bytes=1_000_000)
        storage = DocumentStorage(location=loc, quota=quota)
        
        archive_service = ArchiveService(storage=storage, archive_retention_days=30)
        
        # Document not archived
        doc1 = Document(
            id="d1",
            number="DOC-001",
            title="Test",
            author=self.user,
            status=WorkflowState.NEW,
            metadata=DocumentMetadata()
        )
        self.assertFalse(archive_service.can_delete_archived(doc1))
        
        # Archived document but too recent
        doc2 = Document(
            id="d2",
            number="DOC-002",
            title="Test",
            author=self.user,
            status=WorkflowState.ARCHIVED,
            metadata=DocumentMetadata()
        )
        self.assertFalse(archive_service.can_delete_archived(doc2))
        
        # Old archived document that can be deleted
        doc3 = Document(
            id="d3",
            number="DOC-003",
            title="Test",
            author=self.user,
            status=WorkflowState.ARCHIVED,
            metadata=DocumentMetadata()
        )
        # Simulate old document by setting created_at to past
        doc3.created_at = datetime.utcnow() - timedelta(days=40)
        self.assertTrue(archive_service.can_delete_archived(doc3))
    
    def test_storage_attachment_quota_exceeded(self):
        """Test storing attachment when quota is exceeded"""
        from documentflow.exceptions import StorageLimitExceededError
        
        loc = StorageLocation(name="test", base_path="/tmp")
        quota = QuotaManager(max_bytes=100)
        storage = DocumentStorage(location=loc, quota=quota)
        
        doc = Document(
            id="d1",
            number="DOC-001",
            title="Test",
            author=self.user,
            status=WorkflowState.NEW,
            metadata=DocumentMetadata()
        )
        storage.save(doc)
        
        # Try to store attachment that exceeds quota
        large_att = DocumentAttachment(
            filename="large.pdf",
            content_type="application/pdf",
            size=200,
            checksum="abc"
        )
        
        with self.assertRaises(StorageLimitExceededError):
            storage.store_attachment(doc, large_att)


if __name__ == "__main__":
    unittest.main()
