# Local Development (SAM + DynamoDB Local)

Quick steps to run a local stack with DynamoDB Local and SAM (Windows PowerShell):

1. Start DynamoDB Local and seed sample data:
   powershell -NoProfile -ExecutionPolicy Bypass -File .\dev\run-sam-local.ps1

   This will:
   - start DynamoDB Local via docker-compose
   - seed `dairy-shifts-local` with sample employees, tasks, and shifts
   - start `sam local start-api` with environment variables from `dev/env.json`

2. Serve the frontend:
   cd src
   python -m http.server 8000
   Open http://localhost:8000/shifts.html

Notes:
- Make sure Docker Desktop and AWS SAM CLI are installed.
- `dev/env.json` sets env vars for common functions; adjust logical function names if your SAM template uses different names.
