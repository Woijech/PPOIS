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
    
    def test_password_policy_strength(self):
        """Test password strength scoring"""
        policy = PasswordPolicy(min_length=8)
        
        # Weak password (only length)
        weak = "abcdefgh"
        score_weak = policy.get_strength_score(weak)
        self.assertEqual(score_weak, 25)
        
        # Medium password (length + digit)
        medium = "abcdefg1"
        score_medium = policy.get_strength_score(medium)
        self.assertEqual(score_medium, 50)
        
        # Strong password (length + digit + uppercase)
        strong = "Abcdefg1"
        score_strong = policy.get_strength_score(strong)
        self.assertEqual(score_strong, 75)
        
        # Very strong password (length + digit + uppercase + special)
        very_strong = "Abcdefg1!"
        score_very_strong = policy.get_strength_score(very_strong)
        self.assertEqual(score_very_strong, 100)
        
        # Short password (no points)
        short = "Ab1!"
        score_short = policy.get_strength_score(short)
        self.assertEqual(score_short, 75)  # Has digit, uppercase, special but not length
    
    def test_password_policy_validation_rules(self):
        """Test password policy with different requirements"""
        # Policy requiring uppercase
        policy_upper = PasswordPolicy(min_length=6, require_digit=False, require_uppercase=True)
        self.assertTrue(policy_upper.validate("AbCdEf"))
        self.assertFalse(policy_upper.validate("abcdef"))
        
        # Policy requiring special characters
        policy_special = PasswordPolicy(min_length=6, require_digit=False, require_special=True)
        self.assertTrue(policy_special.validate("abc@ef"))
        self.assertFalse(policy_special.validate("abcdef"))
        
        # Policy with all requirements
        policy_strict = PasswordPolicy(
            min_length=10,
            require_digit=True,
            require_uppercase=True,
            require_special=True
        )
        self.assertTrue(policy_strict.validate("Abc123!@#$"))
        self.assertFalse(policy_strict.validate("short1A!"))
        self.assertFalse(policy_strict.validate("NoDigitHere!A"))
        self.assertFalse(policy_strict.validate("nouppercas1!"))
        self.assertFalse(policy_strict.validate("NoSpecial1A"))
    
    def test_session_terminate(self):
        """Test session termination"""
        now = datetime.utcnow()
        session = Session(
            user_id="user1",
            token="token123",
            created_at=now,
            expires_at=now + timedelta(hours=2)
        )
        
        self.assertTrue(session.is_active(now))
        
        # Terminate session
        session.terminate()
        self.assertTrue(session.is_terminated)
        self.assertFalse(session.is_active(now))
    
    def test_session_extend(self):
        """Test session expiration extension"""
        now = datetime.utcnow()
        original_expiry = now + timedelta(hours=1)
        session = Session(
            user_id="user2",
            token="token456",
            created_at=now,
            expires_at=original_expiry
        )
        
        # Extend by 2 hours
        session.extend(2)
        expected_expiry = original_expiry + timedelta(hours=2)
        self.assertEqual(session.expires_at, expected_expiry)
        
        # Session should be active at extended time
        extended_moment = now + timedelta(hours=2)
        self.assertTrue(session.is_active(extended_moment))
    
    def test_session_expired(self):
        """Test expired session"""
        now = datetime.utcnow()
        session = Session(
            user_id="user3",
            token="token789",
            created_at=now - timedelta(hours=3),
            expires_at=now - timedelta(hours=1)
        )
        
        # Session should not be active after expiration
        self.assertFalse(session.is_active(now))
    
    def test_token_revoke(self):
        """Test token revocation"""
        token = Token.generate()
        
        # Token should not be expired initially
        now = datetime.utcnow()
        self.assertFalse(token.is_expired(now))
        
        # Revoke token
        revoke_time = datetime.utcnow()
        token.revoke()
        
        # Token should be expired after revocation (check a moment after revocation)
        after_revoke = revoke_time + timedelta(seconds=1)
        self.assertTrue(token.is_expired(after_revoke))
    
    def test_token_expiration(self):
        """Test token expiration check"""
        now = datetime.utcnow()
        
        # Token with future expiration
        future_token = Token(
            value="abc123",
            issued_at=now,
            expires_at=now + timedelta(hours=1)
        )
        self.assertFalse(future_token.is_expired(now))
        self.assertTrue(future_token.is_expired(now + timedelta(hours=2)))
        
        # Token with no expiration
        no_expiry_token = Token(
            value="xyz789",
            issued_at=now,
            expires_at=None
        )
        self.assertFalse(no_expiry_token.is_expired(now))
        self.assertFalse(no_expiry_token.is_expired(now + timedelta(days=365)))
    
    def test_quota_manager_methods(self):
        """Test quota manager additional methods"""
        quota = QuotaManager(max_bytes=1000, warning_threshold=800)
        
        # Test initial state
        self.assertEqual(quota.get_usage_percentage(), 0)
        self.assertFalse(quota.is_near_limit())
        
        # Allocate some space
        quota.allocate(500)
        self.assertEqual(quota.used_bytes, 500)
        self.assertEqual(quota.get_usage_percentage(), 50)
        self.assertFalse(quota.is_near_limit())
        
        # Allocate more to approach warning threshold
        quota.allocate(350)
        self.assertEqual(quota.used_bytes, 850)
        self.assertEqual(quota.get_usage_percentage(), 85)
        self.assertTrue(quota.is_near_limit())
        
        # Test deallocate
        quota.deallocate(200)
        self.assertEqual(quota.used_bytes, 650)
        self.assertEqual(quota.get_usage_percentage(), 65)
        self.assertFalse(quota.is_near_limit())
        
        # Test deallocate more than used (should set to 0)
        quota.deallocate(1000)
        self.assertEqual(quota.used_bytes, 0)
        self.assertEqual(quota.get_usage_percentage(), 0)

if __name__ == "__main__":
    unittest.main()
