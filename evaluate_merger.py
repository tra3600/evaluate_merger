"""Évaluation financière simplifiée d'une fusion-acquisition entre deux entreprises.

Usage :
    python evaluate_merger.py                      # exemple intégré
    python evaluate_merger.py a.json b.json        # deux bilans au format JSON
    python evaluate_merger.py a.json b.json --json # sortie JSON

Champs d'un bilan : revenue, profit, assets, liabilities (obligatoires) ;
revenue_prev (CA de l'exercice précédent) et name (facultatifs).
"""
import argparse
import json
import sys
from dataclasses import dataclass, field

REQUIRED = ("revenue", "profit", "assets", "liabilities")


@dataclass
class Thresholds:
    max_debt_ratio: float = 0.5         # passifs / actifs
    min_profit_margin: float = 0.10     # bénéfice / revenu
    min_revenue_growth: float = 0.0     # croissance combinée du CA
    min_roa: float = 0.05               # bénéfice / actifs
    min_score: float = 0.75             # part de critères à satisfaire


@dataclass
class Evaluation:
    metrics: dict
    criteria: dict = field(default_factory=dict)  # nom -> (valeur, seuil, ok)
    score: float = 0.0
    interesting: bool = False
    verdict: str = ""


def validate(company, label="entreprise"):
    """Vérifie et normalise un bilan ; lève ValueError si invalide."""
    if not isinstance(company, dict):
        raise ValueError(f"{label} : un dictionnaire est attendu")
    missing = [k for k in REQUIRED if k not in company]
    if missing:
        raise ValueError(f"{label} : champs manquants {missing}")
    data = {}
    for key in REQUIRED + ("revenue_prev",):
        if key not in company or company[key] is None:
            continue
        try:
            data[key] = float(company[key])
        except (TypeError, ValueError):
            raise ValueError(f"{label} : '{key}' doit être numérique") from None
    if data["revenue"] <= 0:
        raise ValueError(f"{label} : 'revenue' doit être > 0")
    if data["assets"] <= 0:
        raise ValueError(f"{label} : 'assets' doit être > 0")
    if data["liabilities"] < 0:
        raise ValueError(f"{label} : 'liabilities' doit être >= 0")
    if data.get("revenue_prev", 1) <= 0:
        raise ValueError(f"{label} : 'revenue_prev' doit être > 0")
    data["name"] = str(company.get("name", label))
    return data


def _ratios(c):
    return {
        "debt_ratio": c["liabilities"] / c["assets"],
        "profit_margin": c["profit"] / c["revenue"],
        "roa": c["profit"] / c["assets"],
    }


def evaluate_merger(company1, company2, thresholds=None):
    """Retourne un objet Evaluation (verdict, score, détail des critères)."""
    t = thresholds or Thresholds()
    c1 = validate(company1, "entreprise 1")
    c2 = validate(company2, "entreprise 2")

    combined = {k: c1[k] + c2[k] for k in REQUIRED}
    metrics = _ratios(combined)

    # Croissance : uniquement calculable si le CA précédent est connu pour les deux.
    if "revenue_prev" in c1 and "revenue_prev" in c2:
        prev = c1["revenue_prev"] + c2["revenue_prev"]
        metrics["revenue_growth"] = combined["revenue"] / prev - 1
    else:
        metrics["revenue_growth"] = None

    criteria = {
        "Ratio d'endettement combiné": (metrics["debt_ratio"], t.max_debt_ratio,
                                        metrics["debt_ratio"] < t.max_debt_ratio),
        "Marge bénéficiaire combinée": (metrics["profit_margin"], t.min_profit_margin,
                                        metrics["profit_margin"] > t.min_profit_margin),
        "Rentabilité des actifs (ROA)": (metrics["roa"], t.min_roa,
                                         metrics["roa"] > t.min_roa),
    }
    if metrics["revenue_growth"] is not None:
        g = metrics["revenue_growth"]
        criteria["Croissance du chiffre d'affaires"] = (g, t.min_revenue_growth,
                                                        g > t.min_revenue_growth)

    score = sum(ok for _, _, ok in criteria.values()) / len(criteria)
    # Les critères d'endettement et de marge combinés sont éliminatoires.
    essential = (criteria["Ratio d'endettement combiné"][2]
                 and criteria["Marge bénéficiaire combinée"][2])
    interesting = essential and score >= t.min_score
    verdict = ("La fusion-acquisition est financièrement intéressante."
               if interesting else
               "La fusion-acquisition n'est pas financièrement intéressante.")
    return Evaluation(metrics, criteria, score, interesting, verdict)


def format_report(ev):
    lines = ["Critères :"]
    for name, (value, threshold, ok) in ev.criteria.items():
        lines.append(f"  [{'OK' if ok else 'KO'}] {name} : {value:.2%} (référence {threshold:.2%})")
    if ev.metrics["revenue_growth"] is None:
        lines.append("  [--] Croissance du CA : non évaluée (revenue_prev absent)")
    lines.append(f"Score : {ev.score:.0%}")
    lines.append(ev.verdict)
    return "\n".join(lines)


def _to_json(ev):
    return {
        "metrics": ev.metrics,
        "criteria": {n: {"value": v, "reference": r, "ok": ok}
                     for n, (v, r, ok) in ev.criteria.items()},
        "score": ev.score,
        "interesting": ev.interesting,
        "verdict": ev.verdict,
    }


EXAMPLE = (
    {"name": "A", "revenue": 1_000_000, "revenue_prev": 900_000, "profit": 200_000,
     "assets": 1_500_000, "liabilities": 500_000},
    {"name": "B", "revenue": 800_000, "revenue_prev": 780_000, "profit": 100_000,
     "assets": 1_200_000, "liabilities": 400_000},
)


def main(argv=None):
    p = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    p.add_argument("files", nargs="*", help="deux fichiers JSON de bilans")
    p.add_argument("--json", action="store_true", help="sortie JSON")
    args = p.parse_args(argv)
    if len(args.files) not in (0, 2):
        p.error("fournir exactement deux fichiers JSON (ou aucun pour l'exemple)")
    try:
        if args.files:
            companies = []
            for path in args.files:
                with open(path, encoding="utf-8") as f:
                    companies.append(json.load(f))
        else:
            companies = EXAMPLE
        ev = evaluate_merger(*companies)
    except (OSError, ValueError) as e:  # JSONDecodeError est un ValueError
        print(f"Erreur : {e}", file=sys.stderr)
        return 1
    print(json.dumps(_to_json(ev), ensure_ascii=False, indent=2) if args.json
          else format_report(ev))
    return 0


if __name__ == "__main__":
    sys.exit(main())
