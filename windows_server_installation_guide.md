# Windows Server Installation Guide for CRM Application

This guide will walk you through the process of installing and configuring the CRM application on a Windows server.

## Prerequisites

- Windows Server 2016 or later
- Administrator access to the server

## Step 1: Install Python

1. Download Python 3.9 or later from the official website: https://www.python.org/downloads/windows/
2. Run the installer and select "Add Python to PATH" during installation.
3. Open Command Prompt and verify the installation by running:
   ```
   python --version
   ```

## Step 2: Install PostgreSQL

1. Download PostgreSQL from the official website: https://www.postgresql.org/download/windows/
2. Run the installer and follow the prompts. Remember the password you set for the postgres user.
3. Add PostgreSQL bin directory to your system PATH (usually C:\Program Files\PostgreSQL\13\bin).

## Step 3: Create a Database

1. Open Command Prompt and connect to PostgreSQL:
   ```
   psql -U postgres
   ```
2. Create a new database for the CRM application:
   ```sql
   CREATE DATABASE crm_database;
   ```
3. Exit psql by typing `\q` and pressing Enter.

## Step 4: Set Up the Application

1. Clone or download the CRM application code to your server.
2. Navigate to the application directory in Command Prompt.
3. Create a virtual environment:
   ```
   python -m venv venv
   ```
4. Activate the virtual environment:
   ```
   venv\Scripts\activate
   ```
5. Install the required packages:
   ```
   pip install -r requirements.txt
   ```

## Step 5: Configure the Application

1. Create a `.env` file in the application directory with the following content:
   ```
   DATABASE_URL=postgresql://postgres:your_password@localhost/crm_database
   SECRET_KEY=your_secret_key
   MAIL_SERVER=your_mail_server
   MAIL_PORT=your_mail_port
   MAIL_USE_TLS=True
   MAIL_USERNAME=your_email@example.com
   MAIL_PASSWORD=your_email_password
   ```
   Replace the placeholders with your actual database and email configuration.

2. Initialize the database:
   ```
   flask db upgrade
   ```

## Step 6: Configure Email Settings

1. Set up an email account for sending automated follow-ups. You can use a Gmail account or any other email service that supports SMTP.
2. If using Gmail, you may need to create an "App Password" for increased security. Follow these steps:
   a. Go to your Google Account settings.
   b. Select "Security" on the left panel.
   c. Under "Signing in to Google," select "App Passwords."
   d. Generate a new App Password for "Mail" and "Windows Computer."
3. Update the `.env` file with your email settings:
   ```
   MAIL_SERVER=smtp.gmail.com
   MAIL_PORT=587
   MAIL_USE_TLS=True
   MAIL_USERNAME=your_email@gmail.com
   MAIL_PASSWORD=your_app_password
   ```
   Replace the placeholders with your actual email configuration.

## Step 7: Run the Application as a Windows Service

1. Install `nssm` (Non-Sucking Service Manager):
   - Download from https://nssm.cc/download
   - Extract the nssm.exe file to C:\Windows\System32

2. Open Command Prompt as Administrator and run:
   ```
   nssm install CRMService
   ```

3. In the NSSM service installer:
   - Set the "Path" to your Python executable in the virtual environment (e.g., C:\path\to\your\app\venv\Scripts\python.exe)
   - Set the "Startup directory" to your application directory
   - Set "Arguments" to "app.py"
   - Click "Install service"

4. Start the service:
   ```
   nssm start CRMService
   ```

## Step 8: Configure IIS as a Reverse Proxy (Optional)

If you want to use IIS as a reverse proxy to handle HTTPS:

1. Install IIS and URL Rewrite Module.
2. Create a new website in IIS Manager.
3. Set up URL Rewrite rules to forward requests to your Flask application.

## Troubleshooting

- Check the Windows Event Viewer for any error logs related to the CRMService.
- Ensure all environment variables are correctly set.
- Verify that the PostgreSQL service is running.
- If emails are not being sent, double-check your email configuration and ensure that your email provider allows sending emails through SMTP.

For any additional support, please contact our technical support team.
