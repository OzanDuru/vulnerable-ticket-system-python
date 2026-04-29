# Vulnerable Ticket System (Flask + Docker)

This is an intentionally vulnerable support ticket lab app for security training.

Warning:
- Do not deploy to the internet.
- Use only in isolated lab environments.

## Included Vulnerabilities

- Stored XSS in admin ticket view
- Weak authentication (admin/password, plaintext storage)
- Unrestricted file upload
- RCE flow by executing uploaded Python files

## Project Structure

- app.py
- init_db.py
- requirements.txt
- Dockerfile
- docker-compose.yml
- templates/
- static/
- uploads/
- data/

## Run With Docker Compose

1. Open terminal in this folder.
2. Build and start:

   docker compose up --build

3. Open:
- http://localhost:5000/
- http://localhost:5000/admin/login

4. Admin credentials:
- username: admin
- password: password

5. Stop:

   docker compose down

Notes:
- Uploaded files are persisted in uploads/
- SQLite database is persisted in data/tickets.db

## Run Without Docker (Optional)

1. Install dependencies:

   pip install -r requirements.txt

2. Initialize DB (optional):

   python init_db.py

3. Run app:

   python app.py

## Example Script for Upload Testing

A sample shell.py is included. In the admin file manager, upload shell.py and use Run to pass a command argument.
