"""Tests for the Pub Quiz game logic."""

import sys
from unittest.mock import patch

import pytest
import requests

from pub_quiz import ask_question, get_player_name, make_request, score_message, run_quiz
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
# make_request
# ---------------------------------------------------------------------------

class TestMakeRequest:
    def test_returns_json_response_when_available(self):
        with patch("pub_quiz.requests.get") as mock_get:
            mock_response = mock_get.return_value
            mock_response.raise_for_status.return_value = None
            mock_response.json.return_value = {"ok": True}
            result = make_request("https://example.com/api")

        assert result == {"ok": True}
        mock_get.assert_called_once_with("https://example.com/api", timeout=10.0)
        mock_response.raise_for_status.assert_called_once()

    def test_falls_back_to_text_when_json_is_not_available(self):
        with patch("pub_quiz.requests.get") as mock_get:
            mock_response = mock_get.return_value
            mock_response.raise_for_status.return_value = None
            mock_response.json.side_effect = requests.exceptions.JSONDecodeError("not json", "x", 0)
            mock_response.text = "plain text"
            result = make_request("https://example.com/text")

        assert result == "plain text"
        mock_response.json.assert_called_once()

    def test_raises_helpful_error_when_requests_is_missing(self, monkeypatch):
        monkeypatch.setattr("pub_quiz.requests", None)
        with pytest.raises(RuntimeError, match="pip install requests"):
            make_request("https://example.com")

    def test_raises_for_non_http_url(self):
        with pytest.raises(ValueError, match="absolute http\\(s\\) URL"):
            make_request("file:///etc/hosts")

    def test_propagates_request_errors(self):
        with patch("pub_quiz.requests.get", side_effect=requests.exceptions.Timeout):
            with pytest.raises(requests.exceptions.Timeout):
                make_request("https://example.com/api")


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
