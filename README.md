ShareHub - Community Item Donation and Exchange Platform
ShareHub is a community platform that allows people to donate items they no longer need or exchange items with their neighbors. Instead of usable items going to waste or being thrown away, people can post them online for others in the community to find, request, and pick up. It's completely free and focused on helping neighbors share resources.
 
Feature List
Landing Page
- Clear business introduction and purpose
- Donate, Exchange, and Community sections
- Working navigation to Browse, Login, and Register
- Responsive design — works on mobile and desktop
Users
- Register with Username, email, and password
- Login with Username or email and password
- Logout securely end your session
- Passwords are securely hashed never stored in plain text
- Protected pages - some pages require you to be logged in
- Ownership rules - you can only edit or delete your own items
- Personalized dashboard showing your listings and requests
CRUD
Create - Post a new item with title, description, category, condition, type, and photo
Read - Browse all items, view item details, search by keyword, filter by category/condition/type
Update - Edit your own item listings
Delete - Remove your own items from the platform
 
Tech Stack Used
Programming Language: Python 3.11+
Web Framework: Flask 3
Database: SQLite with Flask-SQLAlchemy
Authentication: Flask-Login, Werkzeug Security (password hashing)
Forms & Validation:  Flask-WTF, CSRF protection
Frontend: HTML5, Jinja2 Templates, Bootstrap 5
File Storage: Local `uploads/` folder for item images
 
Demo Login
Username: alice
Password: sharehub123
Username: bob
Password: sharehub123
 
How to Run
1. Create virtual environment: python -m venv venv
2. Activate: source venv/bin/activate, (Linux/Mac) or venv\Scripts\activate, (Windows)
3. Install dependencies: pip install -r requirements.txt
4. Load sample data: python seed.py
5. Run the app: python app.py
6. Visit: http://127.0.0.1:5000