# Coffee Stress Evaluator - Refactored Architecture

## Overview

This backend is built with FastAPI and acts as the central logic layer of the application. It serves HTML pages, processes login and form submissions, reads survey data from SQLite for dashboard visualizations, and exposes a prediction endpoint that uses a previously trained Random Forest model.

**Technology Stack:**
- FastAPI for REST API framework
- Jinja2 templates for server-rendered pages
- SQLite for lightweight persistence (two databases)
- Joblib + NumPy for machine learning inference
- JWT tokens for authentication
- Bcrypt for password hashing

## Project Structure

```
app/
├── main.py                 # Entry point, router assembly
├── config.py               # Configuration & environment variables
├── requirements.txt        # Python dependencies
├── .env                    # Environment configuration (git-ignored)
├── train_model.py          # Model training script (not part of app)
├── stress_model_rf.joblib  # Trained ML model
├── db/
│   ├── __init__.py
│   ├── connection.py       # Context managers for DB connections
│   ├── users.py           # UserRepository - user CRUD
│   └── predictions.py     # PredictionRepository - prediction CRUD
├── models/
│   ├── __init__.py
│   └── schemas.py         # Pydantic request/response models
├── services/
│   ├── __init__.py
│   ├── auth_service.py    # Authentication & JWT logic
│   ├── ml_service.py      # ML inference & symptom scoring
│   └── dashboard_service.py # Dashboard data aggregation
├── routes/
│   ├── __init__.py
│   ├── auth.py            # /register, /login endpoints
│   ├── pages.py           # HTML page routes (/, /dashboard, /form)
│   ├── prediction.py      # /form, /predict, /my-predictions endpoints
│   └── dashboard.py       # /dashboard-data endpoint (admin only)
├── templates/             # Jinja2 HTML templates
│   ├── base.html
│   ├── login.html
│   ├── dashboard.html
│   └── form.html
└── static/                # CSS, JavaScript
    ├── style.css
    └── form.js
```

## Key Architectural Improvements

### 1. Real Authentication & Password Security
- ✅ Passwords hashed with bcrypt via `passlib`
- ✅ Separate `/register` and `/login` endpoints
- ✅ JWT token-based session management (30 min expiry)
- ✅ HTTPBearer security scheme for protected routes

### 2. Authorization Layer
- ✅ Role-based access control: `user`, `admin`, `analyst`
- ✅ `get_current_user()` dependency extracts JWT
- ✅ `require_role()` factory enforces role checks
- ✅ Dashboard data requires `admin` or `analyst` role
- ✅ Users can only view own predictions

### 3. Database Access Pattern
- ✅ Context managers ensure connection cleanup
- ✅ Try/finally blocks guarantee resource release
- ✅ Repositories encapsulate all DB operations
- ✅ All queries centralized in service/repository layer

### 4. Input Validation
- ✅ Pydantic models enforce all business rules
- ✅ Age: 18–100; coffee cups: 0–20; sleep: 0–24 hours
- ✅ Symptoms constrained to 0–4
- ✅ Enum types for gender, roles, boolean choices
- ✅ FastAPI returns 422 on validation failure

### 5. Configuration Management
- ✅ All hardcoded paths in `config.py`
- ✅ Environment variables via `.env` (python-dotenv)
- ✅ Validation ranges centralized
- ✅ Production-ready: change `.env` without touching code

### 6. Unified Prediction Logic
- ✅ `/form` endpoint: symptom-based scoring
- ✅ `/predict` endpoint: Random Forest ML model
- ✅ Both save to same schema with separate fields
- ✅ Clear separation: rule-based vs. learned models

## Running the Application

### Prerequisites
```bash
pip install -r requirements.txt
```

### Environment Setup
Copy and edit `.env` with your configuration:
```bash
SECRET_KEY=your-secret-key
COFFEE_DB_PATH=path/to/coffee_data.db
STRES_DB_PATH=stres.db
MODEL_PATH=stress_model_rf.joblib
```

### Start the Server
```bash
python main.py
```

Or directly with Uvicorn:
```bash
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

## API Endpoints

### Authentication
```
POST /register       - Register new user
POST /login         - Authenticate and get JWT token
```

### Pages
```
GET  /               - Login page
GET  /dashboard      - Dashboard page
GET  /form           - Form/prediction page
```

### Predictions (require auth)
```
POST /form          - Submit form with symptoms → risk score
POST /predict       - ML prediction from health metrics
GET  /my-predictions - User's prediction history
```

### Dashboard (admin/analyst only)
```
GET  /dashboard-data - Aggregated data for 8 charts
```

## Database Schema

### `user` table
```sql
id, username (unique), password_hash, role (user|admin|analyst), created_at
```

### `prediction` table
```sql
id, user_id (FK), varsta, cesti_cafea_zi, ore_somn, nivel_stres,
predictie_stres, symptom_score, created_at
```

## Security Notes

- Plaintext passwords are never stored
- Tokens expire after 30 minutes (configurable)
- JWT payload includes `sub` (user_id) and `role`
- All sensitive operations check role before executing
- Database connections clean up automatically

## Testing Authentication

### Register
```bash
curl -X POST http://localhost:8000/register \
  -H "Content-Type: application/json" \
  -d '{"username":"john","password":"password123"}'
```

### Login
```bash
curl -X POST http://localhost:8000/login \
  -H "Content-Type: application/json" \
  -d '{"username":"john","password":"password123"}'
```

### Protected Endpoint (include token)
```bash
curl -X GET http://localhost:8000/my-predictions \
  -H "Authorization: Bearer YOUR_TOKEN_HERE"
```

## Future Improvements

1. Migrate from SQLite to PostgreSQL for multi-user scale
2. Add refresh token mechanism
3. Implement rate limiting and CORS policies
4. Add detailed logging and monitoring
5. Separate read-only analytics database
6. API documentation with interactive Swagger UI (auto-generated at `/docs`)

## Migration from Old api.py

The old `api.py` is no longer used. All functionality has been distributed across:
- Routes layer: HTTP handling
- Services layer: Business logic
- DB layer: Data access
- Models layer: Validation

To fully transition, update frontend JavaScript to send JWT tokens in headers after login.
