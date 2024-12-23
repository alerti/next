import os

# Flask basic settings
DEBUG = True
SECRET_KEY = os.environ.get('SECRET_KEY', 'change_this_please')

# Flask-Security configuration
SECURITY_PASSWORD_SALT = os.environ.get('SECURITY_PASSWORD_SALT', 's3cr3tS@lt')
SECURITY_REGISTERABLE = True
SECURITY_RECOVERABLE = True
SECURITY_TRACKABLE = True
SECURITY_CONFIRMABLE = False
SECURITY_SEND_REGISTER_EMAIL = False


DB_USER = os.environ.get('DB_USER', 'nexusfp')
DB_PASS = os.environ.get('DB_PASS', 'nexusrfp')
DB_HOST = os.environ.get('DB_HOST', 'localhost')
DB_PORT = os.environ.get('DB_PORT', '5432')
DB_NAME = os.environ.get('DB_NAME', 'nexusrfp')

SQLALCHEMY_DATABASE_URI = (
 f'postgresql://{DB_USER}:{DB_PASS}@{DB_HOST}:{DB_PORT}/{DB_NAME}'
)
SQLALCHEMY_TRACK_MODIFICATIONS = False

# Flask-Admin settings
FLASK_ADMIN_SWATCH = 'cerulean'
