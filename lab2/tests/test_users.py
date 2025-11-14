import unittest
from documentflow.users import Permission, Role, Department, AccessPolicy, Organization, User


class TestUsers(unittest.TestCase):
    def test_permission_priority(self):
        """Test permission priority comparison"""
        perm1 = Permission(code="READ", description="Read access", priority=1)
        perm2 = Permission(code="WRITE", description="Write access", priority=2)
        perm3 = Permission(code="DELETE", description="Delete access", priority=1)
        
        self.assertTrue(perm2.is_higher_priority_than(perm1))
        self.assertFalse(perm1.is_higher_priority_than(perm2))
        self.assertFalse(perm1.is_higher_priority_than(perm3))
    
    def test_role_permissions(self):
        """Test role permission management"""
        perm_read = Permission(code="READ", description="Read access")
        perm_write = Permission(code="WRITE", description="Write access")
        
        role = Role(name="Editor")
        self.assertTrue(role.is_active)
        
        # Test adding permissions
        role.add_permission(perm_read)
        role.add_permission(perm_write)
        
        self.assertTrue(role.allows("READ"))
        self.assertTrue(role.allows("WRITE"))
        self.assertFalse(role.allows("DELETE"))
        
        # Test removing permissions
        role.remove_permission(perm_write)
        self.assertFalse(role.allows("WRITE"))
        self.assertTrue(role.allows("READ"))
    
    def test_role_activation(self):
        """Test role activation/deactivation"""
        perm = Permission(code="ACCESS", description="Access permission")
        role = Role(name="TestRole", permissions={perm})
        
        self.assertTrue(role.allows("ACCESS"))
        
        # Deactivate role
        role.deactivate()
        self.assertFalse(role.is_active)
        self.assertFalse(role.allows("ACCESS"))
        
        # Reactivate role
        role.activate()
        self.assertTrue(role.is_active)
        self.assertTrue(role.allows("ACCESS"))
    
    def test_department_budget(self):
        """Test department budget management"""
        dept = Department(name="IT", cost_center="CC-001", budget=10000)
        
        # Test initial budget
        self.assertEqual(dept.get_remaining_budget(), 10000)
        
        # Test allocating budget
        dept.allocate_budget(5000)
        self.assertEqual(dept.get_remaining_budget(), 15000)
        
        # Test spending budget
        success = dept.spend_budget(8000)
        self.assertTrue(success)
        self.assertEqual(dept.get_remaining_budget(), 7000)
        
        # Test insufficient budget
        success = dept.spend_budget(10000)
        self.assertFalse(success)
        self.assertEqual(dept.get_remaining_budget(), 7000)
    
    def test_access_policy(self):
        """Test access policy"""
        policy = AccessPolicy()
        
        # Add allowed roles
        policy.allow_role("ADMIN")
        policy.allow_role("EDITOR")
        
        # Add denied roles
        policy.deny_role("GUEST")
        
        # Create roles
        admin_role = Role(name="ADMIN")
        editor_role = Role(name="EDITOR")
        guest_role = Role(name="GUEST")
        user_role = Role(name="USER")
        
        # Test access with allowed roles
        self.assertTrue(policy.can_access([admin_role]))
        self.assertTrue(policy.can_access([editor_role]))
        
        # Test access with denied roles (denied takes precedence)
        self.assertFalse(policy.can_access([guest_role]))
        self.assertFalse(policy.can_access([admin_role, guest_role]))
        
        # Test access with role not in policy
        self.assertFalse(policy.can_access([user_role]))
    
    def test_organization(self):
        """Test organization"""
        org = Organization(name="Test Corp", inn="1234567890", address="123 Main St")
        
        # Test contact info update
        org.update_contact_info(phone="+1234567890", email="info@test.com")
        self.assertEqual(org.phone, "+1234567890")
        self.assertEqual(org.email, "info@test.com")
        
        # Test partial update
        org.update_contact_info(phone="+0987654321")
        self.assertEqual(org.phone, "+0987654321")
        self.assertEqual(org.email, "info@test.com")
        
        # Test INN validation
        self.assertTrue(org.validate_inn())
        
        org2 = Organization(name="Test2", inn="123456789012")  # 12 digits
        self.assertTrue(org2.validate_inn())
        
        org3 = Organization(name="Test3", inn="123")  # invalid length
        self.assertFalse(org3.validate_inn())
        
        org4 = Organization(name="Test4", inn="12345abc90")  # non-digits
        self.assertFalse(org4.validate_inn())
    
    def test_user_permissions(self):
        """Test user permission checking"""
        perm = Permission(code="EDIT", description="Edit permission")
        role = Role(name="Editor", permissions={perm})
        
        user = User(id="u1", login="testuser", display_name="Test User")
        user.assign_role(role)
        
        # Test permission check
        self.assertTrue(user.has_permission("EDIT"))
        self.assertFalse(user.has_permission("DELETE"))
        
        # Test blocked user
        user.block()
        self.assertTrue(user.is_blocked)
        self.assertFalse(user.has_permission("EDIT"))
        
        # Test unblocked user
        user.unblock()
        self.assertFalse(user.is_blocked)
        self.assertTrue(user.has_permission("EDIT"))
    
    def test_user_role_management(self):
        """Test user role assignment and removal"""
        role1 = Role(name="Role1")
        role2 = Role(name="Role2")
        
        user = User(id="u2", login="user2", display_name="User Two")
        
        # Test assigning roles
        user.assign_role(role1)
        self.assertEqual(len(user.roles), 1)
        
        # Test assigning duplicate role (should not add)
        user.assign_role(role1)
        self.assertEqual(len(user.roles), 1)
        
        user.assign_role(role2)
        self.assertEqual(len(user.roles), 2)
        
        # Test removing roles
        user.remove_role(role1)
        self.assertEqual(len(user.roles), 1)
        self.assertEqual(user.roles[0].name, "Role2")
        
        # Test removing non-existent role (should not raise error)
        user.remove_role(role1)
        self.assertEqual(len(user.roles), 1)
    
    def test_user_department(self):
        """Test user department change"""
        dept1 = Department(name="IT", cost_center="CC-001")
        dept2 = Department(name="HR", cost_center="CC-002")
        
        user = User(id="u3", login="user3", display_name="User Three")
        self.assertIsNone(user.department)
        
        user.change_department(dept1)
        self.assertEqual(user.department.name, "IT")
        
        user.change_department(dept2)
        self.assertEqual(user.department.name, "HR")
    
    def test_user_active_roles(self):
        """Test getting active roles"""
        role1 = Role(name="Role1", is_active=True)
        role2 = Role(name="Role2", is_active=False)
        role3 = Role(name="Role3", is_active=True)
        
        user = User(id="u4", login="user4", display_name="User Four")
        user.assign_role(role1)
        user.assign_role(role2)
        user.assign_role(role3)
        
        active_roles = user.get_active_roles()
        self.assertEqual(len(active_roles), 2)
        self.assertTrue(all(r.is_active for r in active_roles))
        self.assertIn(role1, active_roles)
        self.assertIn(role3, active_roles)
        self.assertNotIn(role2, active_roles)


if __name__ == "__main__":
    unittest.main()
