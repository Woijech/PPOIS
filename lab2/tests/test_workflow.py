import unittest
from datetime import datetime
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

if __name__ == "__main__":
    unittest.main()
