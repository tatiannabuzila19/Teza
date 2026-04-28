
import importlib

packages = [
    "fastapi",
    "uvicorn",
    "jinja2",
    "joblib",
    "numpy",
    "sklearn",
    "pydantic",
    "jose",
    "passlib",
    "bcrypt",
    "dotenv",
    "pandas",
    "openpyxl"
]

for package in packages:
    try:
        importlib.import_module(package)
        print(f"{package} is installed.")
    except ImportError:
        print(f"Error: {package} is not installed.")
