SPAM DETECTOR API
=================

A Django REST API for identifying spam phone numbers and managing contacts.

PREREQUISITES
-------------
- Python 3.8+
- MySQL 8.0+
- pip

INSTALLATION
------------
1. Download the zip file:
   drive link : 

3. Install dependencies:
   pip install -r requirements.txt

4. Set up MySQL database:
   DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.mysql',
        'NAME': 'Database_Name',
        'USER': 'User_Name',
        'PASSWORD': 'Password',
        'HOST': 'localhost',
        'PORT': '3306',
    }
}


RUNNING THE APPLICATION
----------------------
1. Apply migrations:
   python manage.py makemigrations
   python manage.py migrate

3. Run development server:
   python manage.py runserver

4. Access API at:
   http://localhost:8000/api/

API ENDPOINTS
-------------
- POST   /api/auth/register/      User registration
- POST   /api/auth/login/         User login
- GET    /api/contacts/           List contacts
- POST   /api/contacts/           Create contact
- POST   /api/contacts/bulk_create/ Bulk create
- GET    /api/spam-reports/       List spam reports
- POST   /api/spam-reports/       Report spam
- GET    /api/search/             Search by name
- GET    /api/search/phone/       Search by phone


TROUBLESHOOTING
--------------
- MySQL issues: add proper credieantials in spam_detector/setting.py file
- Migration errors: Run makemigrations first
- Auth problems: Check tokens/cookies


