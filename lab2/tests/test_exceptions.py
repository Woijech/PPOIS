import unittest
from documentflow.exceptions import (
    DocumentNotFoundError, InvalidDocumentStatusError, AccessDeniedError,
    ApprovalStepError, InvalidSignatureError, UserBlockedError, VersionConflictError,
    RouteNotFoundError, PaymentOperationError, AuthFailedError, DuplicateDocumentError, StorageLimitExceededError
)

class TestExceptions(unittest.TestCase):
    def test_instantiation(self):
        for exc in [DocumentNotFoundError, InvalidDocumentStatusError, AccessDeniedError, ApprovalStepError, InvalidSignatureError, UserBlockedError, VersionConflictError, RouteNotFoundError, PaymentOperationError, AuthFailedError, DuplicateDocumentError, StorageLimitExceededError]:
            self.assertTrue(issubclass(exc, Exception))
            _ = exc("msg")

if __name__ == "__main__":
    unittest.main()
