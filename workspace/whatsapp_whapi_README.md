# Degreefyd WhatsApp WHAPI Bot Package

This package contains the WhatsApp/WHAPI code needed to run locally or on VPS without depending on Hermes WhatsApp bridge.

## Files
- student_churn_bot.py: FastAPI webhook/state-machine bot.
- trigger_churn_hook.py: outbound trigger script for MBA/churn flow.
- whapi_local_sender.py: standalone WhatsApp text/file/image sender via WHAPI.
- send_pdf_whapi.py / send_report_whapi.py: report/file sender helpers if present.
- start_tunnel.js: localtunnel helper for temporary local testing only.
- package.json / package-lock.json: Node localtunnel dependency metadata.
- .env.example: environment template. Put real secrets into `.env` locally.

## Install Python deps
```bash
cd /path/to/this/folder
uv run --with fastapi --with requests --with python-dotenv --with uvicorn python student_churn_bot.py
```

Or install normally:
```bash
python3 -m pip install fastapi uvicorn requests python-dotenv
python3 student_churn_bot.py
```

## Send WhatsApp directly without Hermes
```bash
python3 whapi_local_sender.py text "Test message"
python3 whapi_local_sender.py file /absolute/path/report.pdf "Report caption"
python3 whapi_local_sender.py image /absolute/path/chart.png "Chart caption"
```

## Local webhook testing only
```bash
uv run --with fastapi --with requests --with python-dotenv --with uvicorn python student_churn_bot.py
npx --yes localtunnel --port 5000 --print-requests
```
Then set WHAPI webhook to:
`https://YOUR-TUNNEL-URL/webhook`

## Production recommendation
Run `student_churn_bot.py` on VPS with a fixed domain and systemd/Docker. Do not use localtunnel for production.
