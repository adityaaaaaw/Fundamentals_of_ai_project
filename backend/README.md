# AI Study Planner Agent — Backend Service

A FastAPI backend with SQLite, SQLAlchemy 2.x, Alembic, and Google Gemini AI integration.

---

## 🛠️ Tech Stack

- **Python 3.11+**
- **FastAPI**: Modern, asynchronous REST API framework
- **SQLAlchemy 2.x**: Object-relational mapping
- **SQLite**: Local relational database with foreign key support
- **Alembic**: Database migrations
- **Google Gen AI SDK (`google-genai`)**: Official Gemini API integration
- **Pydantic v2**: Strict request and response data validation
- **Pytest & HTTPX**: Automated test suite

---

## 🚀 Local Setup & Running

### 1. Create Virtual Environment
```bash
cd backend
python -m venv .venv
```

**Windows (PowerShell):**
```powershell
.\.venv\Scripts\activate
```

**macOS / Linux:**
```bash
source .venv/bin/activate
```

### 2. Install Dependencies
```bash
pip install -r requirements.txt
```

### 3. Configure Environment Variables
Copy `.env.example` to `.env`:
```bash
cp .env.example .env
```

Edit `backend/.env`:
```env
APP_NAME=AI Study Planner Agent
ENVIRONMENT=development
DATABASE_URL=sqlite:///./study_planner.db
GEMINI_API_KEY=your_gemini_api_key_here
GEMINI_MODEL=gemini-2.5-flash
FRONTEND_ORIGINS=http://localhost:5173
DEMO_USER_ID=demo-user-id
```

### 4. Run Alembic Database Migrations
```bash
alembic upgrade head
```

### 5. Start the FastAPI Server
```bash
uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

- API Base URL: `http://localhost:8000/api/v1`
- Interactive Swagger UI: `http://localhost:8000/docs`
- Interactive ReDoc: `http://localhost:8000/redoc`
- Health Endpoint: `http://localhost:8000/health`

### 6. Run Automated Tests
```bash
pytest -v
```

---

## 📡 API Endpoints

### Health
- `GET /health` — Check server and database health

### Tasks (`/api/v1/tasks`)
- `GET /` — List tasks with filters (`status`, `priority`, `subject`, `due_date`, `search`)
- `POST /` — Create a new coursework task
- `GET /{id}` — Get single task
- `PUT /{id}` — Update task
- `PATCH /{id}/status` — Update task status (`pending`, `in_progress`, `completed`, `missed`)
- `DELETE /{id}` — Delete task

### Study Sessions (`/api/v1/sessions`)
- `GET /` — List sessions with filters (`date`, `day_of_week`, `status`)
- `POST /` — Schedule session (**rejects overlapping sessions with 409 Conflict**)
- `GET /{id}` — Get single session
- `PUT /{id}` — Update session (prevents self-conflict)
- `PATCH /{id}/status` — Change status (`upcoming`, `completed`, `missed`)
- `DELETE /{id}` — Delete session

### Exams (`/api/v1/exams`)
- `GET /` — List exams sorted by date with calculated `days_remaining`
- `POST /` — Schedule an exam
- `GET /{id}` — Get single exam
- `PUT /{id}` — Update exam
- `DELETE /{id}` — Delete exam

### Dashboard (`/api/v1/dashboard`)
- `GET /summary` — Real-time task counts, completion rate, planned vs completed time, streak
- `GET /weekly-progress` — Daily studied hours vs daily targets
- `GET /today-sessions` — Scheduled study sessions for today
- `GET /upcoming-exams` — Milestone exams with countdown badges
- `GET /high-priority-tasks` — Immediate pending tasks

### Gemini AI (`/api/v1/ai`)
- `POST /generate-plan` — Generate structured JSON study blocks tailored to goals & syllabus
- `POST /ask` — AI academic advisor Q&A grounded in student coursework data
- `POST /optimize-schedule` — Suggest non-overlapping study blocks avoiding existing commitments
