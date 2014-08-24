import os

# Running on App Enginge
PRODUCTION = os.environ.get('DATABASE_URL')
# Running Localy
DEVELOPMENT = not PRODUCTION
# You decide when is DEBUG mode, usually when running locally
DEBUG = True
