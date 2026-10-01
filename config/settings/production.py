"""
Configurações para ambiente de Produção do SIPAC.
DEBUG desligado, PostgreSQL mandatório e cabeçalhos de segurança ativados.
"""

import os
from .base import *

DEBUG = False

SECRET_KEY = os.environ.get("SECRET_KEY")
if not SECRET_KEY:
    raise ValueError("A variável de ambiente SECRET_KEY é obrigatória em ambiente de produção.")

raw_hosts = os.environ.get("ALLOWED_HOSTS", "")
ALLOWED_HOSTS = [host.strip() for host in raw_hosts.split(",") if host.strip()]
if not ALLOWED_HOSTS:
    raise ValueError("ALLOWED_HOSTS deve conter ao menos um host válido em produção.")

# Banco de Dados de Produção: PostgreSQL
DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.postgresql",
        "NAME": os.environ.get("DB_NAME", "sipac_db"),
        "USER": os.environ.get("DB_USER", "sipac_user"),
        "PASSWORD": os.environ.get("DB_PASSWORD", ""),
        "HOST": os.environ.get("DB_HOST", "localhost"),
        "PORT": os.environ.get("DB_PORT", "5432"),
    }
}

# Segurança de Cookies e Conexão HTTPS
CSRF_COOKIE_SECURE = True
SESSION_COOKIE_SECURE = True
SECURE_BROWSER_XSS_FILTER = True
SECURE_CONTENT_TYPE_NOSNIFF = True
X_FRAME_OPTIONS = "DENY"

# HTTP Strict Transport Security (HSTS)
SECURE_HSTS_SECONDS = 31536000
SECURE_HSTS_INCLUDE_SUBDOMAINS = True
SECURE_HSTS_PRELOAD = True
