# Migration Guide from Old api.py to New Architecture

## Summary of Changes

The old `api.py` file has been split into multiple focused modules following a layered architecture.

## File Mapping

| Old `api.py` | New Location | Purpose |
|---|---|---|
| Hardcoded paths | `config.py` | Centralized configuration |
| `get_coffee_conn()` | `db/connection.py` | Context manager pattern |
| `get_stres_conn()` | `db/connection.py` | Context manager pattern |
| `@app.post("/login")` | `routes/auth.py` | Authentication endpoint |
| `UserRepository` logic | `db/users.py` | User CRUD operations |
| Password hashing logic | `services/auth_service.py` | JWT & password security |
| `@app.get("/form")` | `routes/pages.py` | HTML form page |
| `@app.post("/form")` | `routes/prediction.py` | Form submission |
| Symptom scoring | `services/ml_service.py` | Rule-based scoring |
| `@app.post("/predict")` | `routes/prediction.py` | ML prediction |
| Prediction saving | `db/predictions.py` | Prediction CRUD |
| `@app.get("/dashboard_data")` | `routes/dashboard.py` | Dashboard aggregation |
| Dashboard logic | `services/dashboard_service.py` | Data aggregation |

## What Changed in Old Endpoints

### Old POST /login
```python
# OLD: No token, plain-text passwords, creates session redirect
@app.post("/login")
async def login(username: str = Form(...), password: str = Form(...)):
    # Stores plain-text password
    # Returns RedirectResponse to /dashboard
    pass
```

### New POST /login
```python
# NEW: JWT token, hashed passwords, returns token
@app.post("/login")
async def login(req: LoginRequest):
    # Verifies hashed password
    # Returns JWT token in JSON response
    return TokenResponse(access_token=token, ...)
```

### New POST /register (new endpoint)
```python
# Allows users to create accounts
# Hashes password on creation
# Returns JWT token
```

### Old GET /dashboard
```python
# OLD: No authentication required
@app.get("/dashboard")
async def dashboard_page(request: Request):
    return templates.TemplateResponse("dashboard.html", ...)
```

### New GET /dashboard
```python
# NEW: Still serves page (no auth required on route)
# But frontend must include JWT token for /dashboard-data API calls
@app.get("/dashboard")
async def dashboard_page(request: Request):
    return templates.TemplateResponse("dashboard.html", ...)
```

### Old GET /dashboard_data
```python
# OLD: No authentication, returns data to anyone
@app.get("/dashboard_data")
def dashboard_data(sex: Optional[str] = None, ...):
    return {...}
```

### New GET /dashboard-data
```python
# NEW: Requires admin or analyst role
@app.get("/dashboard-data")
async def dashboard_data(..., current_user: dict = Depends(require_role("admin", "analyst"))):
    return {...}
```

### Old POST /form (HTML form submission)
```python
# OLD: Returns HTML with embedded results
# No user tracking
@app.post("/form", response_class=HTMLResponse)
async def form_submit(request: Request, ...):
    return templates.TemplateResponse("form.html", {"score": score, ...})
```

### New POST /form (JSON API)
```python
# NEW: Requires authentication
# Returns JSON with score and submission ID
# Saves submission to database
@app.post("/form")
async def submit_form(req: FormSubmissionRequest, current_user: dict = Depends(get_current_user)):
    return FormSubmissionResponse(score=score, message=msg, submission_id=id)
```

## Frontend Integration Changes

### Before: HTML Form Submission
```html
<form method="POST" action="/form">
    <input name="coffee_cups" type="number">
    <!-- form fields -->
    <button type="submit">Submit</button>
</form>
```

### After: API Call with JWT Token
```javascript
// 1. User logs in
const loginResp = await fetch('/login', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ username, password })
});
const { access_token, token_type } = await loginResp.json();

// 2. Store token (localStorage or sessionStorage)
sessionStorage.setItem('token', access_token);

// 3. Use token in subsequent requests
const formResp = await fetch('/form', {
    method: 'POST',
    headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${access_token}`
    },
    body: JSON.stringify({ coffee_cups: 2, ... })
});
const { score, message, submission_id } = await formResp.json();
```

### Dashboard Data Access
```javascript
// OLD: No auth needed
const data = await fetch('/dashboard_data?sex=M');

// NEW: Must include JWT token
const data = await fetch('/dashboard-data?sex=M', {
    headers: {
        'Authorization': `Bearer ${token}`
    }
});
```

## Database Changes

### Old Prediction Table
```sql
CREATE TABLE prediction (
    id INTEGER PRIMARY KEY,
    varsta INTEGER,
    cesti_cafea_zi INTEGER,
    ore_somn REAL,
    nivel_stres INTEGER,
    predictie REAL
);
```

### New Prediction Table
```sql
CREATE TABLE prediction (
    id INTEGER PRIMARY KEY,
    user_id INTEGER,              -- NEW: Track who made prediction
    varsta INTEGER,
    cesti_cafea_zi INTEGER,
    ore_somn REAL,
    nivel_stres INTEGER,
    predictie_stres REAL,         -- RENAMED: more explicit
    symptom_score REAL,           -- NEW: separate from ML prediction
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,  -- NEW: audit trail
    FOREIGN KEY (user_id) REFERENCES user(id)
);
```

### Old User Table
```sql
CREATE TABLE user (
    id INTEGER PRIMARY KEY,
    username TEXT UNIQUE,
    password TEXT                 -- INSECURE: plain text
);
```

### New User Table
```sql
CREATE TABLE user (
    id INTEGER PRIMARY KEY,
    username TEXT UNIQUE NOT NULL,
    password_hash TEXT NOT NULL,  -- SECURE: bcrypt hash
    role TEXT DEFAULT 'user',     -- NEW: role-based access
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP  -- NEW: audit
);
```

## Validation Changes

### Old Validation (minimal)
```python
@app.post("/form")
async def form_submit(
    coffee_cups: int = Form(...),  # No range checks
    age: int = Form(...),          # No range checks
    ...
):
    pass
```

### New Validation (comprehensive)
```python
class FormSubmissionRequest(BaseModel):
    coffee_cups: int = Field(..., ge=0, le=20)      # Range enforced
    age: int = Field(..., ge=18, le=100)            # Range enforced
    sleep_hours: float = Field(..., ge=0, le=24)    # Range enforced
    symptoms_*: int = Field(..., ge=0, le=4)        # Symptom range
    gender: Gender                                   # Enum validation
    smoker: BooleanChoice                           # Enum validation
    ...
```

## Error Handling

### Old Error Handling
```python
# Minimal error handling
if not user:
    return templates.TemplateResponse("login.html", {"error": "..."})

# Silent catches
try:
    age_int = int(age_val)
except Exception:
    continue
```

### New Error Handling
```python
# HTTP status codes
if not user:
    raise HTTPException(status_code=401, detail="Invalid username or password")

# Structured errors
if current_user["role"] not in allowed_roles:
    raise HTTPException(status_code=403, detail="Insufficient permissions")

# Pydantic validation (automatic 422)
# Invalid input → FastAPI returns 422 Unprocessable Entity
```

## Configuration

### Old: Hardcoded
```python
COFFEE_DB = "C:/Users/tatia/Desktop/Anul 3/Teza de licenta/coffee-risk-evaluator/coffee_data.db"
STRES_DB = os.path.join(BASE_DIR, "stres.db")
```

### New: Environment-based
```python
# config.py
COFFEE_DB = os.getenv("COFFEE_DB_PATH", "C:/Users/tatia/...")
STRES_DB = os.getenv("STRES_DB_PATH", "stres.db")

# .env file
COFFEE_DB_PATH=C:/Users/tatia/...
STRES_DB_PATH=stres.db
```

## Running the New Application

### Install Dependencies
```bash
pip install -r requirements.txt
```

### Configure Environment
```bash
# Copy and edit .env
cp .env.example .env
# Edit SECRET_KEY and database paths
```

### Start Server
```bash
python main.py
# OR
uvicorn main:app --reload --port 8000
```

### Documentation
- Interactive API docs: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

## Backward Compatibility Notes

- **Old api.py** is replaced; keep it as reference only
- **Frontend must be updated** to send JWT tokens in Authorization headers
- **HTML form submissions** must change to AJAX/fetch with JSON
- **Session management** changes from redirects to token storage
- **Dashboard data** now requires authentication

## Breaking Changes for Frontend

1. Login now returns JSON with token, not redirect
2. Form submission returns JSON, not HTML with embedded results
3. Dashboard data endpoint is now `/dashboard-data` (was `/dashboard_data`)
4. All API calls (except public pages) require `Authorization: Bearer <token>` header
5. Token must be stored in client (localStorage/sessionStorage)
6. Token refresh needed after 30 minutes

## Rollback Plan

If needed, the old `api.py` can be restored from git or backup. However, features will revert to:
- Plain-text password storage
- No authentication on dashboard
- No user tracking on predictions
- Less structured error handling
