from sqlmodel import create_engine, Session, select
from api import Prediction, DATABASE_URL

engine = create_engine(DATABASE_URL)

with Session(engine) as session:
    preds = session.exec(select(Prediction)).all()

print("Număr predicții salvate:", len(preds))