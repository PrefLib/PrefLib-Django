import os

## Write the settings.py file that we do not git for security reasons
with open("preflib/local_settings.py", "w") as f:
    f.write("""
import os

# Build paths inside the project like this: os.path.join(BASE_DIR, ...)
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = 'thisissecret'

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = True

ALLOWED_HOSTS = []

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': os.path.join(BASE_DIR, 'preflib.db'),
    }
}

CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.filebased.FileBasedCache',
        'LOCATION': os.path.join(BASE_DIR, 'cache/'),
        'TIMEOUT': str(60 * 60 * 12)
    }
}

STATIC_ROOT = "static/"

# Path to the unix convert command for the image handling
CONVERT_PATH = 'convert'
""")
    f.close()

## Create the migration folder and run the initial migration to set up the
## database (a simple SQLlite db here since it should be only use to play around).
try:
    os.makedirs(os.path.join("preflibApp", "migrations"))
except:
    pass
with open(os.path.join("preflibApp", "migrations", "__init__.py"), "w") as f:
    f.write("")
    f.close()

os.system("python3 manage.py makemigrations")
os.system("python3 manage.py migrate")

## Initialize the website
os.system("python3 manage.py initializedb")
os.system("python3 manage.py updatepapers")
os.system("python3 manage.py collectstatic")

## Set everything up to add data
try:
    os.makedirs(os.path.join("preflibApp", "static", "datatoadd"))
except:
    pass
