"""
Configurações para ambiente de Desenvolvimento Local do SIPAC.
DEBUG ativo, SQLite por padrão com chave de alternância para PostgreSQL via .env.
"""

import os
from .base import *

# Chave Secreta
SECRET_KEY = os.getenv(
    "SECRET_KEY",
    "django-insecure-sipac-local-dev-key-change-in-production",
)

# Debug Ativo
DEBUG = os.getenv("DEBUG", "True").lower() in ("true", "1", "yes")

# Hosts Permitidos
ALLOWED_HOSTS = [
    host.strip()
    for host in os.getenv("ALLOWED_HOSTS", "localhost,127.0.0.1").split(",")
    if host.strip()
]
if "testserver" not in ALLOWED_HOSTS:
    ALLOWED_HOSTS.append("testserver")

# Origens confiáveis para CSRF (essencial para testes via IP público HTTP)
raw_csrf = os.getenv("CSRF_TRUSTED_ORIGINS", "")
if raw_csrf:
    CSRF_TRUSTED_ORIGINS = [origin.strip() for origin in raw_csrf.split(",") if origin.strip()]
else:
    CSRF_TRUSTED_ORIGINS = [
        f"http://{host}"
        for host in ALLOWED_HOSTS
        if host not in ("localhost", "127.0.0.1", "testserver") and not host.startswith("*")
    ]



# Banco de Dados
# Padrão: SQLite local. Alternável para PostgreSQL caso DB_ENGINE=postgres no .env
if os.getenv("DB_ENGINE") == "postgres":
    DATABASES = {
        "default": {
            "ENGINE": "django.db.backends.postgresql",
            "NAME": os.getenv("DB_NAME", "sipac_db"),
            "USER": os.getenv("DB_USER", "sipac_user"),
            "PASSWORD": os.getenv("DB_PASSWORD", "sipac_password"),
            "HOST": os.getenv("DB_HOST", "localhost"),
            "PORT": os.getenv("DB_PORT", "5432"),
        }
    }
else:
    DATABASES = {
        "default": {
            "ENGINE": "django.db.backends.sqlite3",
            "NAME": BASE_DIR / "db.sqlite3",
        }
    }

# Email em console para desenvolvimento
EMAIL_BACKEND = "django.core.mail.backends.console.EmailBackend"
