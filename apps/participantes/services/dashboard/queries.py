"""
Agregações analíticas e otimização ORM para o Dashboard do SIPAC.
Executa consultas eficientes com aggregate(), annotate(), Count(distinct=True) e TruncMonth().
Retorna estruturas preparadas para consumo tanto por templates HTML quanto por gráficos Chart.js.
"""

from typing import Any
from django.db.models import Count, QuerySet
from django.db.models.functions import TruncMonth
from apps.participantes.models import (
    ComunidadeTradicional,
    Estado,
    Evento,
    FrenteResponsavel,
    Genero,
    Instituicao,
    MetaInterna,
    TipoParticipante,
)


class DashboardQueries:
    """
    Camada de consultas agregadas do Dashboard.
    Isola todas as operações de banco de dados e formatação analítica.
    """

    @staticmethod
    def get_kpis(qs: QuerySet) -> dict[str, Any]:
        """Calcula os indicadores macro (Cards de KPI)."""
        total_participacoes = qs.count()

        aggregates = qs.aggregate(
            pessoas=Count("pessoa_id", distinct=True),
            eventos=Count("evento_id", distinct=True),
        )
        total_pessoas = aggregates["pessoas"] or 0
        total_eventos = aggregates["eventos"] or 0

        # Instituições distintas envolvidas
        total_instituicoes = (
            qs.exclude(instituicao_id__isnull=True)
            .aggregate(total=Count("instituicao_id", distinct=True))["total"]
            or 0
        )

        # Média de participações por pessoa física
        media_participacoes = 0.0
        if total_pessoas > 0:
            media_participacoes = round(total_participacoes / total_pessoas, 2)

        return {
            "total_participacoes": total_participacoes,
            "total_pessoas_unicas": total_pessoas,
            "total_eventos": total_eventos,
            "total_instituicoes": total_instituicoes,
            "media_participacoes_por_pessoa": media_participacoes,
        }

    @staticmethod
    def get_distribuicao_genero(qs: QuerySet) -> dict[str, Any]:
        """Agrega participações por gênero do participante."""
        choices_map = dict(Genero.choices)
        data_rows = (
            qs.values("pessoa__genero")
            .annotate(total=Count("id"))
            .order_by("-total")
        )

        total_geral = sum(r["total"] for r in data_rows) or 1
        labels: list[str] = []
        data: list[int] = []
        percentages: list[float] = []

        for row in data_rows:
            raw_code = row["pessoa__genero"]
            label = choices_map.get(raw_code, raw_code or "Não Informado")
            val = row["total"]
            labels.append(label)
            data.append(val)
            percentages.append(round((val / total_geral) * 100, 1))

        return {
            "labels": labels,
            "data": data,
            "percentages": percentages,
        }

    @staticmethod
    def get_distribuicao_comunidade(qs: QuerySet) -> dict[str, Any]:
        """Agrega participações por pertencimento a comunidades tradicionais."""
        choices_map = dict(ComunidadeTradicional.choices)
        data_rows = (
            qs.values("pessoa__comunidade_tradicional")
            .annotate(total=Count("id"))
            .order_by("-total")
        )

        labels: list[str] = []
        data: list[int] = []
        for row in data_rows:
            raw_code = row["pessoa__comunidade_tradicional"]
            label = choices_map.get(raw_code, raw_code or "Não")
            labels.append(label)
            data.append(row["total"])

        return {
            "labels": labels,
            "data": data,
        }

    @staticmethod
    def get_distribuicao_estado(qs: QuerySet) -> dict[str, Any]:
        """Agrega participações por Estado (UF) do evento."""
        estado_labels = dict(Estado.choices)
        data_rows = (
            qs.values("evento__estado")
            .annotate(total=Count("id"))
            .order_by("-total")
        )

        total_geral = sum(r["total"] for r in data_rows) or 1
        labels: list[str] = []
        data: list[int] = []
        ranking: list[dict[str, Any]] = []

        for row in data_rows:
            uf = row["evento__estado"] or "NI"
            total = row["total"]
            nome_extenso = estado_labels.get(uf, uf)
            labels.append(uf)
            data.append(total)
            ranking.append(
                {
                    "uf": uf,
                    "nome": nome_extenso,
                    "total": total,
                    "percentual": round((total / total_geral) * 100, 1),
                }
            )

        return {
            "labels": labels,
            "data": data,
            "ranking": ranking,
        }

    @staticmethod
    def get_distribuicao_frente(qs: QuerySet) -> dict[str, Any]:
        """Agrega participações por Frente Responsável."""
        choices_map = dict(FrenteResponsavel.choices)
        data_rows = (
            qs.values("evento__frente_responsavel")
            .annotate(total=Count("id"))
            .order_by("-total")
        )

        labels: list[str] = []
        data: list[int] = []
        for row in data_rows:
            code = row["evento__frente_responsavel"]
            labels.append(choices_map.get(code, code or "-"))
            data.append(row["total"])

        return {
            "labels": labels,
            "data": data,
        }

    @staticmethod
    def get_distribuicao_meta(qs: QuerySet) -> dict[str, Any]:
        """Agrega participações por Meta Interna."""
        choices_map = dict(MetaInterna.choices)
        data_rows = (
            qs.values("evento__meta_interna")
            .annotate(total=Count("id"))
            .order_by("-total")
        )

        labels: list[str] = []
        data: list[int] = []
        for row in data_rows:
            code = row["evento__meta_interna"]
            labels.append(choices_map.get(code, code or "-"))
            data.append(row["total"])

        return {
            "labels": labels,
            "data": data,
        }

    @staticmethod
    def get_distribuicao_tipo_participante(qs: QuerySet) -> dict[str, Any]:
        """Agrega por tipo de participante (Produtor Rural, Técnico de ATER, Outros)."""
        choices_map = dict(TipoParticipante.choices)
        data_rows = (
            qs.values("tipo_participante")
            .annotate(total=Count("id"))
            .order_by("-total")
        )

        labels: list[str] = []
        data: list[int] = []
        for row in data_rows:
            code = row["tipo_participante"]
            labels.append(choices_map.get(code, code or "-"))
            data.append(row["total"])

        return {
            "labels": labels,
            "data": data,
        }

    @staticmethod
    def get_evolucao_temporal(qs: QuerySet) -> dict[str, Any]:
        """Agrega participações cronologicamente mês a mês."""
        data_rows = (
            qs.annotate(mes=TruncMonth("evento__data"))
            .values("mes")
            .annotate(total=Count("id"))
            .order_by("mes")
        )

        labels: list[str] = []
        data: list[int] = []
        for row in data_rows:
            mes_dt = row["mes"]
            if mes_dt:
                labels.append(mes_dt.strftime("%m/%Y"))
                data.append(row["total"])

        return {
            "labels": labels,
            "data": data,
        }

    @staticmethod
    def get_ranking_eventos(qs: QuerySet, limit: int = 5) -> list[dict[str, Any]]:
        """Retorna os eventos/atividades com maior volume de participações."""
        data_rows = (
            qs.values("evento__nome", "evento__estado", "evento__data")
            .annotate(total=Count("id"))
            .order_by("-total")[:limit]
        )
        ranking = []
        for r in data_rows:
            dt = r["evento__data"]
            data_str = dt.strftime("%d/%m/%Y") if dt else "-"
            ranking.append(
                {
                    "nome": r["evento__nome"],
                    "estado": r["evento__estado"],
                    "data": data_str,
                    "total": r["total"],
                }
            )
        return ranking

    @staticmethod
    def get_filter_options() -> dict[str, Any]:
        """Retorna opções disponíveis para preenchimento dos menus suspensos de filtro."""
        # Anos disponíveis a partir das datas dos eventos
        distinct_dates = Evento.objects.dates("data", "year", order="DESC")
        anos_disponiveis = [d.year for d in distinct_dates]

        # Top 100 instituições em ordem alfabética
        instituicoes_disponiveis = list(
            Instituicao.objects.order_by("nome").values_list("nome", flat=True)[:100]
        )

        return {
            "anos": anos_disponiveis,
            "estados": list(Estado.choices),
            "frentes": list(FrenteResponsavel.choices),
            "metas": list(MetaInterna.choices),
            "tipos_participante": list(TipoParticipante.choices),
            "generos": list(Genero.choices),
            "comunidades": list(ComunidadeTradicional.choices),
            "instituicoes": instituicoes_disponiveis,
        }
