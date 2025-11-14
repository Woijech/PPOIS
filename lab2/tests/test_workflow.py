import unittest
from datetime import datetime, timedelta
from documentflow.workflow import ApprovalStep, ApprovalRoute, ApprovalTask, WorkflowState, Notification, WorkflowTransition
from documentflow.exceptions import ApprovalStepError

class TestWorkflow(unittest.TestCase):
    def test_route(self):
        step = ApprovalStep(name="S1", role_name="R1", deadline_hours=1)
        route = ApprovalRoute(name="R", steps=[step])
        self.assertEqual(route.first_step().name, "S1")
        self.assertIsNone(route.next_step(step))

    def test_task(self):
        step = ApprovalStep(name="S2", role_name="R2")
        t = ApprovalTask(step=step, assignee_id="u", created_at=datetime.utcnow())
        t.complete("ok")
        with self.assertRaises(ApprovalStepError):
            t.complete("again")

    def test_transition(self):
        tr = WorkflowTransition(src=WorkflowState.NEW, dst=WorkflowState.APPROVED, reason="auto")
        self.assertEqual(tr.dst, WorkflowState.APPROVED)
    
    def test_approval_step_deadline_methods(self):
        """Test approval step deadline methods"""
        step = ApprovalStep(name="Review", role_name="Reviewer", deadline_hours=24)
        start_time = datetime.utcnow()
        
        # Test deadline calculation
        deadline = step.deadline(start_time)
        expected_deadline = start_time + timedelta(hours=24)
        self.assertEqual(deadline, expected_deadline)
        
        # Test is_overdue
        self.assertFalse(step.is_overdue(start_time))
        
        # Test with old start time (overdue)
        old_start = datetime.utcnow() - timedelta(hours=48)
        self.assertTrue(step.is_overdue(old_start))
        
        # Test extend_deadline
        step.extend_deadline(12)
        self.assertEqual(step.deadline_hours, 36)
    
    def test_approval_task_reassign(self):
        """Test approval task reassignment"""
        step = ApprovalStep(name="Approve", role_name="Approver")
        task = ApprovalTask(step=step, assignee_id="user1", created_at=datetime.utcnow())
        
        # Test reassign before completion
        task.reassign("user2")
        self.assertEqual(task.assignee_id, "user2")
        
        # Complete the task
        task.complete("Approved")
        
        # Test reassign after completion (should fail)
        with self.assertRaises(ApprovalStepError):
            task.reassign("user3")
    
    def test_approval_task_is_overdue(self):
        """Test approval task overdue check"""
        step = ApprovalStep(name="Quick", role_name="Reviewer", deadline_hours=1)
        
        # Task created 2 hours ago (overdue)
        old_task = ApprovalTask(
            step=step,
            assignee_id="user1",
            created_at=datetime.utcnow() - timedelta(hours=2)
        )
        self.assertTrue(old_task.is_overdue())
        
        # Task created just now (not overdue)
        new_task = ApprovalTask(
            step=step,
            assignee_id="user2",
            created_at=datetime.utcnow()
        )
        self.assertFalse(new_task.is_overdue())
    
    def test_approval_route_add_remove_steps(self):
        """Test approval route add and remove steps"""
        route = ApprovalRoute(name="TestRoute")
        
        step1 = ApprovalStep(name="Step1", role_name="Role1")
        step2 = ApprovalStep(name="Step2", role_name="Role2")
        step3 = ApprovalStep(name="Step3", role_name="Role3")
        
        # Test add_step
        route.add_step(step1)
        route.add_step(step2)
        route.add_step(step3)
        
        self.assertEqual(route.get_step_count(), 3)
        
        # Test remove_step
        route.remove_step(step2)
        self.assertEqual(route.get_step_count(), 2)
        
        # Test remove non-existent step (should not raise)
        route.remove_step(step2)
        self.assertEqual(route.get_step_count(), 2)
    
    def test_approval_route_empty_error(self):
        """Test approval route with no steps"""
        empty_route = ApprovalRoute(name="Empty")
        
        with self.assertRaises(ApprovalStepError):
            empty_route.first_step()
    
    def test_approval_route_next_step_error(self):
        """Test approval route next_step with invalid step"""
        step1 = ApprovalStep(name="Step1", role_name="Role1")
        step2 = ApprovalStep(name="Step2", role_name="Role2")
        invalid_step = ApprovalStep(name="Invalid", role_name="Role3")
        
        route = ApprovalRoute(name="TestRoute", steps=[step1, step2])
        
        with self.assertRaises(ApprovalStepError):
            route.next_step(invalid_step)
    
    def test_workflow_transition_validation(self):
        """Test workflow transition validation"""
        # Valid transitions
        valid_transitions = [
            (WorkflowState.NEW, WorkflowState.IN_REVIEW),
            (WorkflowState.NEW, WorkflowState.ARCHIVED),
            (WorkflowState.IN_REVIEW, WorkflowState.APPROVED),
            (WorkflowState.IN_REVIEW, WorkflowState.REJECTED),
            (WorkflowState.IN_REVIEW, WorkflowState.NEW),
            (WorkflowState.APPROVED, WorkflowState.ARCHIVED),
            (WorkflowState.REJECTED, WorkflowState.NEW),
            (WorkflowState.REJECTED, WorkflowState.ARCHIVED),
            (WorkflowState.ARCHIVED, WorkflowState.NEW),
        ]
        
        for src, dst in valid_transitions:
            tr = WorkflowTransition(src=src, dst=dst)
            self.assertTrue(tr.is_valid_transition(), f"Transition {src} -> {dst} should be valid")
        
        # Invalid transitions
        invalid_transitions = [
            (WorkflowState.NEW, WorkflowState.APPROVED),  # Can't skip IN_REVIEW
            (WorkflowState.APPROVED, WorkflowState.NEW),  # Can't go back from approved to new
            (WorkflowState.APPROVED, WorkflowState.REJECTED),  # Can't reject approved
        ]
        
        for src, dst in invalid_transitions:
            tr = WorkflowTransition(src=src, dst=dst)
            self.assertFalse(tr.is_valid_transition(), f"Transition {src} -> {dst} should be invalid")
    
    def test_notification_methods(self):
        """Test notification methods"""
        # Test high priority notification
        high_priority = Notification(
            message="Urgent: Document requires approval",
            recipient_id="user1",
            created_at=datetime.utcnow(),
            priority=10
        )
        self.assertTrue(high_priority.is_high_priority())
        self.assertFalse(high_priority.is_read)
        
        # Test mark_read
        high_priority.mark_read()
        self.assertTrue(high_priority.is_read)
        
        # Test low priority notification
        low_priority = Notification(
            message="Info: Document updated",
            recipient_id="user2",
            created_at=datetime.utcnow(),
            priority=3
        )
        self.assertFalse(low_priority.is_high_priority())

if __name__ == "__main__":
    unittest.main()
