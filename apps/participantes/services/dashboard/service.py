"""
Serviço central do Dashboard Analítico do SIPAC.
Orquestra a aplicação de filtros analíticos e consolida os dados para renderização
gráfica (Chart.js via json_script) e indicadores gerenciais (KPIs).
"""

from typing import Any
from apps.participantes.models import Participacao
from .filters import DashboardFilter
from .queries import DashboardQueries


class DashboardService:
    """
    Fachada para fornecimento de inteligência analítica do SIPAC.
    """

    def __init__(self, queries: DashboardQueries | None = None):
        self.queries = queries or DashboardQueries()

    def get_dashboard_data(
        self,
        filter_dto: DashboardFilter | None = None,
    ) -> dict[str, Any]:
        """
        Consolida todas as métricas, gráficos e opções de filtro para uma determinada combinação de parâmetros.
        """
        filters = filter_dto or DashboardFilter()

        # Queryset base com select_related para evitar queries N+1
        base_qs = Participacao.objects.select_related("pessoa", "evento", "instituicao")
        filtered_qs = filters.apply(base_qs)

        # 1. KPIs Estratégicos
        kpis = self.queries.get_kpis(filtered_qs)

        # 2. Distribuições e Dimensões
        dist_genero = self.queries.get_distribuicao_genero(filtered_qs)
        dist_comunidade = self.queries.get_distribuicao_comunidade(filtered_qs)
        dist_estado = self.queries.get_distribuicao_estado(filtered_qs)
        dist_frente = self.queries.get_distribuicao_frente(filtered_qs)
        dist_meta = self.queries.get_distribuicao_meta(filtered_qs)
        dist_tipo = self.queries.get_distribuicao_tipo_participante(filtered_qs)
        evolucao_temporal = self.queries.get_evolucao_temporal(filtered_qs)
        ranking_eventos = self.queries.get_ranking_eventos(filtered_qs, limit=5)

        # 3. Opções para os formulários de filtro
        filter_options = self.queries.get_filter_options()

        # 4. Estrutura de dados compacta para os gráficos Chart.js (serializável em JSON)
        charts_data = {
            "genero": dist_genero,
            "comunidade": dist_comunidade,
            "estado": {
                "labels": dist_estado["labels"],
                "data": dist_estado["data"],
            },
            "frente": dist_frente,
            "meta": dist_meta,
            "tipo_participante": dist_tipo,
            "evolucao": evolucao_temporal,
        }

        return {
            "kpis": kpis,
            "ranking_estados": dist_estado.get("ranking", []),
            "ranking_eventos": ranking_eventos,
            "charts_data": charts_data,
            "filter_options": filter_options,
            "filters": filters,
            "is_filtered": filters.is_active,
        }
