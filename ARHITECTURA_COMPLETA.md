# 📊 Arhitectura Completă - Coffee Stress Evaluator

## 🏗️ 1. STRUCTURA SISTEMULUI

### 1.1 Diagrama de arhitectură

```
┌─────────────────────────────────────────────────────────────────────────┐
│                         FRONTEND (Browser)                              │
│  HTML: login.html, form.html, dashboard.html, history.html             │
│  CSS: style.css | JS: form.js                                           │
└────────────────────────┬────────────────────────────────────────────────┘
                         │ HTTP/HTTPS
                         ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                     FastAPI Server (main.py)                            │
│  - Uvicorn: 0.0.0.0:8000                                                │
│  - JWT Authentication & Authorization                                   │
│  - Request/Response Validation (Pydantic)                               │
│  - Error Handling & Logging                                             │
└────┬─────────┬──────────────┬────────────────────┬──────────────────────┘
     │         │              │                    │
     ▼         ▼              ▼                    ▼
┌─────────┐ ┌────────┐ ┌────────────┐ ┌───────────────────┐
│ routes/ │ │services│ │    db/     │ │  models/schemas.py│
│         │ │        │ │            │ │                   │
│ • auth  │ │• ML    │ │• Users     │ │ • Pydantic models │
│ • pages │ │• Auth  │ │• Predict   │ │ • Validation      │
│ • pred. │ │• Dash  │ │• Evaluat   │ │ • Enums           │
│ • dash  │ │        │ │            │ │                   │
└─────────┘ └────────┘ └───┬────────┘ └───────────────────┘
                            │
                            ▼
                    ┌───────────────────────┐
                    │   SQLite Database     │
                    │                       │
                    │ • stres.db (users,    │
                    │   predictions,        │
                    │   evaluations)        │
                    │                       │
                    │ • coffee_data.db      │
                    │   (historical data)   │
                    └───────────────────────┘
                            │
                            ▼
                    ┌───────────────────────┐
                    │   ML Model            │
                    │                       │
                    │stress_model_rf.joblib │
                    │(Random Forest)        │
                    └───────────────────────┘
```

---

## 📁 2. STRUCTURA FIȘIERELOR ȘI LOGICA

### 2.1 Fișierele de configurație

#### **config.py**
- **Rol**: Stochează toate setările aplicației (cale baze de date, cheie secretă, intervale valide)
- **Ce contine**:
  - `COFFEE_DB`: Cale către baza de date cu date cafeea
  - `STRES_DB`: Cale către baza de date cu utilizatori și predicții
  - `SECRET_KEY`: Cheie pentru JWT encoding
  - `MODEL_PATH`: Cale către modelul ML antrenat
  - Intervale de validare: vârstă (18-100), cești cafea (0-20), ore somn (0-24), etc.
  - Mapări pentru catgorii: țări, ocupații, calitate somn

#### **.env**
- **Rol**: Variabile de mediu (nu se salvează în git)
- **Ce contine**: Override-uri pentru calea bazei de date, SECRET_KEY

#### **requirements.txt**
- **Rol**: Lista cu versiunile tuturor bibliotecilor Python
- **Biblioteci principale**:
  - `fastapi`, `uvicorn` — framework web
  - `sqlalchemy`-like pattern cu `sqlite3`
  - `pydantic` — validare date
  - `joblib`, `scikit-learn` — machine learning
  - `python-jose` — JWT tokens
  - `bcrypt` — hash parole

---

### 2.2 Rutele API (routes/)

#### **routes/auth.py** — Autentificare
```
POST /register
  - Input: username, password
  - Logica: hash parola cu bcrypt, cre user în BD
  - Output: {"status": "success"} sau error

POST /login
  - Input: username, password
  - Logica: verifică user, compară parola hashed, generate JWT
  - Output: {"access_token": "...", "token_type": "bearer", "user_id": 123}
```

#### **routes/pages.py** — Pagini HTML
```
GET /                → login.html (dacă neautentificat)
GET /dashboard       → dashboard.html (necesită auth)
GET /form            → form.html (necesită auth)
GET /history         → history.html (necesită auth)
```
- Logica: Verifică JWT din cookies/headers, redirectează dacă nu autentificat

#### **routes/prediction.py** — Predicția stresului (PRINCIPAL)
```
POST /form
  - Input: 14 features (cafea, somn, înălțime, greutate, etc.)
  - Logica:
    1. Validează datele cu Pydantic
    2. Apelează MLService.predict_stress()
    3. Calculează indicatori derivați (BMI, cafeină săptămânal, somn)
    4. Salvează predicția în BD (tabelele "prediction" și "evaluation")
    5. Returnează scor stres (0-10), categorie, mesaj, detalii

POST /predict (vechi endpoint)
  - Similar, pentru backward compatibility

GET /api/history
  - Returnează: evaluări utilizator, date săptămânal, comparații

GET /my-predictions
  - Returnează: toate predicțiile utilizatorului
```

#### **routes/dashboard.py** — Dashboard admin
```
GET /dashboard-data (necesită role admin/analyst)
  - Returnează: date agregate pentru 8 grafice
```

---

### 2.3 Servicii (services/)

#### **services/auth_service.py** — Securitate
**Funcții principale**:
- `hash_password()` — Hashing bcrypt (29000 iterații NIST)
- `verify_password()` — Comparare parola plaintext cu hash
- `create_access_token()` — Generează JWT cu user_id, role, expirare (30 min)
- `verify_token()` — Decodează și validează JWT
- `get_current_user()` — Dependency FastAPI care extrage user din request
- `require_role()` — Dependency factory pentru verificare rol (user/admin/analyst)

#### **services/ml_service.py** — Machine Learning (LOGIC PREDICȚIE)
**Funcție principală**: `predict_stress(coffee_cups, sleep_hours, sleep_quality, ...)`
- **Input**: 14 feature-uri (dimensiuni, stil viață, sănătate)
- **Logica**:
  1. Calculează indicatori derivați:
     - `coffee_week = coffee_cups * 7`
     - `caffeine_week = coffee_cups * 7 * 95 mg`  ← mg cofeină/săptămână
     - `sleep_week = sleep_hours * 7`  ← ore somn/săptămână
     - `bmi = weight_kg / (height_m^2)`  ← indice masă corporală
  2. Traduce input-uri din română în engleza (Gender: Masculin→Male)
  3. Construiește DataFrame cu 14 coloane pentru model
  4. Apelează modelul Random Forest `predict_proba()`
  5. Mapează probabilități la scor stres 1-10 (Low=1.5, Medium=5.0, High=9.5)
  6. Categorizează: <3.5 = Scăzut, 3.5-7 = Moderat, >7 = Ridicat
  7. Generează mesaj recomandare
- **Output**: `(stress_score: float, category: str, details: dict, message: str)`

#### **services/dashboard_service.py** — Agregare date
- Construiește date pentru grafice (chart.js)
- Agregate: utilizatori activi, distribuție stres, trend timp

---

### 2.4 Baza de date (db/)

#### **db/connection.py** — Conexiuni SQLite
```python
@contextmanager
def get_stres_connection():  # Utilizatori, predicții, evaluări
def get_coffee_connection(): # Date cafeea (citire doar)
```
- **Context managers**: Asigură că conexiunile se închid automat
- Pattern: try/yield/finally pentru cleanup

#### **db/users.py** — Tabel utilizatori
```sql
CREATE TABLE user (
  id INTEGER PRIMARY KEY,
  username TEXT UNIQUE NOT NULL,
  password_hash TEXT NOT NULL,
  role TEXT DEFAULT 'user',  -- user|admin|analyst
  created_at TIMESTAMP
)
```
- `create_user()` — Cre user cu parola hashed
- `get_user_by_username()` — Caut user
- `user_exists()` — Verifică existență

#### **db/predictions.py** — Tabel predicții
```sql
CREATE TABLE prediction (
  id INTEGER PRIMARY KEY,
  user_id INTEGER FOREIGN KEY,
  varsta INT,
  cesti_cafea_zi INT,
  ore_somn FLOAT,
  nivel_stres INT,
  predictie_stres FLOAT,    -- Scor model 0-10
  symptom_score FLOAT,      -- Score simptome (vechi)
  created_at TIMESTAMP
)
```
- `save_prediction()` — Salvează predicție
- `get_user_predictions()` — Caut predicții utilizator

#### **db/evaluations.py** — Tabel evaluări
```sql
CREATE TABLE evaluation (
  id INTEGER PRIMARY KEY,
  user_id INTEGER FOREIGN KEY,
  coffee_intake_day INT,
  sleep_hours_night FLOAT,
  bmi FLOAT,
  heart_rate INT,
  stress_level TEXT,        -- Low|Medium|High
  stress_score FLOAT,
  physical_activity FLOAT,
  created_at TIMESTAMP
)
```
- `save_evaluation()` — Salvează evaluare
- `get_user_evaluations()` — Fetch evaluări
- `get_user_evaluations_last_week()` — Date ultimei săptămâni
- `get_weekly_comparison()` — Comparație săptămâni

---

### 2.5 Modele de date (models/schemas.py)

#### **Enumerații (Enum)**
```python
class Gender(str, Enum):          # Masculin | Feminin | Altul
class Country(str, Enum):         # 28 țări europene
class Occupation(str, Enum):      # Student | Birou | Sănătate | ...
class SleepQuality(str, Enum):    # Excelent | Bun | Mediu | Slab
class HealthIssues(str, Enum):    # Niciunul | Ușoare | Moderate | Severe
class BooleanChoice(str, Enum):   # Da | Nu
```

#### **Request/Response Models (Pydantic)**
```python
class FormSubmissionRequest:
  # 14 features
  coffee_cups: int          (0-20)
  sleep_hours: float        (0-24)
  sleep_quality: Enum       (Excelent|Bun|Mediu|Slab)
  activity_hours: float     (0-30)
  height_cm: int            (120-220)
  weight_kg: float          (30-200)
  heart_rate: int           (40-200)
  age: int                  (18-100)
  gender: Enum
  country: Enum
  occupation: Enum
  smoking: Enum             (Da|Nu)
  alcohol: Enum             (Da|Nu)
  health_issues: Enum

class FormSubmissionResponse:
  prediction: float         # 0-10
  prediction_category: str  # Scăzut|Moderat|Ridicat
  message: str
  submission_id: int
  details: dict             # {bmi, caffeine_week, sleep_week, ...}
```

---

### 2.6 Frontend (templates/ + static/)

#### **templates/base.html** — Template de bază
- Structura HTML comună
- CSS global
- Navigation/header

#### **templates/login.html** — Pagina login
```
┌─────────────────────────┐
│  Coffee Stress Evaluator │
├─────────────────────────┤
│ [Username input]        │
│ [Password input]        │
│ [Login button]          │
│ [Register button]       │
└─────────────────────────┘
```
- **Logica JS**: POST /login, primește JWT, salvează în cookie
- JWT stocat 30 min, apoi expirare auto

#### **templates/form.html** — Formular predicție (PRINCIPAL)
```
4 Blocuri:
1. 🌙 Somn și Cafea
   - Cești cafea/zi
   - Ore somn/noapte
   - Calitate somn
   
2. 🏃 Activitate și Corp
   - Ore activitate/săptămână
   - Înălțime
   - Greutate
   - Puls în repaus
   
3. 👤 Date personale
   - Vârstă
   - Gen
   - Țară
   - Ocupație
   
4. 🚭 Stil viață
   - Fumat: Da|Nu
   - Alcool: Da|Nu
   - Probleme sănătate
```
- **Validare client-side**: rerange min/max
- **Submit**: POST /form cu JWT, primește:
  ```json
  {
    "prediction": 7.2,
    "prediction_category": "Ridicat",
    "message": "Stres ridicat. Se recomandă...",
    "details": {
      "bmi": 24.5,
      "caffeine_week": 1995,
      "sleep_week": 56
    }
  }
  ```
- **Rezultat**: Circular progress indicator, categorie, mesaj, detalii

#### **templates/dashboard.html** — Dashboard (admin)
- 8 grafice Chart.js
- Date agregate: distribuție stres, trend, trending topics

#### **templates/history.html** — Istoric evaluări
- Tabel evaluări utilizator
- Grafice tend stres
- Comparație săptămânal

#### **static/style.css** — Stil global
- Dark mode/light mode
- Responsive design

#### **static/form.js** — Logica formular
- Event listener submit
- Colecție date din form
- Fetch POST /form
- Display rezultat cu formatare

---

## 🔄 3. FLUXUL INTERACȚIUNE UTILIZATOR

### Pas 1: Acces site
```
Utilizator accesează http://localhost:8000
            ↓
    GET / (pages.py)
            ↓
    Verifică JWT din cookies
            ↓
    ┌─────────────────────────────┐
    │ Dacă NU autentificat         │
    │ → Servește login.html        │
    └─────────────────────────────┘
```

### Pas 2: Înregistrare/Login
```
Utilizator completează:
  username: "john_doe"
  password: "secure_pass123"
            ↓
    POST /register (auth.py)
            ↓
    Validează: username unic, parola 8+ caractere
            ↓
    Hash parola cu bcrypt (29000 iterații)
            ↓
    INSERT INTO user table
            ↓
    ✅ Redirect la login
            ↓
    POST /login (auth.py)
            ↓
    SELECT user WHERE username
            ↓
    Verifică password_hash
            ↓
    Generează JWT: "eyJhbGc..."
            ↓
    Set-Cookie: access_token=JWT (HttpOnly, 30 min)
            ↓
    Redirect la /dashboard
```

### Pas 3: Completarea formularului
```
Utilizator vede pagina /form.html
            ↓
    Completează 14 feature-uri
            ↓
    Clic "Calculează nivelul de stres"
            ↓
    JavaScript:
    ├─ Colecție valori din form
    ├─ GET JWT din cookie
    ├─ POST /form cu auth: Bearer JWT
    └─ Request body: 14 feature-uri JSON
            ↓
    Backend (routes/prediction.py):
    ├─ Validează cu Pydantic
    ├─ Verifică JWT cu get_current_user
    ├─ Apelează MLService.predict_stress()
    │  ├─ Calculează: BMI, cafeină/săpt, somn/săpt
    │  ├─ Traduce categorii din română
    │  ├─ Construiește DataFrame 14 coloane
    │  ├─ Apelează model Random Forest
    │  ├─ Mapează probabilități → scor 0-10
    │  └─ return (stress_score, category, details, message)
    ├─ Salvează în BD:
    │  ├─ INSERT INTO prediction (...)
    │  └─ INSERT INTO evaluation (...)
    └─ return JSON response
            ↓
    Frontend:
    ├─ Primește: prediction, category, message, details
    ├─ Populează circular progress indicator
    ├─ Afișează categorie + mesaj recomandare
    ├─ Afișează detalii: BMI, cafeină, somn
    └─ Scroll la rezultat cu smoothing
```

### Pas 4: Vizualizare istoric
```
Utilizator acum pe /history.html
            ↓
    JavaScript:
    ├─ GET /api/history (auth: Bearer JWT)
    └─ Request: niciun parameter
            ↓
    Backend (routes/prediction.py):
    ├─ Verifică JWT
    ├─ SELECT * FROM evaluation WHERE user_id
    ├─ SELECT * FROM evaluation (last 7 days)
    ├─ SELECT comparație săptămâni
    └─ return JSON {evaluations, weekly_data, weekly_comparison}
            ↓
    Frontend:
    ├─ Randează tabel cu evaluări
    ├─ Construiește grafice Chart.js
    └─ Afișează trend stres
```

### Pas 5: Expirare sesiune
```
Utilizator inactiv 30 minute
            ↓
    JWT expiră (exp claim)
            ↓
    Clic orice buton → fetch fail
            ↓
    get_current_user() → raises 401 Unauthorized
            ↓
    Frontend redirecționează la /
            ↓
    Utilizator trebuie să face login din nou
```

---

## 🔐 4. SECURITATE

### Autentificare
- **Parole**: Hashed cu bcrypt (29000 iterații NIST)
- **Plaintext**: ❌ NICIODATĂ nu se salvează parola plaintext
- **Sesiuni**: JWT (JSON Web Tokens) cu expirare 30 min
- **Transport**: Token în cookie HttpOnly (citire JS = NU) + header Authorization

### Autorizare
- **Roluri**: user | admin | analyst
- **Role-based access control**: 
  - `/dashboard-data` → necesită admin/analyst
  - `/form` → necesită user
  - `/` → public (logout)
- **Dependency injection**: FastAPI `Depends(get_current_user)`, `Depends(require_role(...))`

### Validare
- **Pydantic**: Validează TOATE input-urile
  - Tipuri de date
  - Intervale: vârstă 18-100, cafea 0-20 cești
  - Enumerații: doar Gender.MASCULINE, Gender.FEMININE, etc.
- **Răspuns validare fail**: HTTP 422 Unprocessable Entity cu erori detaliate

### Erori
- **JWT nevalid**: 401 Unauthorized
- **Rol insuficient**: 403 Forbidden
- **Validare fail**: 422 Unprocessable Entity
- **User neautentificat**: 401 + redirect la login

---

## 📊 5. FLUXUL DATELOR

```
┌───────────────────────────────────────────────────────────────┐
│ UTILIZATOR COMPLETEAZĂ FORMULAR (14 FEATURE-URI)             │
└────────────────────┬────────────────────────────────────────┘
                     │ POST /form + JWT
                     ▼
        ┌─────────────────────────────┐
        │ Validare Pydantic (422?)   │
        │ Autentificare JWT (401?)   │
        └────────────┬────────────────┘
                     │
                     ▼
        ┌─────────────────────────────┐
        │ MLService.predict_stress()  │
        │  14 features → 1 predicție  │
        │  Calcul:                    │
        │  • BMI = weight/(height²)   │
        │  • Cafea/săpt = cafeiuni*7  │
        │  • Cafeină/săpt = cafeuni*7*95
        │  • Somn/săpt = ore*7        │
        └────────────┬────────────────┘
                     │
                     ▼
        ┌─────────────────────────────┐
        │ Random Forest Model         │
        │ Predicție probabilități     │
        │ [Low: 0.2, Med: 0.5, High:0.3]
        │ → Mapare scor 1-10          │
        └────────────┬────────────────┘
                     │
                     ▼
        ┌─────────────────────────────┐
        │ Categorizare rezultat:      │
        │ <3.5 = "Scăzut"             │
        │ 3.5-7 = "Moderat"           │
        │ >7 = "Ridicat"              │
        └────────────┬────────────────┘
                     │
                     ▼
        ┌─────────────────────────────┐
        │ Salvează în BD:             │
        │ • predictions (veche)       │
        │ • evaluations (nouă)        │
        └────────────┬────────────────┘
                     │
                     ▼
        ┌─────────────────────────────┐
        │ Return JSON Response:       │
        │ {                           │
        │   prediction: 7.2,          │
        │   category: "Ridicat",      │
        │   message: "...",           │
        │   details: {bmi, caff, ...} │
        │ }                           │
        └────────────┬────────────────┘
                     │ JSON response
                     ▼
        ┌─────────────────────────────┐
        │ Frontend renderează:        │
        │ • Circular progress         │
        │ • Categorie + culoare       │
        │ • Mesaj recomandare         │
        │ • Detalii (BMI, cafeină)   │
        └─────────────────────────────┘
```

---

## 🎯 6. FLUXUL PRINCIPAL AL APLICAȚIEI

```
┌─────────────────────────────────────────────────────────────┐
│                        main.py                              │
│  1. Import router-e: auth, pages, prediction, dashboard    │
│  2. Cre FastAPI app                                         │
│  3. UserRepository.init_db()  → Create user table           │
│  4. PredictionRepository.init_db() → Create prediction tbl │
│  5. EvaluationRepository.init_db() → Create evaluation tbl │
│  6. Mount /static directory                                 │
│  7. Exception handler pentru validation errors             │
│  8. Include router-e în FastAPI                            │
│  9. Uvicorn.run(app, host 0.0.0.0:8000, reload=True)      │
└─────────────────────────────────────────────────────────────┘
                         │
        ┌────────────────┼─────────────────┬──────────────┐
        │                │                 │              │
        ▼                ▼                 ▼              ▼
    ┌────────┐      ┌──────────┐    ┌────────────┐  ┌──────────┐
    │ pages  │      │   auth   │    │ prediction │  │dashboard │
    │        │      │          │    │            │  │          │
    │ GET /  │      │POST /reg │    │ POST /form │  │GET /dash │
    │ GET /d │      │POST /log │    │GET /hist   │  │-data     │
    │ GET /f │      │          │    │            │  │          │
    │ GET /h │      │          │    │            │  │          │
    └────────┘      └──────────┘    └────────────┘  └──────────┘
        │                │                 │              │
        └────────────────┼─────────────────┴──────────────┘
                         │
        ┌────────────────┼──────────┬────────────────┐
        │                │          │                │
        ▼                ▼          ▼                ▼
  ┌────────────┐  ┌────────────┐ ┌──────────┐  ┌────────┐
  │auth_service│  │ml_service  │ │db/*.py   │  │schemas │
  │            │  │            │ │          │  │        │
  │JWT, bcrypt │  │predict_    │ │Users,    │  │Enum    │
  │            │  │stress()    │ │Pred,Eval │  │Request │
  └────────────┘  │            │ └──────────┘  │Response│
                  │BMI, caffein│              │        │
                  │Random Forst│              └────────┘
                  └────────────┘
                         │
                         ▼
                  ┌──────────────┐
                  │ SQLite DBs   │
                  │              │
                  │stres.db:     │
                  │• user        │
                  │• prediction  │
                  │• evaluation  │
                  │              │
                  │coffee_data.db│
                  └──────────────┘
```

---

## 🔄 7. CICLU UNEI PREDICȚII

```
1. INTRARE
   ↓
   Utilizator: 3 cești/zi, 8 ore somn, 70kg, 170cm, etc.
   
2. FRONTEND VALIDATION
   ↓
   JavaScript verifică: 0 ≤ cești ≤ 20, 0 ≤ ore ≤ 24
   
3. CONSTRUIRE REQUEST
   ↓
   ```json
   {
     "coffee_cups": 3,
     "sleep_hours": 8.0,
     "sleep_quality": "Bun",
     "activity_hours": 5.0,
     "height_cm": 170,
     "weight_kg": 70.0,
     "heart_rate": 72,
     "age": 28,
     "gender": "Masculin",
     "country": "România",
     "occupation": "Birou",
     "smoking": "Nu",
     "alcohol": "Da",
     "health_issues": "Niciunul"
   }
   ```
   
4. SERVER RECEIVES
   ↓
   POST /form + Authorization: Bearer JWT
   
5. VALIDARE
   ↓
   ✓ JWT valid → user_id = 5
   ✓ Pydantic validează 14 feature-uri
   ✓ Toate valorile în interval
   
6. CALCUL INDICATORI
   ↓
   coffee_week = 3 * 7 = 21 cești/săpt
   caffeine_week = 3 * 7 * 95 = 1995 mg/săpt
   sleep_week = 8 * 7 = 56 ore/săpt
   bmi = 70 / (1.70²) = 24.22
   
7. TRANSFORMARE PENTRU MODEL
   ↓
   Traducere engleză:
   gender: "Masculin" → "Male"
   sleep_quality: "Bun" → "Good"
   health_issues: "Niciunul" → "None"
   
   Encoding binar:
   smoking: "Nu" → 0
   alcohol: "Da" → 1
   
8. CONSTRUIRE DATAFRAME
   ↓
   ```
   Age                     28
   Gender                  Male
   Country                 Romania
   Coffee_Intake_Week      21
   Caffeine_mg_Week        1995
   Sleep_Hours_Week        56
   Sleep_Quality           Good
   BMI                     24.22
   Heart_Rate              72
   Physical_Activity_Hours_Week 5
   Health_Issues           None
   Occupation              Office
   Smoking                 0
   Alcohol_Consumption     1
   ```
   
9. PREDICȚIE MODEL
   ↓
   Random Forest predict_proba():
   [Low: 0.1, Medium: 0.7, High: 0.2]
   
   Mapare scor:
   score = 0.1*1.5 + 0.7*5.0 + 0.2*9.5 = 5.65
   
10. CATEGORIZARE
    ↓
    5.65 ∈ [3.5, 7) → "Moderat"
    
11. MESAJ RECOMANDARE
    ↓
    "Stres moderat. Încearcă să reduci consumul de cafea și dormi mai mult."
    
12. SALVARE BD
    ↓
    INSERT INTO prediction (user_id=5, varsta=28, ..., predictie_stres=5.65)
    INSERT INTO evaluation (user_id=5, coffee_intake_day=3, ..., stress_score=5.65, stress_level='Medium')
    
13. RESPONSE
    ↓
    ```json
    {
      "prediction": 5.65,
      "prediction_category": "Moderat",
      "message": "Stres moderat. Încearcă...",
      "submission_id": 42,
      "details": {
        "bmi": 24.22,
        "caffeine_week": 1995,
        "sleep_week": 56,
        "heart_rate": 72
      }
    }
    ```
    
14. FRONTEND DISPLAY
    ↓
    • Circular progress: 5.65/10 (56.5%)
    • Culoare: 🟠 Orange (Moderat)
    • Mesaj: "Stres moderat. Încearcă..."
    • Detalii: BMI: 24.22, Cafeină: 1995mg, etc.
    
15. SALVARE ISTORIC
    ↓
    Utilizator poate acum accesa /history și vedea această predicție
```

---

## 🎨 8. INTERFAȚA UTILIZATOR

### Login Page
```
┌──────────────────────────────────────┐
│   ☕ Coffee Stress Evaluator          │
├──────────────────────────────────────┤
│                                      │
│  Username: [________________]        │
│  Password: [________________]        │
│                                      │
│  [   Login Button    ]               │
│  [   Register Button ]               │
│                                      │
└──────────────────────────────────────┘
```

### Form Page (Bloc 1: Somn & Cafea)
```
┌──────────────────────────────────────┐
│ 🌙 Somn și Cafea                     │
├──────────────────────────────────────┤
│                                      │
│ Câte cești de cafea/zi?              │
│ [_____] cești (0-20)                 │
│                                      │
│ Câte ore dormi/noapte?               │
│ [_____] ore (0-24)                   │
│                                      │
│ Calitate somn?                       │
│ ☐ Excelent ☐ Bun ☐ Mediu ☐ Slab   │
│                                      │
└──────────────────────────────────────┘
```

### Rezultat Predicție
```
┌──────────────────────────────────────┐
│ Rezultatul Evaluării                 │
├──────────────────────────────────────┤
│                                      │
│         ╭──────────╮                 │
│         │ 5.65     │  ← Circular      │
│         │   /10    │     progress     │
│         ╰──────────╯     (56.5%)      │
│                                      │
│  🟠 Stres Moderat                    │
│                                      │
│  "Stres moderat. Încearcă să reduci" │
│   "consumul de cafea și dormi mai"   │
│   "mult..."                          │
│                                      │
│  Detalii:                            │
│  • BMI: 24.2                         │
│  • Somn (săpt): 56 ore               │
│  • Cafeină (săpt): 1995 mg           │
│  • Puls: 72 bpm                      │
│                                      │
│  [Completează din nou]               │
│                                      │
└──────────────────────────────────────┘
```

---

## 📈 9. METRICI ȘI STATISTICI

### Tabel Predicții
```
┌────┬──────┬─────────┬──────────┬────────────┬─────────────┐
│ ID │ Vârs │ Cafea/z │ Somn/no │ Stres calc │ Data        │
├────┼──────┼─────────┼──────────┼────────────┼─────────────┤
│ 1  │ 28   │ 3       │ 8        │ 5.65/10    │ 2024-04-20  │
│ 2  │ 28   │ 4       │ 7        │ 6.8/10     │ 2024-04-21  │
│ 3  │ 28   │ 2       │ 9        │ 4.2/10     │ 2024-04-22  │
└────┴──────┴─────────┴──────────┴────────────┴─────────────┘
```

### Comparație Săptămânal
```
Săptămâna 1: Stress mediu = 5.6/10 (Moderat)
Săptămâna 2: Stress mediu = 5.9/10 (Moderat) ↗ +5.4%
Săptămâna 3: Stress mediu = 4.8/10 (Scăzut) ↘ -18.6%
```

---

## ❌ 10. ERORI COMUNE ȘI DEBUGGING

### Eroare: "JWT expirat"
```
Simptom: POST /form → 401 Unauthorized
Cauză: Token JWT > 30 minute
Soluție: Utilizator face login din nou
```

### Eroare: "Validare fail"
```
Simptom: POST /form → 422 Unprocessable Entity
Cauză: Campo outside interval (ex: vârstă 150)
Soluție: Completează din nou cu valori valide
```

### Eroare: "Model ML nu s-a încărcat"
```
Simptom: POST /form → 500 Internal Server Error
Loguri: "[ML SERVICE] ✗ Could not load model"
Cauza: stress_model_rf.joblib missing
Soluție: Antrenează modelul, salvează în MODEL_PATH
```

### Eroare: "User deja există"
```
Simptom: POST /register → 400 Bad Request
Cauză: username deja în tabel
Soluție: Alege alt username
```

---

## 🚀 11. DEPLOYMENT & SCALARE

### Development
```bash
python main.py
# Uvicorn pe localhost:8000 cu --reload
```

### Production
```bash
# Cu Gunicorn + Uvicorn workers
gunicorn -w 4 -k uvicorn.workers.UvicornWorker main:app --bind 0.0.0.0:8000
```

### Optimizări
- Docker containerization
- Database: SQLite → PostgreSQL (multi-user)
- Cache: Redis (sesiuni, predicții frecvente)
- CDN: Statice pe CloudFront
- CI/CD: GitHub Actions

---

## 📝 12. REZUMAT COMPLET

| Componentă | Rol | Tehnologie |
|-----------|-----|-----------|
| **Frontend** | UI interactivă | HTML, CSS, JavaScript |
| **Backend API** | Logică server | FastAPI, Python |
| **Autentificare** | Securitate | JWT + bcrypt |
| **Machine Learning** | Predicție stres | Random Forest (scikit-learn) |
| **Bază de date** | Persistență | SQLite |
| **Validare** | Input safety | Pydantic |
| **Serving** | HTTP server | Uvicorn |

**Fluxul:** Utilizator → Login → Completează formular 14-features → Backend validează & apelează ML → Predicție stres 0-10 → Salvează BD → Afișează rezultat cu recomandări

---

Aceasta este arhitectura completă a aplicației tale! 🎉
