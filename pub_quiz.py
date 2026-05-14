"""
🍺 Welcome to The Rusty Pint Pub Quiz! 🍺
A fun CLI trivia game — grab a pint and test your knowledge.
"""

import random
import textwrap
import sys
import json
import urllib.request
import urllib.error

from questions import QUESTIONS

BANNER = r"""
  ____        _      ___        _
 |  _ \ _   _| |__  / _ \ _   _(_)__
 | |_) | | | | '_ \| | | | | | | |_ /
 |  __/| |_| | |_) | |_| | |_| | |/ /
 |_|    \__,_|_.__/ \__\_\\__,_|_/__|

        🍺  The Rusty Pint Pub Quiz  🍺
"""

DIVIDER = "─" * 52
QUESTION_KEYS = {"category", "question", "choices", "answer", "fun_fact"}


def print_banner() -> None:
    """Print the welcome banner."""
    print(BANNER)
    print(DIVIDER)
    print("  Answer A, B, C, or D for each question.")
    print("  Type 'quit' at any time to leave the pub.")
    print(DIVIDER)


def get_player_name() -> str:
    """Prompt for and return the player's name."""
    name = input("\nWhat's your name, punter? ").strip()
    return name if name else "Mystery Drinker"


def ask_question(index: int, total: int, q: dict) -> bool:
    """
    Display a question and collect the player's answer.

    Returns True if the answer is correct, False otherwise.
    """
    print(f"\n[Question {index}/{total}]  📚 Category: {q['category']}")
    print(textwrap.fill(q["question"], width=52))
    print()
    for choice in q["choices"]:
        print(f"  {choice}")
    print()

    while True:
        raw = input("Your answer: ").strip().upper()
        if raw == "QUIT":
            print("\nThanks for popping in — come back soon! 🍻\n")
            sys.exit(0)
        if raw in ("A", "B", "C", "D"):
            break
        print("  ⚠  Please enter A, B, C, or D (or 'quit' to exit).")

    correct = raw == q["answer"].upper()
    if correct:
        print("  ✅  Correct! Well done!")
    else:
        print(f"  ❌  Nope! The answer was {q['answer']}.")
    print(f"  💡  {q['fun_fact']}")
    return correct


def score_message(score: int, total: int) -> str:
    """Return a flavourful message based on the player's score."""
    pct = score / total if total else 0
    if pct == 1.0:
        return "🏆 Perfect score! You're the pub quiz champion!"
    if pct >= 0.75:
        return "🥇 Brilliant effort — you clearly know your stuff!"
    if pct >= 0.5:
        return "🥈 Not bad at all — another round and you'd ace it!"
    if pct >= 0.25:
        return "🥉 Room for improvement, but good effort!"
    return "🍺 Better luck next time — maybe lay off the Guinness first..."


def fetch_questions(url: str, timeout: int = 10) -> list:
    """Fetch a JSON question bank from an HTTP endpoint."""
    try:
        with urllib.request.urlopen(url, timeout=timeout) as response:
            payload = response.read().decode("utf-8")
    except urllib.error.URLError as exc:
        raise ValueError(f"Could not fetch questions from URL: {url}") from exc

    try:
        data = json.loads(payload)
    except json.JSONDecodeError as exc:
        raise ValueError("Question payload must be valid JSON.") from exc

    if not isinstance(data, list):
        raise ValueError("Question payload must be a JSON list.")

    for q in data:
        if not isinstance(q, dict):
            raise ValueError("Each question must be an object.")
        missing = QUESTION_KEYS - set(q.keys())
        if missing:
            missing_keys = ", ".join(sorted(missing))
            raise ValueError(f"Each question must include required keys: {missing_keys}")
        if not isinstance(q["answer"], str):
            raise ValueError("Question answers must be strings: A, B, C, or D.")
        if q["answer"].upper() not in {"A", "B", "C", "D"}:
            raise ValueError("Question answers must be A, B, C, or D.")

    return data


def run_quiz(
    questions: list | None = None, num_questions: int = 6, questions_url: str | None = None
) -> dict:
    """
    Run the full quiz game loop.

    Args:
        questions:     Question pool to draw from (defaults to the full bank).
        num_questions: How many questions to ask.

    Returns:
        A dict with keys ``name``, ``score``, and ``total``.
    """
    if questions is None:
        questions = fetch_questions(questions_url) if questions_url else QUESTIONS

    print_banner()
    name = get_player_name()
    print(f"\nGreat to have you, {name}! Let's get started…\n")
    print(DIVIDER)

    pool = random.sample(questions, min(num_questions, len(questions)))
    score = 0

    for i, q in enumerate(pool, start=1):
        if ask_question(i, len(pool), q):
            score += 1

    print(f"\n{DIVIDER}")
    print(f"  {name}'s final score: {score}/{len(pool)}")
    print(f"  {score_message(score, len(pool))}")
    print(f"{DIVIDER}\n")

    return {"name": name, "score": score, "total": len(pool)}


if __name__ == "__main__":
    run_quiz()
