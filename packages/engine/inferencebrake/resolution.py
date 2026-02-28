"""
Loop Resolution Engine.

When a loop is detected, generate actionable hints to break it.

Strategies informed by:
    - TAAR (Chen et al., 2026): Structured reboot suffix that
      redirects reasoning rather than just truncating.
    - SMR (Lee et al., 2025): Discrete Stop action as a valid
      reasoning move, not just an error condition.

Resolution types:
    1. Correction hint: Injected into the agent's context
    2. Structured reboot: Replace recent context with redirect
    3. Escalation: Notify human for intervention
    4. Graceful stop: Help agent conclude with what it has
"""

from __future__ import annotations

from inferencebrake.types import LoopType, SessionState


class LoopResolver:
    """
    Generates context-appropriate hints to break detected loops.
    """

    # Default hint templates by loop type
    HINTS = {
        LoopType.EXACT_REPETITION: (
            "You are repeating yourself verbatim. "
            "State your conclusion now or ask the user for clarification. "
            "Do not continue this line of reasoning."
        ),
        LoopType.NGRAM_REPETITION: (
            "Your recent reasoning is highly repetitive. "
            "Try a fundamentally different approach to the problem. "
            "What assumptions have you been making that might be wrong?"
        ),
        LoopType.SEMANTIC_SIMILARITY: (
            "Your reasoning is revisiting the same ideas with different words. "
            "Either commit to a specific answer or explicitly identify "
            "what new information you need to make progress."
        ),
        LoopType.CUSUM_STAGNATION: (
            "Your reasoning has stagnated - you're not making meaningful progress. "
            "Step back and consider: (1) Is this problem solvable with "
            "available information? (2) What specific gap is blocking you? "
            "(3) Should you ask the user for help?"
        ),
        LoopType.ENTROPY_COLLAPSE: (
            "Your output has become formulaic and low-information. "
            "You may be stuck in a pattern. Break out by: "
            "(1) Stating what you know for certain, "
            "(2) Stating what you don't know, "
            "(3) Making a decision and moving forward."
        ),
        LoopType.ACTION_REPETITION: (
            "You have called the same tool/action repeatedly without new results. "
            "Stop calling this tool. Either use a different tool, "
            "try different parameters, or conclude with available information."
        ),
        LoopType.STRUCTURAL_LOOP: (
            "Your actions are cycling through the same pattern. "
            "This cycle will not resolve. "
            "Choose one path and commit to it, or report the limitation to the user."
        ),
        LoopType.PARAPHRASE_LOOP: (
            "You are expressing the same idea in different ways without progress. "
            "This is not productive. Commit to your best answer now."
        ),
        LoopType.PROMPT_ECHO: (
            "You appear to be echoing the original prompt. "
            "Focus on producing new analysis or a direct answer."
        ),
    }

    # Structured reboot suffixes (TAAR-inspired)
    REBOOT_SUFFIXES = {
        LoopType.SEMANTIC_SIMILARITY: (
            "\n\n[SYSTEM: Previous reasoning was unproductive. "
            "RESET. Start fresh with a different strategy. "
            "Constraint: You may NOT repeat any approach from the previous attempts.]\n"
        ),
        LoopType.ACTION_REPETITION: (
            "\n\n[SYSTEM: Tool calls are looping. "
            "CONSTRAINT: Do NOT call {last_action} again. "
            "Available alternatives: summarize findings, ask user, try different tool.]\n"
        ),
        LoopType.CUSUM_STAGNATION: (
            "\n\n[SYSTEM: Reasoning has stalled for {stagnation_steps} steps. "
            "DIRECTIVE: Produce a final answer in the next response, "
            "even if uncertain. Prefix uncertain conclusions with 'I believe' "
            "and explain your reasoning.]\n"
        ),
    }

    def generate_hint(
        self,
        loop_type: LoopType,
        session: SessionState,
        style: str = "assertive",
        custom_hint: str | None = None,
    ) -> str:
        """
        Generate a correction hint for the detected loop type.

        Args:
            loop_type: The type of loop detected.
            session: Current session state for context.
            style: 'gentle', 'assertive', or 'directive'.
            custom_hint: Override with user's custom hint text.

        Returns:
            Hint text suitable for injection into agent context.
        """
        if custom_hint:
            return custom_hint

        base_hint = self.HINTS.get(loop_type, self.HINTS[LoopType.SEMANTIC_SIMILARITY])

        if style == "gentle":
            return f"Note: {base_hint}"
        elif style == "directive":
            return f"IMPORTANT: {base_hint}"
        else:
            return base_hint

    def generate_reboot_suffix(
        self,
        loop_type: LoopType,
        session: SessionState,
    ) -> str:
        """
        Generate a structured reboot suffix (TAAR-inspired).

        This is a stronger intervention than a hint - it replaces
        recent context with a redirect directive.
        """
        template = self.REBOOT_SUFFIXES.get(loop_type, "")
        if not template:
            return self.generate_hint(loop_type, session, style="directive")

        # Fill in context-specific placeholders
        last_action = ""
        if session.action_sequence:
            last_action = session.action_sequence[-1]

        stagnation_steps = max(1, len(session.entropy_history))

        return template.format(
            last_action=last_action,
            stagnation_steps=stagnation_steps,
        )

    def recommend_action(
        self,
        loop_type: LoopType,
        confidence: float,
        session: SessionState,
    ) -> dict:
        """
        Recommend an intervention action based on loop severity.

        Returns a dict with:
            - action: 'hint', 'reboot', 'stop', 'escalate'
            - message: Human-readable explanation
            - hint: The hint/reboot text if applicable
        """
        if confidence >= 0.9:
            if session.step_count > 20:
                return {
                    "action": "stop",
                    "message": "High-confidence loop after many steps. Recommend stopping.",
                    "hint": self.generate_hint(loop_type, session, "directive"),
                }
            else:
                return {
                    "action": "reboot",
                    "message": "High-confidence loop. Injecting reboot directive.",
                    "hint": self.generate_reboot_suffix(loop_type, session),
                }
        elif confidence >= 0.7:
            return {
                "action": "hint",
                "message": "Likely loop. Injecting correction hint.",
                "hint": self.generate_hint(loop_type, session, "assertive"),
            }
        else:
            return {
                "action": "hint",
                "message": "Possible loop. Gentle nudge.",
                "hint": self.generate_hint(loop_type, session, "gentle"),
            }
