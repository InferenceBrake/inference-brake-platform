import unittest
from unittest.mock import patch

import requests

from inferencebrake import (
    AuthenticationError,
    InferenceBrake,
    InferenceBrakeError,
    LoopDetectedError,
    RateLimitError,
)


class FakeResponse:
    def __init__(self, status_code=200, payload=None):
        self.status_code = status_code
        self._payload = payload or {}

    def json(self):
        return self._payload


KILL_PAYLOAD = {
    "action": "KILL",
    "loop_detected": True,
    "similarity": 0.98,
    "status": "danger",
    "message": "Loop detected (confidence=64%)",
    "confidence": 0.64,
    "action_repeat_count": 4,
    "ngram_overlap": 0.8,
    "detectors": {
        "semantic": True,
        "action": True,
        "ngram": False,
        "editdist": False,
        "compression": True,
    },
    "estimated_cost_saved": 0.0028,
}

SAFE_PAYLOAD = {
    "action": "PROCEED",
    "loop_detected": False,
    "similarity": 0.1,
    "status": "safe",
    "message": "Reasoning sound",
    "confidence": 0.0,
    "detectors": {},
    "estimated_cost_saved": 0.0,
}


class ClientTests(unittest.TestCase):
    def test_parses_response(self):
        with patch("requests.Session.post", return_value=FakeResponse(200, KILL_PAYLOAD)):
            status = InferenceBrake(api_key="ib_test").check("some reasoning", "s1")

        self.assertTrue(status.should_stop)
        self.assertAlmostEqual(status.score, 0.64)
        self.assertEqual(status.detector_triggered, "semantic, action, compression")
        self.assertAlmostEqual(status.estimated_cost_saved, 0.0028)
        self.assertFalse(status.degraded)

    def test_401_raises_authentication_error(self):
        with patch(
            "requests.Session.post",
            return_value=FakeResponse(401, {"error": "Invalid API key"}),
        ):
            with self.assertRaises(AuthenticationError):
                InferenceBrake(api_key="bad").check("x", "s1")

    def test_429_raises_rate_limit(self):
        with patch(
            "requests.Session.post",
            return_value=FakeResponse(429, {"error": "rate limited"}),
        ):
            with self.assertRaises(RateLimitError):
                InferenceBrake(api_key="ib_test").check("x", "s1")

    def test_fail_open_on_connection_error(self):
        guard = InferenceBrake(api_key="ib_test")
        with patch(
            "requests.Session.post",
            side_effect=requests.exceptions.ConnectionError("boom"),
        ):
            status = guard.check("x", "s1")

        self.assertFalse(status.should_stop)
        self.assertTrue(status.degraded)
        self.assertEqual(status.action, "PROCEED")

    def test_fail_open_on_5xx(self):
        with patch(
            "requests.Session.post",
            return_value=FakeResponse(503, {"error": "unavailable"}),
        ):
            status = InferenceBrake(api_key="ib_test").check("x", "s1")
        self.assertTrue(status.degraded)

    def test_fail_closed_raises(self):
        guard = InferenceBrake(api_key="ib_test", fail_open=False)
        with patch(
            "requests.Session.post",
            side_effect=requests.exceptions.Timeout("slow"),
        ):
            with self.assertRaises(InferenceBrakeError):
                guard.check("x", "s1")

    def test_auto_stop_raises_loop_detected(self):
        with patch("requests.Session.post", return_value=FakeResponse(200, KILL_PAYLOAD)):
            guard = InferenceBrake(api_key="ib_test", auto_stop=True)
            with self.assertRaises(LoopDetectedError):
                guard.check("x", "s1")

    def test_action_is_sent_in_payload(self):
        captured = {}

        def fake_post(url, json=None, timeout=None):
            captured.update(json or {})
            return FakeResponse(200, SAFE_PAYLOAD)

        with patch("requests.Session.post", side_effect=fake_post):
            InferenceBrake(api_key="ib_test").check("x", "s1", action="get_balance")

        self.assertEqual(captured.get("action"), "get_balance")


if __name__ == "__main__":
    unittest.main()