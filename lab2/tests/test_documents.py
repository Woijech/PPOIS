import unittest
from datetime import datetime, timedelta
from documentflow.users import User, Role, Organization, Department
from documentflow.documents import (
    Document, IncomingDocument, OutgoingDocument, ContractDocument, InvoiceDocument, 
    OrderDocument, DocumentRegistry, DocumentAttachment, DocumentMetadata, DocumentVersion,
    Signature, DigitalCertificate, DocumentHistoryRecord, DocumentLock
)
from documentflow.workflow import WorkflowState
from documentflow.exceptions import InvalidDocumentStatusError, DuplicateDocumentError, InvalidSignatureError, VersionConflictError

class TestDocuments(unittest.TestCase):
    def setUp(self):
        role = Role(name="REVIEWER", permissions={"approve"})
        org = Organization(name="Org", inn="123")
        dep = Department(name="IT", cost_center="42")
        self.user = User(id="u1", login="u1", display_name="U1", roles=[role], org=org, department=dep)

    def test_lsp(self):
        docs: list[Document] = [
            IncomingDocument(id="1", number="N1", title="A", author=self.user),
            OutgoingDocument(id="2", number="N2", title="B", author=self.user),
            ContractDocument(id="3", number="N3", title="C", author=self.user, effective_from=datetime.utcnow(), effective_to=datetime.utcnow()+timedelta(days=1)),
            InvoiceDocument(id="4", number="N4", title="D", author=self.user, amount_due=100),
            OrderDocument(id="5", number="N5", title="E", author=self.user),
        ]
        for d in docs:
            d.validate()
            if d.status == WorkflowState.NEW:
                d.approve()
                self.assertEqual(d.status, WorkflowState.APPROVED)

    def test_registry(self):
        reg = DocumentRegistry()
        reg.register("A")
        with self.assertRaises(DuplicateDocumentError):
            reg.register("A")
        self.assertTrue(reg.contains("A"))

    def test_signing(self):
        inv = InvoiceDocument(id="6", number="INV", title="Inv", author=self.user, amount_due=10)
        with self.assertRaises(InvalidSignatureError):
            inv.sign(self.user.id)
        inv.add_version("v1", self.user.id)
        inv.sign(self.user.id)
        self.assertTrue(inv.signatures)

    def test_archive_restore(self):
        doc = IncomingDocument(id="7", number="X", title="Doc", author=self.user)
        doc.archive()
        with self.assertRaises(InvalidDocumentStatusError):
            doc.archive()
        doc.restore()
        self.assertEqual(doc.status, WorkflowState.NEW)

    def test_attachments(self):
        doc = IncomingDocument(id="8", number="Y", title="Doc2", author=self.user)
        att = DocumentAttachment(filename="f.txt", content_type="text/plain", size=12, checksum="c")
        doc.add_attachment(att)
        self.assertEqual(len(doc.attachments), 1)
    
    def test_document_metadata(self):
        """Test document metadata operations"""
        metadata = DocumentMetadata()
        
        # Test add_tag
        metadata.add_tag("important")
        metadata.add_tag("urgent")
        self.assertEqual(len(metadata.tags), 2)
        
        # Test add duplicate tag (should not add)
        metadata.add_tag("important")
        self.assertEqual(len(metadata.tags), 2)
        
        # Test has_tag
        self.assertTrue(metadata.has_tag("important"))
        self.assertFalse(metadata.has_tag("not_present"))
        
        # Test remove_tag
        metadata.remove_tag("urgent")
        self.assertEqual(len(metadata.tags), 1)
        self.assertFalse(metadata.has_tag("urgent"))
        
        # Test remove non-existent tag (should not raise error)
        metadata.remove_tag("not_present")
        self.assertEqual(len(metadata.tags), 1)
    
    def test_document_attachment_methods(self):
        """Test document attachment methods"""
        # Test image attachment
        img_att = DocumentAttachment(
            filename="photo.jpg",
            content_type="image/jpeg",
            size=1024,
            checksum="abc123"
        )
        self.assertTrue(img_att.is_image())
        self.assertFalse(img_att.is_pdf())
        self.assertEqual(img_att.get_extension(), "jpg")
        
        # Test PDF attachment
        pdf_att = DocumentAttachment(
            filename="document.pdf",
            content_type="application/pdf",
            size=2048,
            checksum="def456"
        )
        self.assertFalse(pdf_att.is_image())
        self.assertTrue(pdf_att.is_pdf())
        self.assertEqual(pdf_att.get_extension(), "pdf")
        
        # Test file without extension
        no_ext_att = DocumentAttachment(
            filename="readme",
            content_type="text/plain",
            size=512,
            checksum="ghi789"
        )
        self.assertEqual(no_ext_att.get_extension(), "")
    
    def test_document_version_methods(self):
        """Test document version methods"""
        version = DocumentVersion(
            number=1,
            content="Document content here",
            created_at=datetime.utcnow(),
            author_id="user1",
            comment="Initial version"
        )
        
        # Test get_content_length
        self.assertEqual(version.get_content_length(), len("Document content here"))
        
        # Test is_latest
        self.assertTrue(version.is_latest(1))
        self.assertFalse(version.is_latest(2))
    
    def test_signature_methods(self):
        """Test signature methods"""
        signature = Signature(
            user_id="user1",
            certificate_id="cert123",
            signed_at=datetime.utcnow()
        )
        
        # Test is_valid_for
        self.assertTrue(signature.is_valid_for("user1"))
        self.assertFalse(signature.is_valid_for("user2"))
    
    def test_digital_certificate_methods(self):
        """Test digital certificate methods"""
        now = datetime.utcnow()
        cert = DigitalCertificate(
            id="cert1",
            subject="CN=Test User",
            valid_from=now - timedelta(days=30),
            valid_to=now + timedelta(days=60),
            issuer="Test CA"
        )
        
        # Test is_valid
        self.assertTrue(cert.is_valid(now))
        self.assertFalse(cert.is_valid(now - timedelta(days=40)))
        self.assertFalse(cert.is_valid(now + timedelta(days=70)))
        
        # Test days_until_expiry
        days = cert.days_until_expiry()
        self.assertTrue(50 <= days <= 60)  # Should be around 60 days
        
        # Test is_expiring_soon
        self.assertFalse(cert.is_expiring_soon(30))  # 60 days remaining, not expiring soon
        self.assertTrue(cert.is_expiring_soon(90))  # 60 days < 90, expiring soon
        
        # Test expired certificate
        expired_cert = DigitalCertificate(
            id="cert2",
            subject="CN=Expired",
            valid_from=now - timedelta(days=100),
            valid_to=now - timedelta(days=10),
            issuer="Test CA"
        )
        self.assertFalse(expired_cert.is_expiring_soon())  # Already expired
    
    def test_document_history_record(self):
        """Test document history record"""
        record = DocumentHistoryRecord(
            event="document:created",
            actor_id="user1",
            occurred_at=datetime.utcnow(),
            details="Document was created"
        )
        
        # Test get_event_type
        self.assertEqual(record.get_event_type(), "document")
        
        # Test simple event without colon
        simple_record = DocumentHistoryRecord(
            event="approved",
            actor_id="user2",
            occurred_at=datetime.utcnow()
        )
        self.assertEqual(simple_record.get_event_type(), "approved")
    
    def test_document_lock(self):
        """Test document lock"""
        lock = DocumentLock(
            owner_id="user1",
            acquired_at=datetime.utcnow() - timedelta(seconds=30)
        )
        
        # Test get_lock_duration
        duration = lock.get_lock_duration()
        self.assertTrue(duration >= 30)
    
    def test_document_lock_unlock(self):
        """Test document locking and unlocking"""
        doc = IncomingDocument(id="9", number="LOCK-1", title="Lock Test", author=self.user)
        
        # Lock document
        doc.lock("user1")
        self.assertIsNotNone(doc._lock)
        self.assertEqual(doc._lock.owner_id, "user1")
        
        # Try to lock by same user (should succeed)
        doc.lock("user1")
        
        # Try to lock by different user (should fail)
        with self.assertRaises(VersionConflictError):
            doc.lock("user2")
        
        # Unlock by wrong user (should fail)
        with self.assertRaises(VersionConflictError):
            doc.unlock("user2")
        
        # Unlock by correct user (should succeed)
        doc.unlock("user1")
        self.assertIsNone(doc._lock)
    
    def test_document_registry_methods(self):
        """Test additional document registry methods"""
        reg = DocumentRegistry()
        
        # Test initial count
        self.assertEqual(reg.count(), 0)
        
        # Register documents
        reg.register("DOC-001")
        reg.register("DOC-002")
        reg.register("DOC-003")
        
        self.assertEqual(reg.count(), 3)
        self.assertTrue(reg.contains("DOC-001"))
        
        # Unregister document
        reg.unregister("DOC-002")
        self.assertEqual(reg.count(), 2)
        self.assertFalse(reg.contains("DOC-002"))
        
        # Unregister non-existent document (should not raise)
        reg.unregister("NON-EXISTENT")
        self.assertEqual(reg.count(), 2)
    
    def test_invoice_document_mark_paid(self):
        """Test invoice document mark_paid method"""
        invoice = InvoiceDocument(
            id="10",
            number="INV-001",
            title="Invoice",
            author=self.user,
            amount_due=1000,
            paid=False
        )
        
        self.assertFalse(invoice.paid)
        invoice.mark_paid()
        self.assertTrue(invoice.paid)
    
    def test_document_validation_errors(self):
        """Test document validation with empty title/number"""
        # Document with empty title
        doc_no_title = IncomingDocument(id="11", number="N-11", title="", author=self.user)
        with self.assertRaises(ValueError):
            doc_no_title.validate()
        
        # Document with empty number
        doc_no_number = IncomingDocument(id="12", number="", title="Title", author=self.user)
        with self.assertRaises(ValueError):
            doc_no_number.validate()
    
    def test_document_approve_wrong_status(self):
        """Test approving document in wrong status"""
        doc = IncomingDocument(id="13", number="N-13", title="Test", author=self.user)
        doc.status = WorkflowState.APPROVED  # Already approved
        
        with self.assertRaises(InvalidDocumentStatusError):
            doc.approve()
    
    def test_document_restore_not_archived(self):
        """Test restoring document that is not archived"""
        doc = IncomingDocument(id="14", number="N-14", title="Test", author=self.user)
        doc.status = WorkflowState.NEW  # Not archived
        
        with self.assertRaises(InvalidDocumentStatusError):
            doc.restore()
    
    def test_contract_document_invalid_dates(self):
        """Test contract document with invalid date range"""
        now = datetime.utcnow()
        
        # End date before start date should raise error
        contract = ContractDocument(
            id="15",
            number="CON-001",
            title="Contract",
            author=self.user,
            effective_from=now,
            effective_to=now - timedelta(days=1)  # End before start
        )
        
        with self.assertRaises(ValueError):
            contract.validate()

if __name__ == "__main__":
    unittest.main()
