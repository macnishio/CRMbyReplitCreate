# Ubuntu Linux Installation Guide for CRM Application

This guide will walk you through the process of installing and configuring the CRM application on an Ubuntu Linux server.

## Prerequisites

- Ubuntu 20.04 LTS or later
- Sudo access to the server

## Step 1: Update System Packages

1. Open a terminal and update the package list:
   ```
   sudo apt update
   ```
2. Upgrade the installed packages:
   ```
   sudo apt upgrade -y
   ```

## Step 2: Install Python

1. Install Python 3 and pip:
   ```
   sudo apt install python3 python3-pip -y
   ```
2. Verify the installation:
   ```
   python3 --version
   pip3 --version
   ```

## Step 3: Install PostgreSQL

1. Install PostgreSQL:
   ```
   sudo apt install postgresql postgresql-contrib -y
   ```
2. Start the PostgreSQL service:
   ```
   sudo systemctl start postgresql
   sudo systemctl enable postgresql
   ```

## Step 4: Create a Database

1. Switch to the postgres user:
   ```
   sudo -i -u postgres
   ```
2. Create a new database for the CRM application:
   ```
   createdb crm_database
   ```
3. Exit the postgres user session:
   ```
   exit
   ```

## Step 5: Set Up the Application

1. Clone or download the CRM application code to your server.
2. Navigate to the application directory in the terminal.
3. Install the required packages:
   ```
   pip3 install -r requirements.txt
   ```

## Step 6: Configure the Application

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

## Step 7: Configure Email Settings

1. Set up an email account for sending automated follow-ups. You can use a Gmail account or any other email service that supports SMTP.
2. If using Gmail, you may need to create an "App Password" for increased security. Follow these steps:
   a. Go to your Google Account settings.
   b. Select "Security" on the left panel.
   c. Under "Signing in to Google," select "App Passwords."
   d. Generate a new App Password for "Mail" and "Other (Custom name)."
3. Update the `.env` file with your email settings:
   ```
   MAIL_SERVER=smtp.gmail.com
   MAIL_PORT=587
   MAIL_USE_TLS=True
   MAIL_USERNAME=your_email@gmail.com
   MAIL_PASSWORD=your_app_password
   ```
   Replace the placeholders with your actual email configuration.

## Step 8: Run the Application

1. Start the application:
   ```
   python3 app.py
   ```

## Step 9: Set Up a Systemd Service (Optional)

To run the application as a service:

1. Create a new service file:
   ```
   sudo nano /etc/systemd/system/crm.service
   ```
2. Add the following content:
   ```
   [Unit]
   Description=CRM Application
   After=network.target

   [Service]
   User=your_username
   WorkingDirectory=/path/to/your/app
   ExecStart=/usr/bin/python3 /path/to/your/app/app.py
   Restart=always

   [Install]
   WantedBy=multi-user.target
   ```
   Replace `your_username` and `/path/to/your/app` with the appropriate values.

3. Save the file and exit the editor.
4. Reload the systemd daemon:
   ```
   sudo systemctl daemon-reload
   ```
5. Start the service:
   ```
   sudo systemctl start crm
   ```
6. Enable the service to start on boot:
   ```
   sudo systemctl enable crm
   ```

## Step 10: Set Up Nginx as a Reverse Proxy (Optional)

If you want to use Nginx as a reverse proxy to handle HTTPS:

1. Install Nginx:
   ```
   sudo apt install nginx -y
   ```
2. Create a new Nginx configuration file:
   ```
   sudo nano /etc/nginx/sites-available/crm
   ```
3. Add the following content:
   ```
   server {
       listen 80;
       server_name your_domain.com;

       location / {
           proxy_pass http://localhost:5000;
           proxy_set_header Host $host;
           proxy_set_header X-Real-IP $remote_addr;
       }
   }
   ```
   Replace `your_domain.com` with your actual domain name.

4. Create a symbolic link to enable the site:
   ```
   sudo ln -s /etc/nginx/sites-available/crm /etc/nginx/sites-enabled
   ```
5. Test the Nginx configuration:
   ```
   sudo nginx -t
   ```
6. If the test is successful, restart Nginx:
   ```
   sudo systemctl restart nginx
   ```

## Troubleshooting

- Check the application logs for any error messages.
- Ensure all environment variables are correctly set in the `.env` file.
- Verify that the PostgreSQL service is running:
  ```
  sudo systemctl status postgresql
  ```
- If emails are not being sent, double-check your email configuration and ensure that your email provider allows sending emails through SMTP.

For any additional support, please contact our technical support team.
