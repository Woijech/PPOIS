import unittest
from datetime import datetime, timedelta
from documentflow.users import User, Role, Organization, Department
from documentflow.documents import Document, IncomingDocument, OutgoingDocument, ContractDocument, InvoiceDocument, OrderDocument, DocumentRegistry, DocumentAttachment
from documentflow.workflow import WorkflowState
from documentflow.exceptions import InvalidDocumentStatusError, DuplicateDocumentError, InvalidSignatureError

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

if __name__ == "__main__":
    unittest.main()
