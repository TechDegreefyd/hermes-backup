import os
import json
import requests
from datetime import datetime, timedelta
from fastapi import FastAPI, Request, BackgroundTasks
from dotenv import load_dotenv

WORKDIR = "/home/mohit/workspace"
load_dotenv(os.path.join(WORKDIR, ".env"))

WHAPI_TOKEN = os.getenv("WHAPI_TOKEN")
WHAPI_URL = "https://gate.whapi.cloud"
ADMIN_GROUP = os.getenv("WHATSAPP_GROUP", "120363426619711887@g.us")

app = FastAPI(title="Degreefyd MBA Fit WhatsApp Bot")
USER_STATES = {}
PAUSED_CHATS = set()
CONVERSATIONS = {}
CONVERSATION_LOG_PATH = os.path.join(WORKDIR, "mba_fit_bot_conversations.jsonl")
SEND_LOG_PATH = os.path.join(WORKDIR, "mba_fit_bot_send_log.jsonl")

UNIVERSITIES = {
    "uni_manipal": {
        "name": "Manipal Online MBA",
        "short": "Manipal",
        "desc": "⭐ 89% placements · ₹1.5L · NIRF #6",
        "fees": "₹1.5L",
        "emi": "₹4,500/mo",
        "placement": "89% placement rate",
        "format": "Live weekend classes",
        "accreditation": "NIRF #6 · UGC-entitled online degree",
    },
    "uni_amity": {
        "name": "Amity Online MBA",
        "short": "Amity",
        "desc": "⭐ EMI ₹4,500/mo · ₹1.2L · 10+ specs",
        "fees": "₹1.2L",
        "emi": "₹4,500/mo",
        "placement": "Strong online MBA network",
        "format": "Flexible online learning",
        "accreditation": "UGC-entitled · 10+ specializations",
    },
    "uni_nmims": {
        "name": "NMIMS Online MBA",
        "short": "NMIMS",
        "desc": "⭐ Top brand recall · ₹2L · Mumbai legacy",
        "fees": "₹2L",
        "emi": "Available",
        "placement": "Top brand recall",
        "format": "Structured online format",
        "accreditation": "Mumbai legacy · recognized brand",
    },
    "uni_jain": {
        "name": "Jain University MBA",
        "short": "Jain",
        "desc": "⭐ Flexible 2-4 yrs · ₹1.4L · Self-paced",
        "fees": "₹1.4L",
        "emi": "Available",
        "placement": "Career-focused programs",
        "format": "Flexible 2-4 yrs · self-paced",
        "accreditation": "UGC-entitled online degree",
    },
}

Q1_OPTIONS = {
    "q1_work_grow": "Working — want to grow",
    "q1_work_switch": "Working — want to switch",
    "q1_recent_role": "Recent grad — first big role",
    "q1_recent_career": "Recent grad — building career",
    "q1_between_jobs": "Between jobs — comeback time",
    "q1_break": "On a career break",
    "q1_govt": "Government job prep",
    "q1_exploring": "Just exploring options",
}

Q2_OPTIONS = {
    "q2_afford": "💰 Will I afford it?",
    "q2_time": "⏰ Time alongside work?",
    "q2_value": "🤔 Will employers value it?",
    "q2_right_course": "🧐 Am I picking the right course?",
    "q2_late": "⏳ Am I too late to start?",
    "q2_exam": "📚 What about exam difficulty?",
    "q2_family": "🏠 Family/personal situation",
    "q2_gap": "💼 Career break gaps",
}

CALL_OPTIONS = {
    "call_today_6": "Today, 6:00 PM",
    "call_tom_11": "Tomorrow, 11:00 AM",
    "call_tom_7": "Tomorrow, 7:00 PM",
    "call_tom_morning": "Tomorrow morning (8-10 AM)",
    "call_day_after": "Day after tomorrow",
    "call_weekend": "This weekend",
    "call_anytime": "Just request a callback whenever",
    "call_exact": "Pick exact date/time",
}


def _headers():
    return {
        "accept": "application/json",
        "content-type": "application/json",
        "authorization": f"Bearer {WHAPI_TOKEN}",
    }


def log_event(chat_id, direction, text, meta=None):
    event = {
        "ts": datetime.now().isoformat(),
        "chat_id": chat_id,
        "direction": direction,
        "text": text,
        "meta": meta or {},
    }
    CONVERSATIONS.setdefault(chat_id, []).append(event)
    try:
        with open(CONVERSATION_LOG_PATH, "a", encoding="utf-8") as f:
            f.write(json.dumps(event, ensure_ascii=False) + "\n")
    except Exception:
        pass


def payload_text(payload):
    if not isinstance(payload, dict):
        return ""
    if payload.get("body") and isinstance(payload.get("body"), str):
        return payload.get("body", "")
    body = payload.get("body") or {}
    if isinstance(body, dict):
        return body.get("text", "")
    return ""


def send_whapi_message(payload, endpoint="messages/interactive"):
    url = f"{WHAPI_URL}/{endpoint}"
    response = requests.post(url, json=payload, headers=_headers(), timeout=20)
    try:
        result = response.json()
    except Exception:
        result = {"status_code": response.status_code, "text": response.text}
    to = payload.get("to")
    text = payload_text(payload)
    log_event(to, "bot", text, {"endpoint": endpoint, "payload_type": payload.get("type"), "response": result})
    try:
        with open(SEND_LOG_PATH, "a", encoding="utf-8") as f:
            f.write(json.dumps({"ts": datetime.now().isoformat(), "endpoint": endpoint, "payload": payload, "response": result}, ensure_ascii=False) + "\n")
    except Exception:
        pass
    return result


def send_text_message(to, text):
    return send_whapi_message({"to": to, "body": text}, endpoint="messages/text")


def send_buttons(to, text, buttons):
    payload = {
        "to": to,
        "type": "button",
        "body": {"text": text},
        "action": {"buttons": [{"type": "quick_reply", "title": title[:20], "id": bid} for bid, title in buttons]},
    }
    return send_whapi_message(payload)


def send_list(to, text, button, section_title, rows):
    payload = {
        "to": to,
        "type": "list",
        "body": {"text": text},
        "action": {
            "button": button[:20],
            "sections": [{
                "title": section_title[:24],
                "rows": [
                    {
                        "id": rid,
                        "title": title[:24],
                        "description": desc[:72] if desc else "Select this option",
                    }
                    for rid, title, desc in rows
                ],
            }],
        },
    }
    return send_whapi_message(payload)


def initial_state(first_name="Priya", university="Manipal Online", course="MBA"):
    return {
        "step": "WAITING_STAGE0",
        "first_name": first_name,
        "university": university,
        "course": course,
        "answers": {},
        "created_at": datetime.now().isoformat(),
    }


def stage0_opening(to, first_name="Priya", university="Manipal Online", course="MBA"):
    USER_STATES[to] = initial_state(first_name, university, course)
    text = (
        f"Hey {first_name} 👋\n\n"
        f"I noticed you were exploring {university} {course} with us last week — but the admission isn't locked in yet.\n"
        "No pressure at all 🙂\n"
        "If you've got 2 minutes, I'd love to ask you 4 quick questions so we can help you find a college that actually fits your goals."
    )
    return send_buttons(to, text, [
        ("start_yes", "Yes, let's do it"),
        ("start_later", "Maybe later"),
        ("start_no", "Not interested"),
    ])


def send_stage1(to, state):
    state["step"] = "WAITING_Q1"
    USER_STATES[to] = state
    text = (
        "Awesome! 🎯\n"
        "Question 1 of 4\n\n"
        "Where are you in life right now, and why are you thinking about this MBA?\n"
        "Pick whichever fits best:\n\n"
        "1️⃣ Working — want to grow\n"
        "2️⃣ Working — want to switch\n"
        "3️⃣ Recent grad — first big role\n\n"
        "For more options, tap below."
    )
    send_buttons(to, text, [
        ("q1_work_grow", "Working: grow"),
        ("q1_work_switch", "Working: switch"),
        ("q1_recent_role", "Recent grad"),
    ])
    return send_list(to, "See more options for Question 1:", "See more options", "More options", [
        ("q1_recent_career", "Recent grad career", "Recent grad — building career"),
        ("q1_between_jobs", "Between jobs", "Between jobs — comeback time"),
        ("q1_break", "Career break", "On a career break"),
        ("q1_govt", "Govt job prep", "Government job prep"),
        ("q1_exploring", "Just exploring", "Just exploring options"),
    ])


def q1_dynamic_goal(q1):
    if "switch" in q1.lower():
        return "switch into a better role"
    if "recent grad" in q1.lower():
        return "build your first serious career path"
    if "between jobs" in q1.lower() or "comeback" in q1.lower():
        return "make a strong comeback"
    if "break" in q1.lower():
        return "restart your career with confidence"
    if "government" in q1.lower():
        return "keep a backup career path ready"
    if "exploring" in q1.lower():
        return "understand your options clearly"
    return "grow in your career"


def send_stage2(to, state):
    state["step"] = "WAITING_Q2"
    USER_STATES[to] = state
    goal = q1_dynamic_goal(state["answers"].get("life_stage", ""))
    text = (
        f"Got it — you're aiming to {goal}. Good context 👍\n\n"
        "Question 2 of 4\n\n"
        "What's the real worry holding you back?\n"
        "Be honest — we've heard it all 😊\n\n"
        "1️⃣ 💰 Will I afford it?\n"
        "2️⃣ ⏰ Time alongside work?\n"
        "3️⃣ 🤔 Will employers value it?"
    )
    send_buttons(to, text, [
        ("q2_afford", "💰 Afford it?"),
        ("q2_time", "⏰ Time with work?"),
        ("q2_value", "🤔 Employer value?"),
    ])
    return send_list(to, "Other concerns:", "Other concerns", "Other concerns", [
        ("q2_right_course", "Right course?", "🧐 Am I picking the right course?"),
        ("q2_late", "Too late?", "⏳ Am I too late to start?"),
        ("q2_exam", "Exam difficulty", "📚 What about exam difficulty?"),
        ("q2_family", "Family situation", "🏠 Family/personal situation"),
        ("q2_gap", "Career break gaps", "💼 Career break gaps"),
    ])


def alumni_name_for(state):
    q1 = state["answers"].get("life_stage", "").lower()
    q2 = state["answers"].get("worry", "").lower()
    if "recent grad" in q1 and "employers" in q2:
        return "Aarav", "used the NMIMS brand to break into his first big role"
    if "time" in q2 or "working" in q1:
        return "Anjali", "managed weekend classes while working full-time"
    if "afford" in q2:
        return "Rohit", "used EMI + scholarship support to start without pressure"
    return "Anjali", "started exactly where you are and still made it work"


def send_stage3_alumni(to, state):
    state["step"] = "WAITING_ALUMNI_CONTINUE"
    USER_STATES[to] = state
    name, story = alumni_name_for(state)
    text = (
        "Totally fair concern. Most working pros worry about this.\n"
        "Before we go on — meet someone who started exactly where you are 👇\n\n"
        f"🎓 *{name}'s Story*\n"
        f"{name} {story}.\n\n"
        f"2,400+ alumni with stories like {name}'s.\n"
        "Ready for question 3?"
    )
    return send_buttons(to, text, [("alumni_continue", "Yes, continue →")])


def send_stage4_university(to, state):
    state["step"] = "WAITING_UNIVERSITY"
    USER_STATES[to] = state
    text = (
        "Question 3 of 4\n\n"
        "Based on your goal + worry, here are 4 universities that fit you well.\n"
        "Each one's strong at something different. Pick the one you'd love to know more about 👇\n\n"
        "1️⃣ Manipal Online MBA — ⭐ 89% placements · ₹1.5L · NIRF #6\n"
        "2️⃣ Amity Online MBA — ⭐ EMI ₹4,500/mo · ₹1.2L · 10+ specs\n"
        "3️⃣ NMIMS Online MBA — ⭐ Top brand recall · ₹2L · Mumbai legacy\n"
        "4️⃣ Jain University MBA — ⭐ Flexible 2-4 yrs · ₹1.4L · Self-paced\n\n"
        "Tap the list below OR reply 1/2/3/4."
    )
    return send_list(to, text, "View 4 universities", "Universities", [
        (uid, u["name"][:24], u["desc"]) for uid, u in UNIVERSITIES.items()
    ])


def send_university_card(to, state):
    uid = state["answers"].get("university_id", "uni_manipal")
    u = UNIVERSITIES[uid]
    alumni, _ = alumni_name_for(state)
    text = (
        f"✨ Great pick! {u['short']} is exactly what {alumni} studied.\n"
        "Here's why it's a strong match for you:\n\n"
        f"🏫 *{u['name']}*\n"
        f"⭐ {u['placement']}\n"
        f"💸 Fees: {u['fees']}\n"
        f"📆 EMI: {u['emi']}\n"
        f"📚 Format: {u['format']}\n"
        f"✅ Accreditation: {u['accreditation']}"
    )
    send_text_message(to, text)
    return send_stage5_summary(to, state)


def send_stage5_summary(to, state):
    state["step"] = "WAITING_SUMMARY_CONTINUE"
    USER_STATES[to] = state
    first_name = state.get("first_name", "Priya")
    q1 = state["answers"].get("life_stage", "working full-time, aiming to grow")
    q2 = state["answers"].get("worry", "time management")
    uid = state["answers"].get("university_id", "uni_manipal")
    u = UNIVERSITIES[uid]
    text = (
        f"Quick recap, {first_name} 📋\n\n"
        f"✓ You're {q1.lower()}\n"
        f"✓ Your worry: {q2.lower()} (totally solvable)\n"
        f"✓ Best match: {u['name']}\n"
        f"⭐ Known for {u['placement']}\n"
        f"📚 {u['format']}\n"
        f"💸 {u['fees']} · EMI from {u['emi']}\n"
        "You've unlocked 🎁\n"
        "• Scholarship up to ₹40,000\n"
        "• No-cost EMI option\n"
        "• Early-bird discount\n"
        "Counsellor will confirm exact eligibility on call 💬\n\n"
        "⚡ Heads up: Premium batches fill fast. Best to lock yours this week."
    )
    return send_buttons(to, text, [("summary_continue", "Schedule call")])


def send_stage6_call(to, state):
    state["step"] = "WAITING_CALL_TIME"
    USER_STATES[to] = state
    text = (
        "Last question — promise!\n\n"
        "When can Counsellor Riya call you?\n"
        "She already has all your context — no need to repeat anything 🙏"
    )
    send_buttons(to, text, [
        ("call_today_6", "📞 Today 6 PM"),
        ("call_tom_11", "📞 Tom 11 AM"),
        ("call_tom_7", "📞 Tom 7 PM"),
    ])
    return send_list(to, "Pick custom time / callback:", "Pick custom time", "Callback options", [
        ("call_tom_morning", "Tomorrow morning", "📅 Tomorrow morning (8-10 AM)"),
        ("call_day_after", "Day after tomorrow", "📅 Day after tomorrow"),
        ("call_weekend", "This weekend", "📅 This weekend"),
        ("call_anytime", "Request callback", "📞 Just request a callback whenever"),
        ("call_exact", "Exact date/time", "📝 Pick exact date/time"),
    ])


def complete_flow(to, state):
    first_name = state.get("first_name", "Priya")
    uid = state["answers"].get("university_id", "uni_manipal")
    u = UNIVERSITIES[uid]
    call_time = state["answers"].get("call_time", "today at 6:00 PM")
    text = (
        f"✅ All set, {first_name}!\n"
        f"Riya will call you {call_time}.\n"
        "She'll know:\n"
        "• Your goal & worry\n"
        f"• Your shortlist ({u['short']})\n"
        "• Your scholarship eligibility\n"
        "No need to start from zero 🙌\n"
        "Talk soon!"
    )
    send_text_message(to, text)
    ans = state.get("answers", {})
    notify_text = (
        "🔔 *MBA Fit Bot Completed*\n"
        f"👤 Chat: {to}\n"
        f"Name: {first_name}\n"
        f"Life stage: {ans.get('life_stage')}\n"
        f"Worry: {ans.get('worry')}\n"
        f"University: {u['name']}\n"
        f"Call time: {call_time}\n"
        f"Completed at: {datetime.now().strftime('%d %b %Y %I:%M %p')}"
    )
    send_text_message(ADMIN_GROUP, notify_text)
    USER_STATES[to] = {**state, "step": "COMPLETED", "completed_at": datetime.now().isoformat()}


def normalize_selection(selection_id):
    if not selection_id:
        return None
    sid = str(selection_id).replace("ButtonsV3:", "")
    return sid.split(":")[-1]


def extract_incoming_text_and_selection(msg):
    body = msg.get("text", {}).get("body", "") or msg.get("body", "") or msg.get("caption", "") or ""
    selection_id = None
    inter = msg.get("interactive", {}) or {}
    if inter:
        selection_id = (
            inter.get("button_reply", {}).get("id")
            or inter.get("list_reply", {}).get("id")
            or inter.get("reply", {}).get("id")
        )
        body = body or inter.get("button_reply", {}).get("title", "") or inter.get("list_reply", {}).get("title", "")
    # Some WHAPI payloads flatten button/list replies differently.
    selection_id = selection_id or msg.get("button", {}).get("id") or msg.get("list_reply", {}).get("id")
    body = body or msg.get("button", {}).get("text", "") or msg.get("list_reply", {}).get("title", "")
    return body, selection_id


def text_choice_to_id(step, body):
    b = (body or "").strip().lower()
    maps = {
        "WAITING_STAGE0": {"1": "start_yes", "yes": "start_yes", "yes, let's do it": "start_yes", "2": "start_later", "maybe later": "start_later", "3": "start_no", "not interested": "start_no"},
        "WAITING_Q1": {"1": "q1_work_grow", "2": "q1_work_switch", "3": "q1_recent_role", "4": "q1_recent_career", "5": "q1_between_jobs", "6": "q1_break", "7": "q1_govt", "8": "q1_exploring"},
        "WAITING_Q2": {"1": "q2_afford", "2": "q2_time", "3": "q2_value", "4": "q2_right_course", "5": "q2_late", "6": "q2_exam", "7": "q2_family", "8": "q2_gap"},
        "WAITING_ALUMNI_CONTINUE": {"1": "alumni_continue", "yes": "alumni_continue", "continue": "alumni_continue"},
        "WAITING_UNIVERSITY": {"1": "uni_manipal", "2": "uni_amity", "3": "uni_nmims", "4": "uni_jain", "manipal": "uni_manipal", "amity": "uni_amity", "nmims": "uni_nmims", "jain": "uni_jain"},
        "WAITING_SUMMARY_CONTINUE": {"1": "summary_continue", "yes": "summary_continue", "schedule": "summary_continue"},
        "WAITING_CALL_TIME": {"1": "call_today_6", "2": "call_tom_11", "3": "call_tom_7", "4": "call_tom_morning", "5": "call_day_after", "6": "call_weekend", "7": "call_anytime", "8": "call_exact"},
    }
    return maps.get(step, {}).get(b)


async def handle_student_churn_flow(sender_id, message_body, selection_id=None):
    state = USER_STATES.get(sender_id)
    body = (message_body or "").strip()
    body_l = body.lower()
    log_event(sender_id, "user", body or f"[selection:{selection_id}]", {"selection_id": selection_id})

    if body_l in ["stop", "stop bot", "bot stop", "pause", "pause bot"]:
        PAUSED_CHATS.add(sender_id)
        USER_STATES[sender_id] = {**(state or {}), "step": "PAUSED", "paused_at": datetime.now().isoformat()}
        send_text_message(sender_id, "🛑 Bot stopped for this chat. I will not continue the flow. Type START BOT or RESUME BOT when you want me to run again.")
        send_text_message(ADMIN_GROUP, f"🛑 MBA Fit Bot stopped in chat: {sender_id}")
        return

    if body_l in ["start bot", "resume bot", "restart bot"]:
        PAUSED_CHATS.discard(sender_id)
        stage0_opening(sender_id, (state or {}).get("first_name", "Priya"), (state or {}).get("university", "Manipal Online"), (state or {}).get("course", "MBA"))
        return

    if sender_id in PAUSED_CHATS or (state and state.get("step") == "PAUSED"):
        # Silent while stopped, except for explicit resume above.
        return

    if body_l in ["hi", "hello", "menu", "reset", "start"] or not state:
        stage0_opening(sender_id)
        return

    sid = normalize_selection(selection_id) or text_choice_to_id(state.get("step"), body)
    step = state.get("step")

    if step == "WAITING_STAGE0":
        if sid == "start_yes":
            send_stage1(sender_id, state)
        elif sid == "start_later":
            state["step"] = "FOLLOWUP_LATER"
            state["followup_at"] = (datetime.now() + timedelta(days=3)).isoformat()
            USER_STATES[sender_id] = state
            send_text_message(sender_id, "No worries 🙂 We'll check back in 3 days. Take your time.")
            send_text_message(ADMIN_GROUP, f"⏳ MBA Fit Bot: {sender_id} selected Maybe later. Follow-up after 3 days.")
        elif sid == "start_no":
            state["step"] = "COLD"
            state["cold_until"] = (datetime.now() + timedelta(days=30)).isoformat()
            USER_STATES[sender_id] = state
            send_text_message(sender_id, "Totally understood 🙂 We won't push. If you ever want clarity on MBA options, just message us here. Wishing you the best!")
            send_text_message(ADMIN_GROUP, f"🧊 MBA Fit Bot: {sender_id} marked cold. Re-engage after 30 days with different angle.")
        else:
            send_text_message(sender_id, "Please tap a button or reply 1 for Yes, 2 for Maybe later, 3 for Not interested.")
        return

    if step == "WAITING_Q1":
        if sid in Q1_OPTIONS:
            state["answers"]["life_stage"] = Q1_OPTIONS[sid]
            send_stage2(sender_id, state)
        else:
            send_text_message(sender_id, "Please choose one option. You can reply 1-8.")
        return

    if step == "WAITING_Q2":
        if sid in Q2_OPTIONS:
            state["answers"]["worry"] = Q2_OPTIONS[sid]
            send_stage3_alumni(sender_id, state)
        else:
            send_text_message(sender_id, "Please choose one concern. You can reply 1-8.")
        return

    if step == "WAITING_ALUMNI_CONTINUE":
        if sid == "alumni_continue":
            send_stage4_university(sender_id, state)
        else:
            send_text_message(sender_id, "Reply 1 or tap Yes, continue →")
        return

    if step == "WAITING_UNIVERSITY":
        if sid in UNIVERSITIES:
            state["answers"]["university_id"] = sid
            state["answers"]["university"] = UNIVERSITIES[sid]["name"]
            USER_STATES[sender_id] = state
            send_university_card(sender_id, state)
        else:
            send_text_message(sender_id, "Please pick one university from the list.")
        return

    if step == "WAITING_SUMMARY_CONTINUE":
        if sid == "summary_continue":
            send_stage6_call(sender_id, state)
        else:
            send_text_message(sender_id, "Tap Schedule call or reply 1.")
        return

    if step == "WAITING_CALL_TIME":
        if sid in CALL_OPTIONS:
            call_time = CALL_OPTIONS[sid]
            if sid == "call_today_6":
                call_time = "today at 6:00 PM"
            elif sid == "call_tom_11":
                call_time = "tomorrow at 11:00 AM"
            elif sid == "call_tom_7":
                call_time = "tomorrow at 7:00 PM"
            state["answers"]["call_time"] = call_time
            complete_flow(sender_id, state)
        else:
            send_text_message(sender_id, "Please pick a callback option or reply 1-8.")
        return

    if step in ["FOLLOWUP_LATER", "COLD", "COMPLETED"]:
        if body_l in ["restart", "start", "menu"]:
            stage0_opening(sender_id, state.get("first_name", "Priya"), state.get("university", "Manipal Online"), state.get("course", "MBA"))
        else:
            send_text_message(sender_id, "Type 'restart' if you want to start the MBA fit flow again.")
        return

    send_text_message(sender_id, "I didn't quite get that. Type 'menu' to restart.")


@app.get("/health")
async def health():
    return {"status": "running", "bot": "degreefyd_mba_fit", "states": len(USER_STATES)}


@app.get("/api/results")
async def results():
    return {"states": USER_STATES, "paused_chats": list(PAUSED_CHATS)}


@app.get("/api/conversation")
async def conversation(chat_id: str = None):
    if chat_id:
        return {"chat_id": chat_id, "events": CONVERSATIONS.get(chat_id, [])}
    return CONVERSATIONS


@app.post("/api/stop")
async def api_stop(data: dict):
    chat_id = data.get("chat_id") or ADMIN_GROUP
    PAUSED_CHATS.add(chat_id)
    USER_STATES[chat_id] = {**USER_STATES.get(chat_id, {}), "step": "PAUSED", "paused_at": datetime.now().isoformat()}
    send_text_message(chat_id, "🛑 Bot stopped. Type START BOT or RESUME BOT when you want it active again.")
    return {"status": "stopped", "chat_id": chat_id}


@app.post("/api/resume")
async def api_resume(data: dict):
    chat_id = data.get("chat_id") or ADMIN_GROUP
    PAUSED_CHATS.discard(chat_id)
    stage0_opening(chat_id, data.get("first_name", "Priya"), data.get("university", "Manipal Online"), data.get("course", "MBA"))
    return {"status": "resumed", "chat_id": chat_id}


@app.post("/api/send_transcript")
async def send_transcript(data: dict):
    chat_id = data.get("chat_id") or ADMIN_GROUP
    events = CONVERSATIONS.get(chat_id, [])
    if not events and os.path.exists(CONVERSATION_LOG_PATH):
        with open(CONVERSATION_LOG_PATH, "r", encoding="utf-8") as f:
            events = [json.loads(line) for line in f if line.strip() and json.loads(line).get("chat_id") == chat_id]
    lines = [f"Conversation transcript for {chat_id}", "=" * 60]
    for e in events:
        who = "BOT" if e.get("direction") == "bot" else "USER"
        lines.append(f"[{e.get('ts')}] {who}: {e.get('text')}")
    if not events:
        lines.append("No conversation events captured yet.")
    text = "\n\n".join(lines)
    out_path = os.path.join(WORKDIR, f"mba_fit_transcript_{chat_id.replace('@','_').replace('/','_')}.txt")
    with open(out_path, "w", encoding="utf-8") as f:
        f.write(text)
    # Send as document using WHAPI data URI.
    import base64
    b64 = base64.b64encode(text.encode("utf-8")).decode("utf-8")
    media = f"data:text/plain;name={os.path.basename(out_path)};base64,{b64}"
    result = send_whapi_message({"to": ADMIN_GROUP, "media": media, "caption": f"Full MBA Fit bot transcript for {chat_id}"}, endpoint="messages/document")
    return {"status": "sent", "path": out_path, "events": len(events), "result": result}


@app.post("/api/preview_full_script")
async def preview_full_script(data: dict):
    chat_id = data.get("chat_id") or ADMIN_GROUP
    full_script = """FULL MBA FIT BOT CONVERSATION PREVIEW

Stage 0:
Hey Priya 👋

I noticed you were exploring Manipal Online MBA with us last week — but the admission isn't locked in yet.
No pressure at all 🙂
If you've got 2 minutes, I'd love to ask you 4 quick questions so we can help you find a college that actually fits your goals.
Buttons: Yes, let's do it / Maybe later / Not interested

Stage 1:
Awesome! 🎯
Question 1 of 4
Where are you in life right now, and why are you thinking about this MBA?
Options: Working — want to grow / Working — want to switch / Recent grad — first big role / Recent grad — building career / Between jobs — comeback time / On a career break / Government job prep / Just exploring options

Stage 2:
Got it — you're aiming to grow in your career. Good context 👍
Question 2 of 4
What's the real worry holding you back?
Options: 💰 Will I afford it? / ⏰ Time alongside work? / 🤔 Will employers value it? / 🧐 Right course? / ⏳ Too late? / 📚 Exam difficulty? / 🏠 Family/personal / 💼 Career break gaps

Stage 3:
Alumni story: Anjali/Aarav/Rohit based on Q1+Q2.
2,400+ alumni with similar stories. Ready for question 3?

Stage 4:
4 universities: Manipal, Amity, NMIMS, Jain with placement/fee/EMI details.

Stage 5:
Personalized recap + scholarship up to ₹40,000 + no-cost EMI + early-bird discount.

Stage 6:
Callback scheduling with Counsellor Riya.
Final: Riya will call with full context. Admin summary is sent.

STOP CONTROL:
Reply STOP / STOP BOT / PAUSE BOT anytime to stop. Reply START BOT / RESUME BOT to restart.
"""
    send_text_message(chat_id, full_script[:4000])
    return {"status": "sent", "chat_id": chat_id}


@app.post("/api/trigger")
async def trigger(data: dict):
    to = data.get("to") or ADMIN_GROUP
    first_name = data.get("first_name", "Priya")
    university = data.get("university", "Manipal Online")
    course = data.get("course", "MBA")
    result = stage0_opening(to, first_name, university, course)
    return {"status": "sent", "to": to, "result": result}


@app.post("/webhook")
async def whapi_webhook(request: Request, background_tasks: BackgroundTasks):
    data = await request.json()
    try:
        with open(os.path.join(WORKDIR, "webhook_debug.log"), "a", encoding="utf-8") as f:
            f.write(json.dumps(data, ensure_ascii=False) + "\n")
    except Exception:
        pass

    for msg in data.get("messages", []):
        if msg.get("from_me"):
            continue
        sender_id = msg.get("chat_id") or msg.get("from")
        body, selection_id = extract_incoming_text_and_selection(msg)
        background_tasks.add_task(handle_student_churn_flow, sender_id, body, selection_id)
    return {"status": "ok"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=5000)
