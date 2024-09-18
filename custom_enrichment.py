import random

def enrich_lead_data(email):
    # This function simulates enriching lead data
    # In a real scenario, this would call an actual API
    
    # Generate mock data
    industries = ['Technology', 'Finance', 'Healthcare', 'Education', 'Retail']
    job_titles = ['Manager', 'Director', 'CEO', 'CTO', 'Developer']
    
    domain = email.split('@')[1]
    company_name = domain.split('.')[0].capitalize()
    
    enriched_data = {
        'full_name': f"{email.split('@')[0].replace('.', ' ').title()}",
        'job_title': random.choice(job_titles),
        'company_name': company_name,
        'company_domain': domain,
        'company_industry': random.choice(industries),
        'company_employee_count': random.randint(10, 1000)
    }
    
    return enriched_data

# Example usage
if __name__ == "__main__":
    test_email = "john.doe@example.com"
    result = enrich_lead_data(test_email)
    print(f"Enriched data for {test_email}:")
    for key, value in result.items():
        print(f"{key}: {value}")
