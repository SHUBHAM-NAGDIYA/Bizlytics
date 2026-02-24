import os
import dj_database_url
#SECRET_KEY = os.environ.get('J-2F5WVva_U4Hp0Geki_TE2SM0d04gurUlLe62NclCF1ixUcZmN5tIGmmOMnxg1Bafg')
SECRET_KEY = os.environ.get("SECRET_KEY")
DEBUG = os.environ.get("DEBUG", "False") == "True"
ROOT_URLCONF = 'main.urls'
ALLOWED_HOSTS = os.environ.get("ALLOWED_HOSTS", "").split(",")

DATABASES = {
    "default": dj_database_url.config(
        default=os.environ.get("DATABASE_URL"),
        conn_max_age=600
    )
}
