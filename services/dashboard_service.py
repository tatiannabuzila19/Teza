from typing import Optional, List, Dict
from db.connection import get_coffee_connection

class DashboardService:
    @staticmethod
    def fetch_and_filter_records(sex: Optional[str] = None,
                                 age_group: Optional[str] = None,
                                 domeniu: Optional[str] = None) -> List[Dict]:
        """Fetch coffee consumption data with optional filters."""
        with get_coffee_connection() as conn:
            query = """
                SELECT Varsta, Sex, Domeniu,
                       "Cesti cafea/zi", "Tip cafea", "Ore somn/noapte",
                       "Nivel stres", "Motiv consum", "Stare dupa cafea",
                       "Loc consum", "Dependenta cafea", "Reducere consum",
                       "Consumul de alcool", "Fumat", "Sanatate generala"
                FROM coffee_consumption
            """
            rows = conn.execute(query).fetchall()

        records = []
        for row in rows:
            try:
                age_int = int(row[0])
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
                "sex": str(row[1]) if row[1] else "",
                "domeniu": str(row[2]) if row[2] else "",
                "cesti": str(row[3]) if row[3] else "",
                "tip_cafea": str(row[4]) if row[4] else "",
                "ore_somn": str(row[5]) if row[5] else "",
                "nivel_stres": str(row[6]) if row[6] else "",
                "motiv": str(row[7]) if row[7] else "",
                "stare_dupa": str(row[8]) if row[8] else "",
                "loc_consum": str(row[9]) if row[9] else "",
                "dependenta": str(row[10]) if row[10] else "",
                "reducere": str(row[11]) if row[11] else "",
                "alcool": str(row[12]) if row[12] else "",
                "fumat": str(row[13]) if row[13] else "",
                "sanatate": str(row[14]) if row[14] else "",
            }
            records.append(rec)

        if sex:
            records = [r for r in records if r["sex"] == sex]
        if age_group:
            records = [r for r in records if r["age_group"] == age_group]
        if domeniu:
            records = [r for r in records if r["domeniu"] == domeniu]

        return records

    @staticmethod
    def generate_dashboard_data(sex: Optional[str] = None,
                              age_group: Optional[str] = None,
                              domeniu: Optional[str] = None) -> Dict:
        """Generate aggregated dashboard data for 8 charts."""
        records = DashboardService.fetch_and_filter_records(sex, age_group, domeniu)
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

        # Dependenta vs Reducere
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

        # Alcohol/Smoking/Health
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
