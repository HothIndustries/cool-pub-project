"""Tests for the Pub Quiz game logic."""

import sys
import json
from unittest.mock import patch

import pytest

from pub_quiz import ask_question, fetch_questions, get_player_name, score_message, run_quiz
from questions import QUESTIONS

# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

SAMPLE_QUESTION = {
    "category": "Science",
    "question": "What is the chemical symbol for gold?",
    "choices": ["A) Go", "B) Gd", "C) Au", "D) Ag"],
    "answer": "C",
    "fun_fact": "Gold's symbol comes from its Latin name 'Aurum'.",
}


# ---------------------------------------------------------------------------
# score_message
# ---------------------------------------------------------------------------

class TestScoreMessage:
    def test_perfect_score(self):
        msg = score_message(10, 10)
        assert "Perfect" in msg or "champion" in msg

    def test_high_score(self):
        msg = score_message(8, 10)
        assert msg  # just a non-empty string

    def test_mid_score(self):
        msg = score_message(5, 10)
        assert msg

    def test_low_score(self):
        msg = score_message(2, 10)
        assert msg

    def test_zero_score(self):
        msg = score_message(0, 10)
        assert msg

    def test_zero_total_does_not_raise(self):
        # Edge case: avoid division by zero
        msg = score_message(0, 0)
        assert isinstance(msg, str)


# ---------------------------------------------------------------------------
# ask_question
# ---------------------------------------------------------------------------

class TestAskQuestion:
    def test_correct_answer_returns_true(self, capsys):
        with patch("builtins.input", return_value="C"):
            result = ask_question(1, 5, SAMPLE_QUESTION)
        assert result is True
        captured = capsys.readouterr()
        assert "Correct" in captured.out

    def test_wrong_answer_returns_false(self, capsys):
        with patch("builtins.input", return_value="A"):
            result = ask_question(1, 5, SAMPLE_QUESTION)
        assert result is False
        captured = capsys.readouterr()
        assert "Nope" in captured.out

    def test_quit_exits(self):
        with patch("builtins.input", return_value="quit"), pytest.raises(SystemExit):
            ask_question(1, 5, SAMPLE_QUESTION)

    def test_invalid_then_valid_answer(self, capsys):
        # First input is invalid, second is correct
        with patch("builtins.input", side_effect=["X", "C"]):
            result = ask_question(1, 5, SAMPLE_QUESTION)
        assert result is True
        captured = capsys.readouterr()
        assert "Please enter" in captured.out


# ---------------------------------------------------------------------------
# get_player_name
# ---------------------------------------------------------------------------

class TestGetPlayerName:
    def test_returns_input_name(self):
        with patch("builtins.input", return_value="Alice"):
            assert get_player_name() == "Alice"

    def test_empty_input_returns_default(self):
        with patch("builtins.input", return_value=""):
            assert get_player_name() == "Mystery Drinker"

    def test_whitespace_input_returns_default(self):
        with patch("builtins.input", return_value="   "):
            assert get_player_name() == "Mystery Drinker"


# ---------------------------------------------------------------------------
# fetch_questions
# ---------------------------------------------------------------------------

class TestFetchQuestions:
    class MockResponse:
        def __init__(self, payload):
            self.payload = payload

        def __enter__(self):
            return self

        def __exit__(self, exc_type, exc, tb):
            return None

        def read(self):
            return json.dumps(self.payload).encode("utf-8")

    def test_fetches_valid_question_bank(self):
        response = [
            {
                "category": "Science",
                "question": "What is H2O?",
                "choices": ["A) Salt", "B) Water", "C) Gold", "D) Iron"],
                "answer": "B",
                "fun_fact": "Water covers around 71% of Earth's surface.",
            }
        ]

        with patch("pub_quiz.urllib.request.urlopen", return_value=self.MockResponse(response)):
            assert fetch_questions("https://example.com/questions.json") == response

    def test_raises_for_non_list_payload(self):
        with patch(
            "pub_quiz.urllib.request.urlopen", return_value=self.MockResponse({"bad": "payload"})
        ):
            with pytest.raises(ValueError, match="JSON list"):
                fetch_questions("https://example.com/questions.json")


# ---------------------------------------------------------------------------
# run_quiz (integration)
# ---------------------------------------------------------------------------

class TestRunQuiz:
    def _make_inputs(self, name: str, answers: list[str]) -> list[str]:
        return [name] + answers

    def test_returns_correct_score(self):
        questions = [SAMPLE_QUESTION]
        inputs = self._make_inputs("Bob", ["C"])  # correct answer
        with patch("builtins.input", side_effect=inputs):
            result = run_quiz(questions=questions, num_questions=1)
        assert result["name"] == "Bob"
        assert result["score"] == 1
        assert result["total"] == 1

    def test_returns_zero_score_on_wrong_answers(self):
        questions = [SAMPLE_QUESTION]
        inputs = self._make_inputs("Eve", ["A"])  # wrong answer
        with patch("builtins.input", side_effect=inputs):
            result = run_quiz(questions=questions, num_questions=1)
        assert result["score"] == 0

    def test_num_questions_capped_by_pool_size(self):
        questions = [SAMPLE_QUESTION]
        inputs = self._make_inputs("Sam", ["C"])
        with patch("builtins.input", side_effect=inputs):
            result = run_quiz(questions=questions, num_questions=999)
        assert result["total"] == 1

    def test_can_use_questions_url(self):
        questions = [SAMPLE_QUESTION]
        inputs = self._make_inputs("Rae", ["C"])
        with patch("pub_quiz.fetch_questions", return_value=questions):
            with patch("builtins.input", side_effect=inputs):
                result = run_quiz(questions_url="https://example.com/questions.json", num_questions=1)
        assert result["name"] == "Rae"
        assert result["score"] == 1
        assert result["total"] == 1

    def test_question_bank_is_not_empty(self):
        assert len(QUESTIONS) > 0

    def test_all_questions_have_required_keys(self):
        required = {"category", "question", "choices", "answer", "fun_fact"}
        for q in QUESTIONS:
            assert required.issubset(q.keys()), f"Missing keys in: {q}"

    def test_all_answers_are_valid_choices(self):
        valid = {"A", "B", "C", "D"}
        for q in QUESTIONS:
            assert q["answer"].upper() in valid, f"Bad answer in: {q}"
