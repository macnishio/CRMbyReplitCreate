import numpy as np
from sklearn.preprocessing import StandardScaler
from sklearn.ensemble import RandomForestClassifier
from models import Lead, Opportunity

def calculate_lead_score(lead):
    # Simple scoring based on lead attributes
    score = 0
    if lead.status == 'Qualified':
        score += 30
    elif lead.status == 'Contacted':
        score += 20
    elif lead.status == 'New':
        score += 10
    
    # Add more scoring criteria as needed
    
    return min(score, 100)  # Ensure score doesn't exceed 100

def train_lead_scoring_model(leads):
    # Prepare features and labels
    X = []
    y = []
    for lead in leads:
        features = [
            1 if lead.status == 'Qualified' else 0,
            1 if lead.status == 'Contacted' else 0,
            1 if lead.status == 'New' else 0,
            # Add more features as needed
        ]
        X.append(features)
        y.append(1 if any(opp.stage == 'Closed Won' for opp in lead.opportunities) else 0)
    
    X = np.array(X)
    y = np.array(y)
    
    # Normalize features
    scaler = StandardScaler()
    X_scaled = scaler.fit_transform(X)
    
    # Train model
    model = RandomForestClassifier(n_estimators=100, random_state=42)
    model.fit(X_scaled, y)
    
    return model, scaler

def predict_lead_score(model, scaler, lead):
    features = [
        1 if lead.status == 'Qualified' else 0,
        1 if lead.status == 'Contacted' else 0,
        1 if lead.status == 'New' else 0,
        # Add more features as needed
    ]
    X = np.array([features])
    X_scaled = scaler.transform(X)
    score = model.predict_proba(X_scaled)[0][1] * 100
    return round(score, 2)

def get_conversion_rate():
    total_leads = Lead.query.count()
    converted_leads = Opportunity.query.filter_by(stage='Closed Won').count()
    if total_leads > 0:
        return (converted_leads / total_leads) * 100
    return 0

def get_average_deal_size():
    closed_won_opportunities = Opportunity.query.filter_by(stage='Closed Won').all()
    if closed_won_opportunities:
        total_amount = sum(opp.amount for opp in closed_won_opportunities)
        return total_amount / len(closed_won_opportunities)
    return 0

def get_sales_pipeline_value():
    open_opportunities = Opportunity.query.filter(Opportunity.stage != 'Closed Won', Opportunity.stage != 'Closed Lost').all()
    return sum(opp.amount for opp in open_opportunities)
