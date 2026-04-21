# Quick Start Guide

## 1. Environment Setup

### Install Python (3.9+)
```bash
python --version  # Should be 3.9 or higher
```

### Clone/Enter Project
```bash
cd "c:\Users\tatia\Desktop\Anul 3\Teza de licenta\Teza"
```

### Create Virtual Environment
```bash
python -m venv venv
venv\Scripts\activate  # On Windows
# or: source venv/bin/activate  # On macOS/Linux
```

### Install Dependencies
```bash
pip install -r requirements.txt
```

## 2. Configuration

### Edit `.env` File
Create/edit `.env` in the project root:
```
SECRET_KEY=your-secret-key-change-this-in-production
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30
COFFEE_DB_PATH=C:/Users/tatia/Desktop/Anul 3/Teza de licenta/coffee-risk-evaluator/coffee_data.db
STRES_DB_PATH=stres.db
MODEL_PATH=stress_model_rf.joblib
```

⚠️ **Important**: Change `SECRET_KEY` to a strong random string in production!

## 3. Start the Application

### Option A: Direct Python
```bash
python main.py
```

### Option B: Uvicorn (with auto-reload)
```bash
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

### Verify It's Running
Open browser: http://localhost:8000
- You should see the login page
- Interactive docs at http://localhost:8000/docs
- ReDoc at http://localhost:8000/redoc

## 4. Testing the API

### Test Login/Register
```bash
# Register new user
curl -X POST http://localhost:8000/register \
  -H "Content-Type: application/json" \
  -d '{"username":"testuser","password":"password123"}'

# Response:
# {
#   "access_token": "eyJhbGciOiJIUzI1NiIs...",
#   "token_type": "bearer",
#   "user_id": 1,
#   "role": "user"
# }
```

### Test Protected Endpoints
```bash
# Save token from login/register
TOKEN="your_token_here"

# Get user's predictions
curl -X GET http://localhost:8000/my-predictions \
  -H "Authorization: Bearer $TOKEN"
```

### Test Dashboard (Admin Only)
```bash
# First, manually set role to "admin" in database OR
# Create admin user with register, then update DB

curl -X GET "http://localhost:8000/dashboard-data?sex=M" \
  -H "Authorization: Bearer $ADMIN_TOKEN"
```

## 5. Database Management

### View Database Files
- `stres.db` - Contains users and predictions (auto-created)
- Coffee data DB path configurable in `.env`

### Reset Database
```bash
# Delete stres.db to reset (will be recreated on startup)
rm stres.db
```

### Make User an Admin
Use SQLite CLI:
```bash
sqlite3 stres.db
UPDATE user SET role='admin' WHERE username='youruser';
.quit
```

## 6. Frontend Integration

### Step 1: Update Login Form
Change from HTML form submission to AJAX:

```javascript
// OLD: <form method="POST" action="/login">
// NEW: JavaScript API call

const loginBtn = document.getElementById('loginBtn');
const usernameInput = document.getElementById('username');
const passwordInput = document.getElementById('password');

loginBtn.addEventListener('click', async (e) => {
    e.preventDefault();
    
    const resp = await fetch('/login', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
            username: usernameInput.value,
            password: passwordInput.value
        })
    });
    
    if (resp.ok) {
        const data = await resp.json();
        // Store token
        sessionStorage.setItem('token', data.access_token);
        window.location.href = '/dashboard';
    } else {
        alert('Login failed');
    }
});
```

### Step 2: Add Token to All API Calls
```javascript
// Helper function
async function apiCall(endpoint, method = 'GET', body = null) {
    const token = sessionStorage.getItem('token');
    
    const options = {
        method,
        headers: {
            'Content-Type': 'application/json',
            'Authorization': `Bearer ${token}`
        }
    };
    
    if (body) options.body = JSON.stringify(body);
    
    return fetch(endpoint, options);
}

// Usage
const predictions = await apiCall('/my-predictions');
const data = await predictions.json();
```

### Step 3: Update Form Submission
```javascript
// OLD: Form submits to /form with HTML response
// NEW: JavaScript API call

const submitBtn = document.getElementById('submitForm');

submitBtn.addEventListener('click', async (e) => {
    e.preventDefault();
    
    const formData = {
        coffee_cups: parseInt(document.getElementById('coffeeCups').value),
        caffeine_mg: parseInt(document.getElementById('caffeineMg').value),
        sleep_hours: parseFloat(document.getElementById('sleepHours').value),
        activity_hours: parseFloat(document.getElementById('activityHours').value),
        age: parseInt(document.getElementById('age').value),
        gender: document.getElementById('gender').value,
        smoker: document.getElementById('smoker').value,
        alcohol: document.getElementById('alcohol').value,
        symptoms_palpitations_tremor: parseInt(document.getElementById('symptom1').value),
        symptoms_insomnia: parseInt(document.getElementById('symptom2').value),
        symptoms_agitation: parseInt(document.getElementById('symptom3').value),
        symptoms_concentration: parseInt(document.getElementById('symptom4').value),
        symptoms_headache: parseInt(document.getElementById('symptom5').value),
        symptoms_digestive: parseInt(document.getElementById('symptom6').value)
    };
    
    const resp = await apiCall('/form', 'POST', formData);
    const result = await resp.json();
    
    // Display results
    document.getElementById('score').textContent = (result.score * 100).toFixed(1) + '%';
    document.getElementById('message').textContent = result.message;
    document.getElementById('results').style.display = 'block';
});
```

### Step 4: Update Dashboard Data Fetching
```javascript
// OLD: No authentication
// const data = await fetch('/dashboard_data?sex=M');

// NEW: Include JWT token
async function loadDashboardData(filters = {}) {
    const token = sessionStorage.getItem('token');
    
    const params = new URLSearchParams(filters);
    const resp = await fetch(`/dashboard-data?${params}`, {
        headers: { 'Authorization': `Bearer ${token}` }
    });
    
    if (resp.status === 403) {
        alert('You need admin/analyst role to view dashboard');
        return null;
    }
    
    return resp.json();
}
```

## 7. Troubleshooting

### ModuleNotFoundError
```bash
# Make sure venv is activated
# And all dependencies installed
pip install -r requirements.txt
```

### Port Already in Use
```bash
# Windows
netstat -ano | findstr :8000
taskkill /PID <PID> /F

# macOS/Linux
lsof -i :8000
kill -9 <PID>
```

### Database Locked Error
```bash
# Close any other connections to stres.db
# This typically happens if previous instance didn't close cleanly
rm stres.db  # Will be recreated on startup
```

### JWT Token Expired
- After 30 minutes, user needs to login again
- Token expiry configurable in `.env` (ACCESS_TOKEN_EXPIRE_MINUTES)
- Consider implementing refresh tokens for production

### "Invalid token" Error
- Check token is included in Authorization header
- Format must be: `Authorization: Bearer YOUR_TOKEN`
- Not `Authorization: YOUR_TOKEN` (missing "Bearer")

## 8. Production Deployment

### Security Checklist Before Deploy

- [ ] Change SECRET_KEY to strong random value
- [ ] Change database paths to production locations
- [ ] Use HTTPS (not HTTP)
- [ ] Enable CORS with proper allowed origins
- [ ] Set up database backups
- [ ] Use strong password requirements
- [ ] Enable logging and monitoring
- [ ] Set up error tracking (Sentry, etc.)
- [ ] Use environment-specific configs
- [ ] Disable debug mode

### Example Production .env
```
SECRET_KEY=<generate-with-secrets-module>
DEBUG=false
ALLOWED_ORIGINS=https://yourdomain.com
DATABASE_URL=postgresql://user:pass@prod-db:5432/mydb
```

## 9. Common Tasks

### Backup Database
```bash
cp stres.db stres_backup_$(date +%Y%m%d_%H%M%S).db
```

### View All Users
```bash
sqlite3 stres.db "SELECT id, username, role FROM user;"
```

### View Predictions for User
```bash
sqlite3 stres.db "SELECT * FROM prediction WHERE user_id = 1;"
```

### Create Admin User
```bash
sqlite3 stres.db "UPDATE user SET role = 'admin' WHERE id = 1;"
```

## 10. Next Steps

1. ✅ Start server
2. ✅ Test API endpoints at `/docs`
3. ✅ Update frontend JavaScript
4. ✅ Test login/form submission
5. ✅ Configure production settings
6. ✅ Deploy to server
