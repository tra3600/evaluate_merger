def evaluate_merger(company1, company2):
    # Extraire les données financières
    revenue1 = company1['revenue']
    profit1 = company1['profit']
    assets1 = company1['assets']
    liabilities1 = company1['liabilities']

    revenue2 = company2['revenue']
    profit2 = company2['profit']
    assets2 = company2['assets']
    liabilities2 = company2['liabilities']

    # Calculer les métriques combinées
    combined_revenue = revenue1 + revenue2
    combined_profit = profit1 + profit2
    combined_assets = assets1 + assets2
    combined_liabilities = liabilities1 + liabilities2

    # Critères de fusion
    revenue_growth = combined_revenue / (revenue1 + revenue2) - 1
    debt_ratio = combined_liabilities / combined_assets
    combined_profit_margin = combined_profit / combined_revenue

    # Définir les seuils
    acceptable_debt_ratio = 0.5
    minimum_profit_margin = 0.1

    # Évaluer l'opportunité de fusion
    if revenue_growth > 0 and debt_ratio < acceptable_debt_ratio and combined_profit_margin > minimum_profit_margin:
        return "La fusion-acquisition est financièrement intéressante."
    else:
        return "La fusion-acquisition n'est pas financièrement intéressante."

# Exemple de bilans financiers
company1 = {
    'revenue': 1000000,
    'profit': 200000,
    'assets': 1500000,
    'liabilities': 500000
}

company2 = {
    'revenue': 800000,
    'profit': 100000,
    'assets': 1200000,
    'liabilities': 400000
}

# Évaluer la fusion
result = evaluate_merger(company1, company2)
print(result)