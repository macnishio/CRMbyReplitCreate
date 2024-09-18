import os
import clearbit
from flask import current_app

clearbit.key = os.environ.get('CLEARBIT_API_KEY')

def enrich_lead_data(email):
    try:
        person = clearbit.Person.find(email=email, stream=True)
        company = clearbit.Company.find(domain=email.split('@')[1], stream=True)
        
        enriched_data = {
            'full_name': person['name']['fullName'] if person and 'name' in person else None,
            'job_title': person['employment']['title'] if person and 'employment' in person else None,
            'company_name': company['name'] if company else None,
            'company_domain': company['domain'] if company else None,
            'company_industry': company['category']['industry'] if company and 'category' in company else None,
            'company_employee_count': company['metrics']['employees'] if company and 'metrics' in company else None,
        }
        return enriched_data
    except Exception as e:
        current_app.logger.error(f"Error enriching lead data: {str(e)}")
        return {}
