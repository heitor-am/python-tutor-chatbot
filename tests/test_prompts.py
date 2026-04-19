"""System prompt validation.

These aren't behavioural tests of the LLM — they assert the prompt's
*content* contains the rules we rely on downstream. If a refactor
removes "português brasileiro" or the off-topic refusal rule, the eval
harness later in development would catch the regression eventually,
but the prompt test catches it instantly on PR.
"""

from __future__ import annotations

import pytest

from app.prompts.tutor import GROUNDING_RULE, SYSTEM_PROMPT, build_system_prompt


class TestSystemPrompt:
    def test_persona_is_python_tutor(self) -> None:
        assert "tutor de Python" in SYSTEM_PROMPT

    def test_responds_in_brazilian_portuguese(self) -> None:
        assert "português brasileiro" in SYSTEM_PROMPT

    def test_refuses_off_topic_questions(self) -> None:
        # The refusal rule is what stops the tutor from answering
        # "como cozinhar arroz" with a Python recipe analogy.
        assert "recuse educadamente" in SYSTEM_PROMPT

    def test_requires_short_executable_examples(self) -> None:
        assert "menos de 15 linhas" in SYSTEM_PROMPT
        assert "executáveis" in SYSTEM_PROMPT

    def test_requires_explanation_before_code(self) -> None:
        assert "raciocínio antes de mostrar código" in SYSTEM_PROMPT

    def test_uses_markdown_code_blocks(self) -> None:
        assert "```python" in SYSTEM_PROMPT

    @pytest.mark.parametrize("rule_id", ["1.", "2.", "3.", "4.", "5.", "6.", "7.", "8."])
    def test_eight_numbered_rules_present(self, rule_id: str) -> None:
        assert rule_id in SYSTEM_PROMPT


class TestBuildSystemPrompt:
    def test_omits_grounding_rule_when_no_tools(self) -> None:
        prompt = build_system_prompt(with_grounding=False)
        assert prompt == SYSTEM_PROMPT
        assert "9." not in prompt
        assert "tool de busca" not in prompt

    def test_appends_grounding_rule_when_tools_present(self) -> None:
        prompt = build_system_prompt(with_grounding=True)
        assert prompt.startswith(SYSTEM_PROMPT)
        assert prompt.endswith(GROUNDING_RULE)
        # Critical: instructs the model to verify before answering, not
        # to hallucinate an "I don't know" — the rule's *job* is to
        # prevent confidently-wrong API signatures.
        assert "verifique" in prompt
        assert "Não invente" in prompt
