import unittest
from documentflow.services import InMemoryDocumentRepository, ConsoleNotifier, NotificationService, ValidationService, DocumentService, ApprovalService, SearchService, AuthService
from documentflow.storage import StorageLocation, DocumentStorage
from documentflow.security import QuotaManager, PasswordPolicy
from documentflow.documents import IncomingDocument, DocumentRegistry
from documentflow.users import User

class TestServices(unittest.TestCase):
    def setUp(self):
        loc = StorageLocation(name="local", base_path="/tmp")
        quota = QuotaManager(max_bytes=1_000_000)
        storage = DocumentStorage(loc, quota)
        self.repo = InMemoryDocumentRepository(storage=storage)
        self.notify = NotificationService(ConsoleNotifier())
        self.validator = ValidationService()
        self.registry = DocumentRegistry()
        self.doc_service = DocumentService(repo=self.repo, registry=self.registry, validator=self.validator, notifier=self.notify)
    def test_register_and_search(self):
        u = User(id="u1", login="l", display_name="d")
        doc = IncomingDocument(id="1", number="N-1", title="Test", author=u)
        self.doc_service.register(doc)
        search = SearchService(repo=self.repo)
        res = search.find("Test")
        self.assertEqual(res[0].number, "N-1")
    def test_approve_and_sign(self):
        u = User(id="u1", login="l", display_name="d")
        doc = IncomingDocument(id="2", number="N-2", title="Test2", author=u)
        self.doc_service.register(doc)
        appr = ApprovalService(self.notify)
        route = appr.route_for_role("REVIEWER")
        self.doc_service.send_for_approval("N-2", route)
        appr.approve(doc)
        doc.add_version("v1", u.id)
        self.doc_service.sign("N-2", u)
    def test_auth(self):
        auth = AuthService(users={"alice": "pass1234"}, policy=PasswordPolicy())
        token = auth.login("alice", "pass1234")
        self.assertTrue(token.value)

if __name__ == "__main__":
    unittest.main()
