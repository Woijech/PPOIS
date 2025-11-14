import unittest
from datetime import datetime, timedelta
from documentflow.security import PasswordPolicy, Session, Token, QuotaManager
from documentflow.exceptions import StorageLimitExceededError

class TestSecurity(unittest.TestCase):
    def test_policy(self):
        p = PasswordPolicy()
        self.assertTrue(p.validate("goodpass1"))
        self.assertFalse(p.validate("short"))
    def test_session(self):
        now = datetime.utcnow()
        s = Session(user_id="u", token="t", created_at=now, expires_at=now + timedelta(hours=1))
        self.assertTrue(s.is_active(now))
    def test_token(self):
        t = Token.generate()
        self.assertTrue(len(t.value) > 10)
    def test_quota(self):
        q = QuotaManager(max_bytes=10)
        self.assertTrue(q.can_allocate(5))
        q.allocate(5)
        with self.assertRaises(StorageLimitExceededError):
            q.allocate(6)

if __name__ == "__main__":
    unittest.main()
