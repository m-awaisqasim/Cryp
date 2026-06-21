import json
import re
from datetime import datetime, timedelta
from pathlib import Path

from core.logger import get_logger
log = get_logger(__name__)


def _base_dir() -> Path:
    import sys
    if getattr(sys, "frozen", False):
        return Path(sys.executable).parent
    p = Path(__file__).resolve().parent
    while p != p.parent:
        if (p / "main.py").exists() or (p / ".git").exists():
            return p
        p = p.parent
    return Path(__file__).resolve().parent.parent.parent


STATS_PATH = _base_dir() / "memory" / "exam_prep.json"


def _load_stats() -> dict:
    if not STATS_PATH.exists():
        return {}
    try:
        raw = STATS_PATH.read_text(encoding="utf-8")
        data = json.loads(raw) if raw.strip() else {}
        return data if isinstance(data, dict) else {}
    except Exception:
        log.error("exam_prep_stats_load_error", exc_info=True)
        return {}


def _save_stats(stats: dict):
    try:
        STATS_PATH.parent.mkdir(parents=True, exist_ok=True)
        STATS_PATH.write_text(
            json.dumps(stats, indent=2, ensure_ascii=False), encoding="utf-8"
        )
    except Exception:
        log.error("exam_prep_stats_save_error", exc_info=True)


_session = {"topic": None, "questions": [], "current_index": 0, "correct": 0}


def _call_gemini(prompt: str, system: str = "", model_name: str = "gemini-2.5-flash-lite") -> str:
    from config.settings import GEMINI_API_KEY
    from core import gemini_compat as genai
    genai.configure(api_key=GEMINI_API_KEY)
    if system:
        model = genai.GenerativeModel(model_name=model_name, system_instruction=system)
    else:
        model = genai.GenerativeModel(model_name)
    response = model.generate_content(prompt)
    return response.text.strip()


def _generate_questions(topic: str, weak_subtopics: list[str] | None = None) -> list[dict]:
    weak_instruction = ""
    if weak_subtopics:
        weak_instruction = f" Focus extra questions on these weak areas: {', '.join(weak_subtopics)}."
    prompt = (
        f"Generate 5 short-answer practice questions on the topic '{topic}'.{weak_instruction}\n"
        "Each must have a one-line expected answer key.\n"
        "Return ONLY a JSON array, no markdown, no explanation:\n"
        '[{"q": "...", "expected": "..."}, ...]'
    )
    text = _call_gemini(prompt, system="You are an exam preparation coach that generates quiz questions.", model_name="gemini-2.5-flash")
    text = re.sub(r"```(?:json)?", "", text).strip().rstrip("`").strip()
    try:
        questions = json.loads(text)
        if isinstance(questions, list) and len(questions) >= 1 and all("q" in q and "expected" in q for q in questions):
            return questions[:5]
    except Exception:
        pass
    retry_prompt = (
        f"Generate 5 short-answer practice questions on '{topic}'.{weak_instruction}\n"
        "Respond with ONLY the JSON array, nothing else:\n"
        '[{"q": "...", "expected": "..."}, ...]'
    )
    text = _call_gemini(retry_prompt, system="You are an exam preparation coach. Output ONLY valid JSON.", model_name="gemini-2.5-flash")
    text = re.sub(r"```(?:json)?", "", text).strip().rstrip("`").strip()
    try:
        questions = json.loads(text)
        if isinstance(questions, list) and len(questions) >= 1 and all("q" in q and "expected" in q for q in questions):
            return questions
    except Exception:
        pass
    return []


def _grade_answer(question: str, expected: str, user_answer: str) -> tuple[bool, str]:
    prompt = (
        f"Question: {question}\n"
        f"Expected answer: {expected}\n"
        f"Student answer: {user_answer}\n\n"
        f"Respond with exactly one line:\n"
        f"CORRECT — if the student answer captures the key point of the expected answer.\n"
        f"INCORRECT: <one-line reason> — if not."
    )
    text = _call_gemini(prompt, system="You grade short-answer quiz responses. Be fair but accurate.")
    if text.startswith("CORRECT"):
        return True, text
    reason = text.replace("INCORRECT:", "").replace("INCORRECT", "").strip()
    return False, reason


def exam_prep_coach(parameters: dict, player=None, **kwargs) -> str:
    action = parameters.get("action", "status")

    if action == "start_session":
        topic = parameters.get("topic")
        if not topic:
            return "What topic do you want to be quizzed on, sir?"
        questions = _generate_questions(topic)
        if not questions:
            return "Sorry, I couldn't generate questions for that topic. Try a different one, sir."
        _session["topic"] = topic
        _session["questions"] = questions
        _session["current_index"] = 0
        _session["correct"] = 0
        total = len(questions)
        q = questions[0]["q"]
        return f"Question 1 of {total}: {q}"

    if action == "answer":
        user_answer = parameters.get("answer", "")
        if not _session["questions"]:
            return "No active quiz session, sir. Say start a session first."
        idx = _session["current_index"]
        q_data = _session["questions"][idx]
        is_correct, feedback = _grade_answer(q_data["q"], q_data["expected"], user_answer)
        stats = _load_stats()
        topic = _session["topic"]
        if topic:
            topic_key = topic.lower()
            if topic_key not in stats:
                stats[topic_key] = {"asked": 0, "correct": 0, "wrong": 0, "last_reviewed": "", "weak_subtopics": []}
            stats[topic_key]["asked"] += 1
            stats[topic_key]["last_reviewed"] = datetime.now().isoformat(timespec="seconds")
            if is_correct:
                stats[topic_key]["correct"] += 1
                _session["correct"] += 1
            else:
                stats[topic_key]["wrong"] += 1
                note = q_data["q"][:60]
                if note not in stats[topic_key]["weak_subtopics"]:
                    stats[topic_key]["weak_subtopics"].append(note)
            _save_stats(stats)
        _session["current_index"] += 1
        if is_correct:
            line = f"Correct, sir. {feedback}" if feedback and feedback != "CORRECT" else "Correct, sir."
        else:
            line = f"Not quite, sir. The expected answer was: {q_data['expected']}."
        if _session["current_index"] >= len(_session["questions"]):
            total = len(_session["questions"])
            correct = _session["correct"]
            _session["questions"] = []
            return f"{line} Quiz complete! You got {correct} of {total} correct, sir."
        total = len(_session["questions"])
        next_q = _session["questions"][_session["current_index"]]
        return f"{line} Next question: Question {_session['current_index'] + 1} of {total}: {next_q['q']}"

    if action == "review_weak_areas":
        stats = _load_stats()
        candidates = [(t, s) for t, s in stats.items() if s.get("asked", 0) >= 2]
        if not candidates:
            return "Not enough data to identify weak areas yet. Take more quizzes first, sir."
        worst = max(candidates, key=lambda x: x[1]["wrong"] / max(x[1]["asked"], 1))
        topic = worst[0].title()
        weak = worst[1].get("weak_subtopics", [])
        questions = _generate_questions(topic, weak_subtopics=weak)
        if not questions:
            return f"I couldn't generate review questions for {topic}, sir."
        _session["topic"] = topic
        _session["questions"] = questions
        _session["current_index"] = 0
        _session["correct"] = 0
        total = len(questions)
        return f"Let's review {topic}, focusing on your weak areas. Question 1 of {total}: {questions[0]['q']}"

    if action == "schedule_review":
        topic = parameters.get("topic")
        if not topic:
            return "Which topic should I schedule a review for, sir?"
        days = int(parameters.get("days", 3))
        from actions.reminder import reminder
        target = datetime.now() + timedelta(days=days)
        result = reminder({
            "date": target.strftime("%Y-%m-%d"),
            "time": "09:00",
            "message": f"Time to review {topic}, sir.",
        })
        if not result.startswith("Reminder set"):
            return f"Couldn't schedule the review reminder: {result}"
        return f"Scheduled a review reminder for {topic} in {days} days."

    if action == "status":
        if not _session["questions"]:
            stats = _load_stats()
            if stats:
                lines = []
                for t, s in sorted(stats.items(), key=lambda x: x[1].get("last_reviewed", ""), reverse=True)[:5]:
                    rate = ""
                    if s.get("asked", 0) >= 2:
                        pct = int((s["correct"] / s["asked"]) * 100)
                        rate = f" ({pct}% correct)"
                    lines.append(f"{t.title()}: {s['asked']} questions{rate}")
                return "Exam prep stats, sir:\n" + "\n".join(lines) + "\nSay 'start session on <topic>' to begin a quiz."
            return "No exam prep data yet, sir. Say 'quiz me on <topic>' to start."
        idx = _session["current_index"]
        total = len(_session["questions"])
        return f"Active quiz: {_session['topic']}, question {idx + 1} of {total}."

    return "Unknown exam_prep_coach action."
