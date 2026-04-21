# Frontend Integration Checklist

## Overview
The backend API has been refactored with new authentication and authorization. Frontend needs updates to handle JWT tokens instead of form submissions and redirects.

## Files to Update

- [ ] `templates/login.html` - Update form submission
- [ ] `templates/form.html` - Update form submission and add token handling
- [ ] `templates/dashboard.html` - Update data fetching with token
- [ ] `static/form.js` - Add API call logic and token management
- [ ] `static/style.css` - Optional: add styles for loading states

## Detailed Changes

### 1. Login Page (login.html)

**Status**: 🔴 NEEDS UPDATE

**What to Change**:
- [x] Replace HTML form submission with JavaScript API call
- [x] Store JWT token on successful login
- [x] Add error handling for failed login
- [x] Add register link/button

**Before** (HTML form):
```html
<form method="POST" action="/login">
    <input name="username" type="text" required>
    <input name="password" type="password" required>
    <button type="submit">Login</button>
</form>
```

**After** (JavaScript API):
```html
<form id="loginForm">
    <input id="username" type="text" required placeholder="Username">
    <input id="password" type="password" required placeholder="Password">
    <button type="button" onclick="handleLogin()">Login</button>
    <button type="button" onclick="handleRegister()">Register</button>
</form>

<script>
async function handleLogin() {
    const username = document.getElementById('username').value;
    const password = document.getElementById('password').value;
    
    const resp = await fetch('/login', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ username, password })
    });
    
    if (!resp.ok) {
        alert('Login failed: Invalid credentials');
        return;
    }
    
    const data = await resp.json();
    sessionStorage.setItem('token', data.access_token);
    window.location.href = '/dashboard';
}

async function handleRegister() {
    const username = document.getElementById('username').value;
    const password = document.getElementById('password').value;
    
    if (password.length < 8) {
        alert('Password must be at least 8 characters');
        return;
    }
    
    const resp = await fetch('/register', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ username, password })
    });
    
    if (!resp.ok) {
        alert('Registration failed: User may already exist');
        return;
    }
    
    const data = await resp.json();
    sessionStorage.setItem('token', data.access_token);
    alert('Registered successfully!');
    window.location.href = '/dashboard';
}
</script>
```

---

### 2. Form Page (form.html)

**Status**: 🔴 NEEDS UPDATE

**What to Change**:
- [x] Replace form submission with JavaScript API call
- [x] Add token authentication to API call
- [x] Display results without page refresh
- [x] Add logout button

**Before** (HTML form submission):
```html
<form method="POST" action="/form">
    <input name="coffee_cups" type="number" required>
    <!-- other fields -->
    <button type="submit">Submit</button>
</form>

<!-- Results shown after page reload -->
{% if score %}
    <p>Score: {{ score }}</p>
    <p>{{ message }}</p>
{% endif %}
```

**After** (JavaScript API):
```html
<button onclick="logout()" style="float: right;">Logout</button>

<form id="stressForm">
    <input id="coffeeCups" name="coffee_cups" type="number" required>
    <input id="caffeineMg" name="caffeine_mg" type="number" required>
    <input id="sleepHours" name="sleep_hours" type="number" step="0.5" required>
    <input id="activityHours" name="activity_hours" type="number" step="0.5" required>
    <input id="age" name="age" type="number" required>
    
    <select id="gender" name="gender" required>
        <option value="">Select Gender</option>
        <option value="M">Male</option>
        <option value="F">Female</option>
        <option value="Other">Other</option>
    </select>
    
    <select id="smoker" name="smoker" required>
        <option value="">Smoker?</option>
        <option value="Yes">Yes</option>
        <option value="No">No</option>
    </select>
    
    <select id="alcohol" name="alcohol" required>
        <option value="">Alcohol Consumption?</option>
        <option value="Yes">Yes</option>
        <option value="No">No</option>
    </select>
    
    <!-- Symptoms (0-4 scale) -->
    <label>Palpitations/Tremor: <input id="symptom1" type="range" min="0" max="4" value="0"></label>
    <label>Insomnia: <input id="symptom2" type="range" min="0" max="4" value="0"></label>
    <label>Agitation: <input id="symptom3" type="range" min="0" max="4" value="0"></label>
    <label>Concentration: <input id="symptom4" type="range" min="0" max="4" value="0"></label>
    <label>Headache: <input id="symptom5" type="range" min="0" max="4" value="0"></label>
    <label>Digestive: <input id="symptom6" type="range" min="0" max="4" value="0"></label>
    
    <button type="button" onclick="submitForm()">Submit</button>
</form>

<!-- Results displayed here -->
<div id="results" style="display: none;">
    <h3>Results</h3>
    <p>Risk Score: <strong id="score"></strong></p>
    <p id="message"></p>
</div>

<script>
function getToken() {
    const token = sessionStorage.getItem('token');
    if (!token) {
        alert('Not logged in');
        window.location.href = '/';
    }
    return token;
}

function logout() {
    sessionStorage.removeItem('token');
    window.location.href = '/';
}

async function submitForm() {
    const token = getToken();
    
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
    
    try {
        const resp = await fetch('/form', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'Authorization': `Bearer ${token}`
            },
            body: JSON.stringify(formData)
        });
        
        if (resp.status === 401) {
            alert('Session expired. Please login again.');
            window.location.href = '/';
            return;
        }
        
        if (!resp.ok) {
            alert('Validation error. Check your input.');
            return;
        }
        
        const result = await resp.json();
        document.getElementById('score').textContent = (result.score * 100).toFixed(1) + '%';
        document.getElementById('message').textContent = result.message;
        document.getElementById('results').style.display = 'block';
    } catch (error) {
        alert('Error submitting form: ' + error.message);
    }
}
</script>
```

---

### 3. Dashboard Page (dashboard.html)

**Status**: 🔴 NEEDS UPDATE

**What to Change**:
- [x] Add token authentication to data fetch
- [x] Handle 403 (insufficient permissions) error
- [x] Add logout button
- [x] Check user role before showing admin features

**Before** (No authentication):
```javascript
// Fetch dashboard data without token
const resp = await fetch('/dashboard_data?sex=M');
const data = await resp.json();
```

**After** (With token and error handling):
```javascript
function getToken() {
    const token = sessionStorage.getItem('token');
    if (!token) {
        alert('Not logged in');
        window.location.href = '/';
    }
    return token;
}

function logout() {
    sessionStorage.removeItem('token');
    window.location.href = '/';
}

async function loadDashboardData(filters = {}) {
    const token = getToken();
    
    const params = new URLSearchParams(filters);
    const resp = await fetch(`/dashboard-data?${params}`, {
        headers: { 'Authorization': `Bearer ${token}` }
    });
    
    if (resp.status === 401) {
        alert('Session expired. Please login again.');
        window.location.href = '/';
        return;
    }
    
    if (resp.status === 403) {
        document.getElementById('dashboardContent').innerHTML =
            '<p style="color: red;">You need admin or analyst role to view this dashboard.</p>';
        return;
    }
    
    if (!resp.ok) {
        alert('Error loading dashboard data');
        return;
    }
    
    const data = await resp.json();
    renderCharts(data);  // Your existing chart rendering code
}

// Add to page load
document.addEventListener('DOMContentLoaded', () => {
    loadDashboardData();
});
```

---

### 4. JavaScript File (form.js)

**Status**: 🔴 NEEDS UPDATE

**What to Add**:
- [x] Helper function for API calls with token
- [x] Token refresh/validation logic
- [x] Error handling for 401/403
- [x] Logout functionality

**Add to form.js**:
```javascript
// API Helper
async function apiCall(endpoint, method = 'GET', body = null) {
    const token = sessionStorage.getItem('token');
    
    if (!token) {
        alert('Not logged in. Redirecting...');
        window.location.href = '/';
        return null;
    }
    
    const options = {
        method,
        headers: {
            'Content-Type': 'application/json',
            'Authorization': `Bearer ${token}`
        }
    };
    
    if (body) options.body = JSON.stringify(body);
    
    try {
        const resp = await fetch(endpoint, options);
        
        if (resp.status === 401) {
            sessionStorage.removeItem('token');
            alert('Session expired. Please login again.');
            window.location.href = '/';
            return null;
        }
        
        if (resp.status === 403) {
            alert('You do not have permission for this action.');
            return null;
        }
        
        if (!resp.ok) {
            const error = await resp.json();
            throw new Error(error.detail || `HTTP ${resp.status}`);
        }
        
        return resp;
    } catch (error) {
        console.error('API Error:', error);
        alert('API Error: ' + error.message);
        return null;
    }
}

// Validate token is still valid
function isAuthenticated() {
    return !!sessionStorage.getItem('token');
}

// Redirect if not authenticated
function requireAuth() {
    if (!isAuthenticated()) {
        window.location.href = '/';
    }
}

// Logout function
function logout() {
    sessionStorage.removeItem('token');
    window.location.href = '/';
}
```

---

## Testing Checklist

### Before Deployment

- [ ] **Login Page**
  - [ ] Can register new user
  - [ ] Can login with registered user
  - [ ] Token stored in sessionStorage
  - [ ] Error message shows for invalid credentials
  - [ ] Password length validation (min 8 chars)
  - [ ] Username validation (3-50 chars)

- [ ] **Form Page**
  - [ ] Can access form only when logged in
  - [ ] Form submission succeeds with valid data
  - [ ] Results displayed without page refresh
  - [ ] Validation works (age range, coffee cups, sleep hours, etc.)
  - [ ] Logout button works
  - [ ] Token included in request headers

- [ ] **Dashboard Page**
  - [ ] Charts load for admin/analyst users
  - [ ] Error message shows for regular users
  - [ ] Logout button works
  - [ ] Filters work correctly

- [ ] **Error Handling**
  - [ ] 401 redirects to login
  - [ ] 403 shows permission error
  - [ ] 422 shows validation error
  - [ ] Network errors handled gracefully

### Curl Testing Commands

```bash
# Register
curl -X POST http://localhost:8000/register \
  -H "Content-Type: application/json" \
  -d '{"username":"test","password":"password123"}'

# Login
curl -X POST http://localhost:8000/login \
  -H "Content-Type: application/json" \
  -d '{"username":"test","password":"password123"}'

# Get predictions (replace TOKEN)
curl -X GET http://localhost:8000/my-predictions \
  -H "Authorization: Bearer TOKEN"

# Dashboard data (requires admin role)
curl -X GET "http://localhost:8000/dashboard-data" \
  -H "Authorization: Bearer ADMIN_TOKEN"
```

---

## Common Issues & Solutions

### "Authorization header missing"
- ✓ Check token being passed in request
- ✓ Ensure header format: `Authorization: Bearer TOKEN`
- ✓ Verify token not expiring

### "Invalid token"
- ✓ Token may have expired (30 min default)
- ✓ User needs to login again
- ✓ Check SECRET_KEY matches between old and new code

### Form shows "Validation error"
- ✓ Check numeric fields are numbers (not strings)
- ✓ Check symptom values are 0-4
- ✓ Check age is 18-100
- ✓ Check enums match (M/F for gender, Yes/No for boolean)

### Dashboard shows "Insufficient permissions"
- ✓ User needs admin or analyst role
- ✓ Update user role in database:
  ```bash
  sqlite3 stres.db "UPDATE user SET role='admin' WHERE id=1;"
  ```

---

## Summary

| Step | Component | Status | Effort |
|---|---|---|---|
| 1 | Update login.html | [ ] Not Started | 30 min |
| 2 | Update form.html | [ ] Not Started | 45 min |
| 3 | Update dashboard.html | [ ] Not Started | 30 min |
| 4 | Update form.js | [ ] Not Started | 20 min |
| 5 | Test all endpoints | [ ] Not Started | 30 min |
| | **TOTAL** | | ~2.5 hours |

**Ready to start? Begin with login.html, then work down the list.**
