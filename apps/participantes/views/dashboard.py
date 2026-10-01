"""
Controlador analítico do Dashboard do SIPAC.
Renderiza os indicadores consolidados (KPIs, gráficos interativos e rankings)
baseados nos filtros selecionados pelo usuário.
"""

from typing import Any
from django.views.generic import TemplateView
from apps.participantes.services.dashboard import (
    DashboardFilter,
    DashboardService,
)


class DashboardView(TemplateView):
    """
    CBV responsável pela renderização do painel analítico principal do SIPAC.
    """

    template_name = "participantes/dashboard/index.html"

    def get_context_data(self, **kwargs: Any) -> dict[str, Any]:
        context = super().get_context_data(**kwargs)

        # 1. Captura e sanitização dos filtros HTTP
        filters = DashboardFilter.from_request(self.request)

        # 2. Consolidação de métricas e gráficos via Service
        service = DashboardService()
        dashboard_data = service.get_dashboard_data(filters)

        # 3. Injeção no contexto do template
        context.update(dashboard_data)
        context["current_query_string"] = filters.as_query_string()

        return context
