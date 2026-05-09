import json
from datetime import datetime, timezone
from pathlib import Path

from flask import Flask, abort, jsonify, redirect, render_template, request, url_for

app = Flask(__name__)

BASE_DIR = Path(__file__).resolve().parent
CONTENT_FILE = BASE_DIR / "prototype_content.json"
ACTIVITY_FILE = BASE_DIR / "activity_log.json"


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def load_content() -> dict:
    with CONTENT_FILE.open("r", encoding="utf-8") as content_file:
        payload = json.load(content_file)

    required_keys = ["home", "lessons", "quiz_questions"]
    for key in required_keys:
        if key not in payload:
            raise ValueError(f"prototype_content.json is missing '{key}'.")

    if not isinstance(payload["lessons"], list) or not isinstance(payload["quiz_questions"], list):
        raise ValueError("Lessons and quiz_questions must both be lists.")

    return payload


CONTENT = load_content()
LESSONS = CONTENT["lessons"]
QUIZ_QUESTIONS = CONTENT["quiz_questions"]
TOTAL_STEPS = int(CONTENT.get("total_steps", 14))


state = {}


def reset_state() -> None:
    state.clear()
    state.update(
        {
            "started_at": None,
            "page_entries": [],
            "lesson_continues": {},
            "quiz_answers": {},
            "events": [],
        }
    )


reset_state()


def persist_activity() -> None:
    snapshot = {
        "saved_at": now_iso(),
        "started_at": state["started_at"],
        "page_entries": state["page_entries"],
        "lesson_continues": state["lesson_continues"],
        "quiz_answers": state["quiz_answers"],
        "events": state["events"],
    }
    with ACTIVITY_FILE.open("w", encoding="utf-8") as activity_file:
        json.dump(snapshot, activity_file, indent=2)


def log_event(event_type: str, details: dict | None = None) -> None:
    event = {
        "timestamp": now_iso(),
        "event_type": event_type,
        "details": details or {},
    }
    state["events"].append(event)
    persist_activity()


def record_page_entry(page_type: str, page_number: int | None = None, phase: str | None = None) -> None:
    page_event = {
        "timestamp": now_iso(),
        "page_type": page_type,
        "page_number": page_number,
        "phase": phase,
    }
    state["page_entries"].append(page_event)
    log_event("page_entered", page_event)


def ensure_started() -> bool:
    return bool(state["started_at"])


def get_lesson(lesson_number: int) -> dict | None:
    if 1 <= lesson_number <= len(LESSONS):
        return LESSONS[lesson_number - 1]
    return None


def get_question(question_number: int) -> dict | None:
    if 1 <= question_number <= len(QUIZ_QUESTIONS):
        return QUIZ_QUESTIONS[question_number - 1]
    return None


def find_choice(choices: list[dict], selected_id: str) -> dict | None:
    for choice in choices:
        if choice["id"] == selected_id:
            return choice
    return None


def format_order_answer(question: dict, selected_ids: list[str]) -> str:
    labels_by_id = {item["id"]: item["label"] for item in question.get("order_items", [])}
    return " -> ".join(labels_by_id.get(item_id, item_id) for item_id in selected_ids)


def correct_answer_label(question: dict) -> str:
    if question.get("answer_type") == "order":
        return format_order_answer(question, question.get("correct_order", []))

    correct_choice = find_choice(question.get("choices", []), question.get("correct_choice_id", ""))
    if correct_choice:
        return correct_choice["label"]
    return ""


def submitted_answer_label(submitted: dict | None) -> str:
    if not submitted:
        return "No answer submitted."
    return submitted.get("answer_label") or submitted.get("choice_label", "")


def is_submitted_answer_correct(question: dict, submitted: dict | None) -> bool:
    if not submitted:
        return False

    if question.get("answer_type") == "order":
        return submitted.get("order_ids") == question.get("correct_order", [])

    return submitted.get("choice_id") == question.get("correct_choice_id")


def common_template_context(active_section: str = "home") -> dict:
    return {
        "site_title": CONTENT.get("site_title", "Meal Order Glucose Coach"),
        "active_section": active_section,
        "lesson_count": len(LESSONS),
        "quiz_count": len(QUIZ_QUESTIONS),
        "total_steps": TOTAL_STEPS,
    }


@app.route("/")
def home():
    record_page_entry("home")

    context = common_template_context(active_section="home")
    context.update(
        {
            "home": CONTENT["home"],
            "has_started": bool(state["started_at"]),
            "lesson_continue_count": len(state["lesson_continues"]),
            "quiz_count_answered": len(state["quiz_answers"]),
        }
    )
    return render_template("home.html", **context)


@app.route("/start", methods=["POST"])
def start():
    reset_state()
    state["started_at"] = now_iso()
    log_event("learning_started", {"next_route": "/learn/1"})
    return redirect(url_for("learn", lesson_number=1))


@app.route("/learn/<int:lesson_number>", methods=["GET", "POST"])
def learn(lesson_number: int):
    if not ensure_started():
        return redirect(url_for("home"))

    lesson = get_lesson(lesson_number)
    if lesson is None:
        abort(404)

    if request.method == "POST":
        state["lesson_continues"][str(lesson_number)] = now_iso()
        log_event("lesson_continue_clicked", {"lesson_number": lesson_number})

        if lesson_number == len(LESSONS):
            return redirect(url_for("quiz", question_number=1))
        return redirect(url_for("learn", lesson_number=lesson_number + 1))

    record_page_entry("learn", lesson_number)

    step_number = int(lesson.get("step_number", lesson_number + 1))
    context = common_template_context(active_section="learn")
    context.update(
        {
            "lesson": lesson,
            "lesson_number": lesson_number,
            "step_number": step_number,
            "has_previous": lesson_number > 1,
            "has_next": lesson_number < len(LESSONS),
            "learning_progress_percent": int((lesson_number / len(LESSONS)) * 100),
        }
    )
    return render_template("learn.html", **context)


@app.route("/quiz/<int:question_number>", methods=["GET", "POST"])
def quiz(question_number: int):
    if not ensure_started():
        return redirect(url_for("home"))

    question = get_question(question_number)
    if question is None:
        abort(404)

    phase = request.args.get("phase", "question")
    error = ""

    if request.method == "POST":
        if question.get("answer_type") == "order":
            selected_order = [
                item_id.strip()
                for item_id in request.form.get("order_ids", "").split(",")
                if item_id.strip()
            ]
            expected_ids = {item["id"] for item in question.get("order_items", [])}

            if set(selected_order) != expected_ids or len(selected_order) != len(expected_ids):
                error = "Arrange every meal item before continuing."
                phase = "question"
            else:
                state["quiz_answers"][str(question_number)] = {
                    "answer_type": "order",
                    "question_id": question["id"],
                    "question": question["question"],
                    "order_ids": selected_order,
                    "answer_label": format_order_answer(question, selected_order),
                    "submitted_at": now_iso(),
                }
                log_event(
                    "quiz_answer_saved",
                    {
                        "question_number": question_number,
                        "answer_type": "order",
                        "order_ids": selected_order,
                    },
                )
                return redirect(url_for("quiz", question_number=question_number, phase="feedback"))
        else:
            selected_choice = request.form.get("choice_id", "").strip()
            matched_choice = find_choice(question.get("choices", []), selected_choice)

            if not matched_choice:
                error = "Select an answer before continuing."
                phase = "question"
            else:
                state["quiz_answers"][str(question_number)] = {
                    "answer_type": "choice",
                    "question_id": question["id"],
                    "question": question["question"],
                    "choice_id": matched_choice["id"],
                    "choice_label": matched_choice["label"],
                    "answer_label": matched_choice["label"],
                    "submitted_at": now_iso(),
                }
                log_event(
                    "quiz_answer_saved",
                    {
                        "question_number": question_number,
                        "answer_type": "choice",
                        "choice_id": matched_choice["id"],
                    },
                )
                return redirect(url_for("quiz", question_number=question_number, phase="feedback"))

    saved_answer = state["quiz_answers"].get(str(question_number))

    show_feedback = phase == "feedback"
    if show_feedback and not saved_answer:
        return redirect(url_for("quiz", question_number=question_number))

    if show_feedback:
        record_page_entry("quiz", question_number, phase="feedback")
    else:
        record_page_entry("quiz", question_number, phase="question")

    is_correct = is_submitted_answer_correct(question, saved_answer)

    if question_number < len(QUIZ_QUESTIONS):
        next_url = url_for("quiz", question_number=question_number + 1)
    else:
        next_url = url_for("quiz_results")

    context = common_template_context(active_section="quiz")
    context.update(
        {
            "question": question,
            "question_number": question_number,
            "step_number": int(question.get("step_number", 11 + question_number)),
            "show_feedback": show_feedback,
            "error": error,
            "saved_answer": saved_answer,
            "saved_answer_label": submitted_answer_label(saved_answer),
            "correct_answer_label": correct_answer_label(question),
            "is_correct": is_correct,
            "next_url": next_url,
            "quiz_progress_percent": int((question_number / len(QUIZ_QUESTIONS)) * 100),
        }
    )
    return render_template("quiz.html", **context)


@app.route("/quiz/results")
def quiz_results():
    if not ensure_started():
        return redirect(url_for("home"))

    record_page_entry("quiz_results")

    score = 0
    reviewed_questions = []
    for question_number, question in enumerate(QUIZ_QUESTIONS, start=1):
        submitted = state["quiz_answers"].get(str(question_number))
        is_correct = is_submitted_answer_correct(question, submitted)
        if is_correct:
            score += 1

        reviewed_questions.append(
            {
                "question_number": question_number,
                "question": question,
                "submitted": submitted,
                "submitted_label": submitted_answer_label(submitted),
                "is_correct": is_correct,
                "correct_answer_label": correct_answer_label(question),
            }
        )

    percent = int((score / max(len(QUIZ_QUESTIONS), 1)) * 100)

    context = common_template_context(active_section="results")
    context.update(
        {
            "score": score,
            "total": len(QUIZ_QUESTIONS),
            "percent": percent,
            "reviewed_questions": reviewed_questions,
            "wrap_up": CONTENT.get("wrap_up", {}),
            "page_entry_count": len(state["page_entries"]),
        }
    )
    return render_template("results.html", **context)


@app.route("/api/progress")
def api_progress():
    return jsonify(
        {
            "started_at": state["started_at"],
            "page_entries": state["page_entries"],
            "lesson_continues": state["lesson_continues"],
            "quiz_answers": state["quiz_answers"],
            "events": state["events"],
        }
    )


@app.route("/api/event", methods=["POST"])
def api_event():
    payload = request.get_json(silent=True) or {}
    event_type = str(payload.get("event_type", "interaction")).strip() or "interaction"
    details = payload.get("details", {})
    if not isinstance(details, dict):
        details = {"value": details}
    log_event(event_type, details)
    return jsonify({"ok": True})


if __name__ == "__main__":
    app.run(debug=True)
