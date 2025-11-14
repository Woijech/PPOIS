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
    
    def test_repo_get_not_found(self):
        """Test repository get when document not found"""
        loc = StorageLocation(name="local", base_path="/tmp")
        quota = QuotaManager(max_bytes=1_000_000)
        storage = DocumentStorage(loc, quota)
        repo = InMemoryDocumentRepository(storage=storage)
        
        # Should return None for non-existent document
        result = repo.get("NON-EXISTENT")
        self.assertIsNone(result)
    
    def test_document_service_archive(self):
        """Test document service archive method"""
        u = User(id="u1", login="l", display_name="d")
        doc = IncomingDocument(id="3", number="N-3", title="Archive Test", author=u)
        self.doc_service.register(doc)
        
        # Archive the document
        self.doc_service.archive("N-3")
        
        # Verify archived
        from documentflow.workflow import WorkflowState
        archived_doc = self.repo.get("N-3")
        self.assertEqual(archived_doc.status, WorkflowState.ARCHIVED)
    
    def test_document_service_sign_blocked_user(self):
        """Test signing document with blocked user"""
        from documentflow.exceptions import AccessDeniedError
        
        u = User(id="u2", login="blocked", display_name="Blocked User", is_blocked=True)
        doc = IncomingDocument(id="4", number="N-4", title="Sign Test", author=u)
        doc.add_version("v1", u.id)
        self.doc_service.register(doc)
        
        # Attempt to sign with blocked user should raise error
        with self.assertRaises(AccessDeniedError):
            self.doc_service.sign("N-4", u)

if __name__ == "__main__":
    unittest.main()
