import unittest

from inferencebrake import CheckStatus, LoopDetectedError, LoopPolicy, steering_message

from tests.test_client import KILL_PAYLOAD, SAFE_PAYLOAD


def make_status(payload):
    return CheckStatus(
        action=payload["action"],
        loop_detected=payload["loop_detected"],
        similarity=payload["similarity"],
        status=payload["status"],
        message=payload["message"],
        confidence=payload.get("confidence", 0.0),
        detectors=payload.get("detectors", {}),
    )


class PolicyTests(unittest.TestCase):
    def test_escalate_under_budget(self):
        calls = []
        policy = LoopPolicy(
            auto_stop=True,
            max_escalations=2,
            escalate=lambda status, attempt: calls.append(attempt),
        )
        action = policy.handle(make_status(KILL_PAYLOAD))
        self.assertEqual(action, "escalate")
        self.assertEqual(calls, [1])
        self.assertEqual(policy.escalations_used, 1)

    def test_escalate_exhausted_then_raises(self):
        calls = []
        policy = LoopPolicy(
            auto_stop=True,
            max_escalations=1,
            escalate=lambda status, attempt: calls.append(attempt),
        )
        policy.handle(make_status(KILL_PAYLOAD))
        with self.assertRaises(LoopDetectedError):
            policy.handle(make_status(KILL_PAYLOAD))
        self.assertEqual(calls, [1])

    def test_on_loop_called_without_escalate(self):
        seen = []
        policy = LoopPolicy(auto_stop=False, on_loop=seen.append)
        action = policy.handle(make_status(KILL_PAYLOAD))
        self.assertEqual(action, "stop")
        self.assertEqual(len(seen), 1)

    def test_continue_when_safe(self):
        policy = LoopPolicy(auto_stop=True)
        self.assertEqual(policy.handle(make_status(SAFE_PAYLOAD)), "continue")

    def test_steering_message(self):
        message = steering_message(make_status(KILL_PAYLOAD))
        self.assertIn("repeating yourself", message)

    def test_reset(self):
        policy = LoopPolicy(max_escalations=1, escalate=lambda status, attempt: None)
        policy.handle(make_status(KILL_PAYLOAD))
        policy.reset()
        self.assertEqual(policy.escalations_used, 0)


if __name__ == "__main__":
    unittest.main()