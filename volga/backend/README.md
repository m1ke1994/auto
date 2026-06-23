# Backend Docker prerequisites

To run the backend container, place your Django project in this folder with at least:

- `requirements.txt`
- `manage.py`
- `config/settings.py`
- `config/wsgi.py`

Add this snippet to `config/settings.py` for Docker:

```python
import os

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.postgresql",
        "NAME": os.getenv("DB_NAME", "volga"),
        "USER": os.getenv("DB_USER", "volga"),
        "PASSWORD": os.getenv("DB_PASSWORD", "volga"),
        "HOST": os.getenv("DB_HOST", "db"),
        "PORT": os.getenv("DB_PORT", "5432"),
    }
}

ALLOWED_HOSTS = ["*"]
CORS_ALLOW_ALL_ORIGINS = True
```
