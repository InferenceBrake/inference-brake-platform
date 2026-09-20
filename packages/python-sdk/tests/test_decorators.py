import unittest
from unittest.mock import patch

from inferencebrake import LoopDetectedError, guard_agent_loop

from tests.test_client import FakeResponse, KILL_PAYLOAD, SAFE_PAYLOAD


class DecoratorTests(unittest.TestCase):
    def test_raises_on_loop(self):
        @guard_agent_loop(api_key="ib_test", session_id="s1")
        def step(prompt):
            return "identical reasoning"

        with patch("requests.Session.post", return_value=FakeResponse(200, KILL_PAYLOAD)):
            with self.assertRaises(LoopDetectedError):
                step("hi")

    def test_passthrough_when_safe(self):
        @guard_agent_loop(api_key="ib_test", session_id="s1")
        def step(prompt):
            return "ok"

        with patch("requests.Session.post", return_value=FakeResponse(200, SAFE_PAYLOAD)):
            self.assertEqual(step("hi"), "ok")

    def test_extract_and_action(self):
        captured = {}

        def fake_post(url, json=None, timeout=None):
            captured.update(json or {})
            return FakeResponse(200, SAFE_PAYLOAD)

        @guard_agent_loop(
            api_key="ib_test",
            session_id="s1",
            extract=lambda r: r["text"],
            action=lambda r: r["tool"],
            loop_key=lambda a: a.strip().lower(),
        )
        def step(prompt):
            return {"text": "reasoning", "tool": "  Get_Balance "}

        with patch("requests.Session.post", side_effect=fake_post):
            step("hi")

        self.assertEqual(captured["reasoning"], "reasoning")
        self.assertEqual(captured["action"], "get_balance")

    def test_fail_open_lets_call_through(self):
        import requests

        @guard_agent_loop(api_key="ib_test", session_id="s1")
        def step(prompt):
            return "result"

        with patch(
            "requests.Session.post",
            side_effect=requests.exceptions.ConnectionError("down"),
        ):
            self.assertEqual(step("hi"), "result")

    def test_requires_api_key(self):
        import os

        with patch.dict(os.environ, {}, clear=True):
            with self.assertRaises(ValueError):
                guard_agent_loop(session_id="s1")


if __name__ == "__main__":
    unittest.main()