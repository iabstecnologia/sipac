import sys
import django
from django.conf import settings
from django.views.generic import TemplateView


class HomeView(TemplateView):
    """
    View temporária de boas-vindas e diagnóstico de integridade da infraestrutura (Fase 1).
    Será substituída pelo DashboardView na Fase 5.
    """

    template_name = "participantes/home.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        db_conf = settings.DATABASES.get("default", {})
        db_engine = db_conf.get("ENGINE", "").split(".")[-1]

        context.update(
            {
                "django_version": django.__version__,
                "python_version": f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}",
                "debug_mode": settings.DEBUG,
                "db_engine": db_engine,
                "db_name": str(db_conf.get("NAME", "")).split("/")[-1],
                "system_status": "Operacional",
            }
        )
        return context
