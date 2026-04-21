from fastapi import FastAPI, Request, Form
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from typing import Optional
import sqlite3
import joblib
import numpy as np
import os

# ----------------- Căi și conexiuni DB -----------------

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# baza cu cei 6173 respondenți – pentru dashboard
COFFEE_DB = "C:/Users/tatia/Desktop/Anul 3/Teza de licenta/coffee-risk-evaluator/coffee_data.db"
# baza pentru utilizatori + predicții
STRES_DB = os.path.join(BASE_DIR, "stres.db")


def get_coffee_conn():
    return sqlite3.connect(COFFEE_DB)


def get_stres_conn():
    return sqlite3.connect(STRES_DB)

# ----------------- FastAPI + templates + model -----------------

app = FastAPI()

app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")

# Încarcă modelul de stres
model_path = os.path.join(BASE_DIR, "stress_model_rf.joblib")
model = joblib.load(model_path)

# ----------------- Rute pagini (login, dashboard, form) -----------------


@app.get("/", response_class=HTMLResponse)
async def home(request: Request):
    return templates.TemplateResponse("login.html", {"request": request})


@app.post("/login")
async def login(
    request: Request,
    username: str = Form(...),
    password: str = Form(...),
):
    """
    Login simplu: dacă userul nu există îl creăm,
    dacă există verificăm parola și mergem la dashboard.
    """
    conn = get_stres_conn()
    cur = conn.cursor()
    cur.execute(
        "CREATE TABLE IF NOT EXISTS user ("
        "id INTEGER PRIMARY KEY AUTOINCREMENT, "
        "username TEXT UNIQUE, "
        "password TEXT)"
    )
    conn.commit()

    cur.execute("SELECT id, password FROM user WHERE username=?", (username,))
    row = cur.fetchone()

    if row:
        user_id, stored_password = row
        if stored_password != password:
            conn.close()
            return templates.TemplateResponse(
                "login.html",
                {
                    "request": request,
                    "error": "Utilizator sau parolă incorecte",
                },
            )
    else:
        cur.execute(
            "INSERT INTO user (username, password) VALUES (?, ?)",
            (username, password),
        )
        conn.commit()
        user_id = cur.lastrowid

    conn.close()

    return RedirectResponse(url="/dashboard", status_code=303)


@app.get("/dashboard", response_class=HTMLResponse)
async def dashboard_page(request: Request):
    return templates.TemplateResponse("dashboard.html", {"request": request})

# ----------------- Formular nou: GET + POST -----------------


@app.get("/form", response_class=HTMLResponse)
async def form_page(request: Request):
    return templates.TemplateResponse("form.html", {"request": request})


@app.post("/form", response_class=HTMLResponse)
async def form_submit(
    request: Request,
    coffee_cups: int = Form(...),
    caffeine_mg: int = Form(...),
    sleep_hours: float = Form(...),
    activity_hours: float = Form(...),
    age: int = Form(...),
    gender: str = Form(...),
    smoker: str = Form(...),
    alcohol: str = Form(...),
    symptoms_palpitations_tremor: int = Form(...),
    symptoms_insomnia: int = Form(...),
    symptoms_agitation: int = Form(...),
    symptoms_concentration: int = Form(...),
    symptoms_headache: int = Form(...),
    symptoms_digestive: int = Form(...),
):
    """
    Primește valorile din formularul extins și calculează un scor simplu de risc
    bazat pe simptome (0–1).
    """
    symptom_vals = [
        symptoms_palpitations_tremor,
        symptoms_insomnia,
        symptoms_agitation,
        symptoms_concentration,
        symptoms_headache,
        symptoms_digestive,
    ]

    max_per_symptom = 4  # Deloc(0) – Foarte des(4)
    score_raw = sum(symptom_vals)
    score = score_raw / (max_per_symptom * len(symptom_vals)) if symptom_vals else 0

    if score < 0.33:
        message = "Risc scăzut asociat consumului de cafea."
    elif score < 0.66:
        message = "Risc moderat, este bine să monitorizezi consumul."
    else:
        message = "Risc crescut, e recomandată reducerea consumului și consult medical."

    return templates.TemplateResponse(
        "form.html",
        {
            "request": request,
            "score": score,
            "message": message,
        },
    )

# ----------------- Date pentru dashboard (8 diagrame) -----------------


@app.get("/dashboard_data")
def dashboard_data(
    sex: Optional[str] = None,
    age_group: Optional[str] = None,
    domeniu: Optional[str] = None,
):
    conn = get_coffee_conn()
    cursor = conn.cursor()

    cursor.execute(
        """
        SELECT Varsta, Sex, Domeniu,
               "Cesti cafea/zi",
               "Tip cafea",
               "Ore somn/noapte",
               "Nivel stres",
               "Motiv consum",
               "Stare dupa cafea",
               "Loc consum",
               "Dependenta cafea",
               "Reducere consum",
               "Consumul de alcool",
               "Fumat",
               "Sanatate generala"
        FROM coffee_consumption
        """
    )
    rows = cursor.fetchall()
    conn.close()

    records = []
    for row in rows:
        (
            age_val, sex_val, domeniu_val,
            cesti_val,
            tip_cafea, ore_somn, nivel_stres, motiv,
            stare_dupa, loc_consum, dependenta, reducere,
            alcool, fumat, sanatate,
        ) = row

        try:
            age_int = int(age_val)
        except Exception:
            continue

        if age_int < 30:
            ag = "<30"
        elif 30 <= age_int <= 45:
            ag = "30-45"
        else:
            ag = ">45"

        rec = {
            "age_group": ag,
            "sex": str(sex_val) if sex_val is not None else "",
            "domeniu": str(domeniu_val) if domeniu_val is not None else "",
            "cesti": str(cesti_val) if cesti_val is not None else "",
            "tip_cafea": str(tip_cafea) if tip_cafea is not None else "",
            "ore_somn": str(ore_somn) if ore_somn is not None else "",
            "nivel_stres": str(nivel_stres) if nivel_stres is not None else "",
            "motiv": str(motiv) if motiv is not None else "",
            "stare_dupa": str(stare_dupa) if stare_dupa is not None else "",
            "loc_consum": str(loc_consum) if loc_consum is not None else "",
            "dependenta": str(dependenta) if dependenta is not None else "",
            "reducere": str(reducere) if reducere is not None else "",
            "alcool": str(alcool) if alcool is not None else "",
            "fumat": str(fumat) if fumat is not None else "",
            "sanatate": str(sanatate) if sanatate is not None else "",
        }
        records.append(rec)

    if sex:
        records = [r for r in records if r["sex"] == sex]
    if age_group:
        records = [r for r in records if r["age_group"] == age_group]
    if domeniu:
        records = [r for r in records if r["domeniu"] == domeniu]

    total = len(records)

    def simple_count(key: str):
        counts = {}
        for r in records:
            v = r[key] or "Necunoscut"
            counts[v] = counts.get(v, 0) + 1
        labels = list(counts.keys())
        values = [counts[k] for k in labels]
        return {"labels": labels, "values": values}

    ore_somn_data = simple_count("ore_somn")
    nivel_stres_data = simple_count("nivel_stres")
    motive_data = simple_count("motiv")
    cesti_data = simple_count("cesti")
    efecte_data = simple_count("stare_dupa")
    loc_consum_data = simple_count("loc_consum")

    dep_red_counts = {}
    for r in records:
        dep = r["dependenta"] or "Necunoscut"
        red = r["reducere"] or "Necunoscut"
        dep_red_counts.setdefault(dep, {})
        dep_red_counts[dep][red] = dep_red_counts[dep].get(red, 0) + 1

    dep_labels = list(dep_red_counts.keys())
    red_categories = set()
    for m in dep_red_counts.values():
        red_categories.update(m.keys())
    red_labels = sorted(red_categories)

    dep_series = []
    for red in red_labels:
        values = [dep_red_counts.get(dep, {}).get(red, 0) for dep in dep_labels]
        dep_series.append({"name": red, "values": values})
    dependenta_reducere_data = {
        "x_labels": dep_labels,
        "series": dep_series,
    }

    fas_counts = {}
    for r in records:
        fum = r["fumat"] or "Necunoscut"
        alc = r["alcool"] or "Necunoscut"
        san = r["sanatate"] or "Necunoscut"
        key = f"{fum} / {alc}"
        fas_counts.setdefault(key, {})
        fas_counts[key][san] = fas_counts[key].get(san, 0) + 1

    fas_x_labels = list(fas_counts.keys())
    san_categories = set()
    for m in fas_counts.values():
        san_categories.update(m.keys())
    san_labels = sorted(san_categories)

    fas_series = []
    for san in san_labels:
        values = [fas_counts.get(x, {}).get(san, 0) for x in fas_x_labels]
        fas_series.append({"name": san, "values": values})
    alcool_fumat_sanatate_data = {
        "x_labels": fas_x_labels,
        "series": fas_series,
    }

    return {
        "total_records": total,
        "cesti_tip_cafea": cesti_data,
        "ore_somn": ore_somn_data,
        "nivel_stres": nivel_stres_data,
        "motive": motive_data,
        "efecte": efecte_data,
        "loc_consum": loc_consum_data,
        "dependenta_reducere": dependenta_reducere_data,
        "alcool_fumat_sanatate": alcool_fumat_sanatate_data,
    }

# ----------------- Predicția individuală (model RF existent) -----------------


@app.post("/predict")
async def predict_endpoint(
    varsta: int = Form(...),
    cesti_cafea_zi: int = Form(...),
    ore_somn: float = Form(...),
    nivel_stres: int = Form(...),
):
    features = np.array([[varsta, cesti_cafea_zi, ore_somn, nivel_stres]])
    pred = model.predict(features)[0]

    conn = get_stres_conn()
    cur = conn.cursor()
    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS prediction (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            varsta INTEGER,
            cesti_cafea_zi INTEGER,
            ore_somn REAL,
            nivel_stres INTEGER,
            predictie REAL
        )
        """
    )
    conn.commit()
    cur.execute(
        "INSERT INTO prediction (varsta, cesti_cafea_zi, ore_somn, nivel_stres, predictie) "
        "VALUES (?, ?, ?, ?, ?)",
        (varsta, cesti_cafea_zi, ore_somn, nivel_stres, float(pred)),
    )
    conn.commit()
    conn.close()

    return {"predictie_stres": float(pred)}
