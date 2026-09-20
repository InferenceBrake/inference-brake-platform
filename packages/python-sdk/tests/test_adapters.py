import unittest
from unittest.mock import patch

from inferencebrake import (
    InferenceBrakeCallbackHandler,
    LoopDetectedError,
    create_crewai_callback,
)

from tests.test_client import FakeResponse, KILL_PAYLOAD, SAFE_PAYLOAD


class FakeGeneration:
    def __init__(self, text=None):
        self.text = text


class FakeLLMResult:
    def __init__(self, text):
        self.generations = [[FakeGeneration(text=text)]]


class AdapterTests(unittest.TestCase):
    def test_langchain_handler_raises_on_loop(self):
        handler = InferenceBrakeCallbackHandler(api_key="ib_test", session_id="s1")
        with patch("requests.Session.post", return_value=FakeResponse(200, KILL_PAYLOAD)):
            with self.assertRaises(LoopDetectedError):
                handler.on_llm_end(FakeLLMResult("identical"))
        self.assertIsNotNone(handler.last_status)
        self.assertTrue(handler.last_status.should_stop)

    def test_langchain_handler_records_safe_step(self):
        handler = InferenceBrakeCallbackHandler(api_key="ib_test", session_id="s1")
        with patch("requests.Session.post", return_value=FakeResponse(200, SAFE_PAYLOAD)):
            handler.on_llm_end(FakeLLMResult("ok"))
        self.assertEqual(handler.step_count, 1)
        self.assertFalse(handler.last_status.should_stop)

    def test_langchain_handler_ignores_empty_text(self):
        handler = InferenceBrakeCallbackHandler(api_key="ib_test", session_id="s1")
        handler.on_llm_end(FakeLLMResult(None))
        self.assertEqual(handler.step_count, 0)

    def test_langchain_handler_sets_raise_error(self):
        # LangChain swallows callback exceptions unless raise_error is set.
        handler = InferenceBrakeCallbackHandler(api_key="ib_test", session_id="s1")
        self.assertTrue(handler.raise_error)

    def test_crewai_callback_raises_on_loop(self):
        callback = create_crewai_callback(api_key="ib_test", session_id="s1")
        with patch("requests.Session.post", return_value=FakeResponse(200, KILL_PAYLOAD)):
            with self.assertRaises(LoopDetectedError):
                callback.step("same reasoning", action="get_balance")

    def test_crewai_loop_key_normalizes_action(self):
        captured = {}

        def fake_post(url, json=None, timeout=None):
            captured.update(json or {})
            return FakeResponse(200, SAFE_PAYLOAD)

        callback = create_crewai_callback(
            api_key="ib_test",
            session_id="s1",
            loop_key=lambda a: a.strip().lower(),
        )
        with patch("requests.Session.post", side_effect=fake_post):
            callback.step("x", action="  Get_Balance ")

        self.assertEqual(captured["action"], "get_balance")

    def test_crewai_auto_stop_disabled_returns_status(self):
        callback = create_crewai_callback(
            api_key="ib_test", session_id="s1", auto_stop=False
        )
        with patch("requests.Session.post", return_value=FakeResponse(200, KILL_PAYLOAD)):
            status = callback.step("same")
        self.assertTrue(status.should_stop)


if __name__ == "__main__":
    unittest.main()