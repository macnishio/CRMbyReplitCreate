# CRM Application

## Description
This is a comprehensive Customer Relationship Management (CRM) application built with Flask, SQLAlchemy, and PostgreSQL. It provides functionality for managing leads, opportunities, accounts, tasks, and schedules, as well as reporting and analytics features.

## Features
- User authentication and authorization
- Lead management with AI-powered scoring
- Opportunity tracking
- Account management
- Task management
- Scheduling
- Reporting and analytics
- Email integration for automated follow-ups
- Mobile-friendly interface

## Requirements
- Python 3.9+
- PostgreSQL
- See requirements.txt for Python package dependencies

## Installation
1. Clone the repository
2. Create a virtual environment: `python -m venv venv`
3. Activate the virtual environment:
   - On Windows: `venv\Scripts\activate`
   - On macOS and Linux: `source venv/bin/activate`
4. Install the required packages: `pip install -r requirements.txt`
5. Set up your environment variables in a `.env` file (see `.env.example` for required variables)
6. Initialize the database: `flask db upgrade`

## Running the Application
1. Ensure your virtual environment is activated
2. Run the application: `python app.py`
3. Access the application in your web browser at `http://localhost:5000`

## Deployment
This application is designed to be deployed on Replit. Follow these steps for deployment:
1. Create a new Repl and import this GitHub repository
2. In the Replit environment, set up the necessary environment variables
3. Install the required packages using the Replit package manager
4. Run the application using the command: `python app.py`

## Testing
To run the tests, use the following command:
```
python -m unittest discover tests
```

## Contributing
Please read CONTRIBUTING.md for details on our code of conduct and the process for submitting pull requests.

## License
This project is licensed under the MIT License - see the LICENSE.md file for details.

## Acknowledgments
- Flask framework
- SQLAlchemy ORM
- Chart.js for data visualization
- Bootstrap for responsive design

