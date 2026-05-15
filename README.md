# 🍺 The Rusty Pint Pub Quiz

A fun, small Python CLI trivia game. Grab a virtual pint and test your knowledge across Science, History, Pop Culture, and Geography!

## Features

- 12 trivia questions across 4 categories
- Random question selection every game — no two rounds are the same
- Instant feedback with fun facts after each answer
- Score summary with flavourful commentary at the end
- HTTP request helper for fetching data from web APIs

## Requirements

- Python 3.10+
- requests (required for the HTTP request helper feature)

Install dependencies with:

```bash
pip install requests
```

## Running the game

```bash
python pub_quiz.py
```

## Running the tests

```bash
python -m pytest test_pub_quiz.py -v
```

## Project structure

```
cool-pub-project/
├── pub_quiz.py        # Main game entry point
├── questions.py       # Trivia question bank
├── test_pub_quiz.py   # Unit & integration tests
└── README.md
```
