import os
import json
import asyncio
import requests
import asyncpg
from fastapi import FastAPI, Request, BackgroundTasks
from dotenv import load_dotenv

load_dotenv('/workspace/.env')

# --- CONFIG ---
WHAPI_TOKEN = os.getenv("WHAPI_TOKEN")
WHAPI_URL = "https://gate.whapi.cloud"
DB_HOST = os.getenv("REGULAR_LMS_DB_HOST")
DB_PORT = os.getenv("REGULAR_LMS_DB_PORT", "54321")
DB_NAME = os.getenv("REGULAR_LMS_DB_NAME")
DB_USER = os.getenv("REGULAR_LMS_DB_USER")
DB_PASS = os.getenv("REGULAR_LMS_DB_PASSWORD")

app = FastAPI()

# In-memory state tracking (for production, use Redis or SQLite)
USER_STATES = {}

# --- DB HELPERS ---
async def get_db_conn():
    return await asyncpg.connect(
        host=DB_HOST,
        port=int(DB_PORT),
        database=DB_NAME,
        user=DB_USER,
        password=DB_PASS
    )

# --- WHAPI HELPERS ---
def send_whapi_message(payload, endpoint="messages/interactive"):
    headers = {
        "accept": "application/json",
        "content-type": "application/json",
        "authorization": f"Bearer {WHAPI_TOKEN}"
    }
    url = f"{WHAPI_URL}/{endpoint}"
    response = requests.post(url, json=payload, headers=headers)
    return response.json()

def send_text_message(to, text):
    payload = {"to": to, "body": text}
    return send_whapi_message(payload, endpoint="messages/text")

# --- FLOW LOGIC ---
async def handle_whatsapp_flow(sender_id, message_body, selection_id=None):
    state = USER_STATES.get(sender_id, {"step": "START"})
    
    conn = await get_db_conn()
    
    try:
        # CHURN RESPONSE (Independent of state)
        if selection_id and selection_id.startswith("churn_"):
            parts = selection_id.split("_")
            action = parts[1]
            student_id = parts[2]
            
            # Using the connection already opened at the start of handle_whatsapp_flow
            if action == "yes":
                await conn.execute("UPDATE latest_course_statuses SET latest_course_status = 'Re-engaged' WHERE student_id = $1", int(student_id))
                await conn.execute("INSERT INTO student_remarks (student_id, remark, created_by) VALUES ($1, $2, $3)", 
                                   int(student_id), "Student requested callback via WhatsApp Churn Bot", 999)
                send_text_message(sender_id, "✅ Great! A counselor will call you shortly to discuss your admission.")
            
            elif action == "chat":
                send_text_message(sender_id, "One of our experts will join this chat in a moment. How can we help you today?")
            
            elif action == "no":
                await conn.execute("UPDATE latest_course_statuses SET latest_course_status = 'Permanently Not Interested' WHERE student_id = $1", int(student_id))
                send_text_message(sender_id, "Understood. We've updated your preference. Feel free to reach out if you change your mind!")
            return

        # STEP 0: START -> SHOW SUPERVISORS
        if state["step"] == "START" or message_body.lower() in ["hi", "hello", "menu", "reset"]:
            USER_STATES[sender_id] = {"step": "SELECT_SUPERVISOR"}
            
            # Fetch supervisors from DB
            sups = await conn.fetch("SELECT supervisor_id, supervisor_name FROM supervisors WHERE status = 'active' LIMIT 10")
            
            rows = [{"id": f"sup_{s['supervisor_id']}", "title": s['supervisor_name']} for s in sups]
            
            payload = {
                "to": sender_id,
                "type": "list",
                "body": {"text": "👋 *Degreefyd Sequential Bot*\n\nPlease select a *Supervisor* to see their counselors:"},
                "action": {
                    "button": "Select Supervisor",
                    "sections": [{"title": "Supervisors", "rows": rows}]
                }
            }
            send_whapi_message(payload)

        # STEP 1: SUPERVISOR SELECTED -> SHOW COUNSELORS
        elif state["step"] == "SELECT_SUPERVISOR" and selection_id and selection_id.startswith("sup_"):
            sup_id = int(selection_id.split("_")[1])
            USER_STATES[sender_id] = {"step": "SELECT_COUNSELLOR", "supervisor_id": sup_id}
            
            # Fetch counselors for this supervisor
            couns = await conn.fetch("SELECT counsellor_id, counsellor_name FROM counsellors WHERE assigned_to = $1 AND status = 'active' LIMIT 10", sup_id)
            
            if not couns:
                send_text_message(sender_id, "No active counselors found for this supervisor. Type 'menu' to restart.")
                USER_STATES[sender_id] = {"step": "START"}
                return

            rows = [{"id": f"coun_{c['counsellor_id']}", "title": c['counsellor_name']} for c in couns]
            
            payload = {
                "to": sender_id,
                "type": "list",
                "body": {"text": f"Found {len(couns)} counselors. Select one to see options:"},
                "action": {
                    "button": "Select Counselor",
                    "sections": [{"title": "Counselors", "rows": rows}]
                }
            }
            send_whapi_message(payload)

        # STEP 2: COUNSELOR SELECTED -> SHOW ACTIONS
        elif state["step"] == "SELECT_COUNSELLOR" and selection_id and selection_id.startswith("coun_"):
            coun_id = int(selection_id.split("_")[1])
            USER_STATES[sender_id] = {"step": "SELECT_ACTION", "counsellor_id": coun_id}
            
            payload = {
                "to": sender_id,
                "type": "button",
                "body": {"text": "What would you like to do for this counselor?"},
                "action": {
                    "buttons": [
                        {"type": "quick_reply", "title": "📈 View Stats", "id": "act_stats"},
                        {"type": "quick_reply", "title": "📝 Add Remark", "id": "act_remark"},
                        {"type": "quick_reply", "title": "🔄 Reset", "id": "act_reset"}
                    ]
                }
            }
            send_whapi_message(payload)

        # STEP 3: ACTION SELECTED
        elif state["step"] == "SELECT_ACTION" and selection_id and selection_id.startswith("act_"):
            action = selection_id.split("_")[1]
            
            if action == "stats":
                coun_id = state["counsellor_id"]
                # Fetch some real stats from DB
                lead_count = await conn.fetchval("SELECT count(*) FROM students WHERE assigned_to = $1", str(coun_id))
                send_text_message(sender_id, f"📊 *Counselor Stats*\n\nTotal Leads Assigned: {lead_count}\n\nType 'menu' to go back.")
                USER_STATES[sender_id] = {"step": "START"}
            
            elif action == "remark":
                send_text_message(sender_id, "Please type the remark you want to add for this counselor:")
                USER_STATES[sender_id]["step"] = "WAITING_REMARK"
                
            else:
                send_text_message(sender_id, "Resetting flow...")
                USER_STATES[sender_id] = {"step": "START"}
                await handle_whatsapp_flow(sender_id, "menu")

        # STEP 4: REMARK RECEIVED
        elif state["step"] == "WAITING_REMARK":
            coun_id = state["counsellor_id"]
            # Here we "hit the info to db"
            await conn.execute("INSERT INTO user_action_logs (user_id, action, details) VALUES ($1, $2, $3)", 
                               999, 'WHATSAPP_REMARK', f"Counsellor ID {coun_id}: {message_body}")
            
            send_text_message(sender_id, f"✅ Remark saved successfully!\n\nDetails: {message_body}\n\nType 'menu' to start over.")
            USER_STATES[sender_id] = {"step": "START"}

        else:
            send_text_message(sender_id, "I didn't quite get that. Type 'menu' to see the options.")
            
    finally:
        await conn.close()

# --- ENDPOINTS ---
@app.post("/webhook")
async def whapi_webhook(request: Request, background_tasks: BackgroundTasks):
    data = await request.json()
    
    # WHAPI Webhook structure check
    messages = data.get("messages", [])
    for msg in messages:
        if msg.get("from_me"): continue
        
        sender_id = msg.get("from")
        message_body = msg.get("text", {}).get("body", "")
        
        # Check for interactive responses
        selection_id = None
        if msg.get("type") == "interactive":
            interactive = msg.get("interactive", {})
            if "button_reply" in interactive:
                selection_id = interactive["button_reply"].get("id")
            elif "list_reply" in interactive:
                selection_id = interactive["list_reply"].get("id")
        
        # Handle the flow in background to respond fast to webhook
        background_tasks.add_task(handle_whatsapp_flow, sender_id, message_body, selection_id)
        
    return {"status": "ok"}

@app.get("/health")
def health():
    return {"status": "running"}

@app.post("/api/update")
async def update_info(data: dict):
    # Example external API to hit the DB
    target_id = data.get("target_id")
    action = data.get("action")
    details = data.get("details")
    
    conn = await get_db_conn()
    try:
        await conn.execute("INSERT INTO user_action_logs (user_id, action, details) VALUES ($1, $2, $3)", 
                           target_id, action, details)
        return {"status": "success", "message": "Info logged to DB"}
    finally:
        await conn.close()

if __name__ == "__main__":
    import uvicorn
    # Use 0.0.0.0 to be accessible if the user sets up a tunnel
    uvicorn.run(app, host="0.0.0.0", port=5000)
