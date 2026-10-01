"""
Serviço de Segmentação de Participantes do SIPAC.
Implementa a regra de negócio de exclusão sequencial por CPF (pessoa_id)
e recálculo integral de indicadores e gráficos por segmento.
"""

from typing import Any
from django.db.models import Count
from apps.participantes.models import (
    ComunidadeTradicional,
    Estado,
    FrenteResponsavel,
    Genero,
    MetaInterna,
    Participacao,
)
from apps.participantes.services.dashboard.filters import DashboardFilter
from apps.participantes.services.dashboard.queries import DashboardQueries
from .dtos import (
    SegmentDefinition,
    SegmentKPIs,
    SegmentResult,
    SegmentationAnalysisResult,
)


class SegmentacaoService:
    """
    Orquestra a análise multissegmentada de participantes,
    garantindo que cada Pessoa (CPF) pertença unicamente ao primeiro segmento elegível.
    """

    def __init__(self, queries: DashboardQueries | None = None):
        self.queries = queries or DashboardQueries()

    @staticmethod
    def get_default_segments() -> list[SegmentDefinition]:
        """
        Retorna uma configuração padrão de segmentos orientada a casos reais de uso.
        """
        return [
            SegmentDefinition(
                id="seg_1",
                name="Dias de Campo",
                order=1,
                filters=DashboardFilter(
                    tipo_participante="PRODUTOR_RURAL",
                    meta="DCS",
                ),
            ),
            SegmentDefinition(
                id="seg_2",
                name="Cursos Presenciais / ATECs",
                order=2,
                filters=DashboardFilter(
                    tipo_participante="PRODUTOR_RURAL",
                    meta="FORMACAO_ATECS",
                ),
            ),
            SegmentDefinition(
                id="seg_3",
                name="Encontros Temáticos e Seminários",
                order=3,
                filters=DashboardFilter(
                    tipo_participante="PRODUTOR_RURAL",
                    meta="ENCONTROS_TEMATICOS",
                ),
            ),
        ]

    def run_segmentation(
        self,
        segments_input: list[dict[str, Any] | SegmentDefinition],
    ) -> SegmentationAnalysisResult:
        """
        Executa a segmentação sequencial no banco de dados.

        Algoritmo:
        R_1 = A_1
        R_k = A_k - (R_1 ∪ R_2 ∪ ... ∪ R_{k-1})
        """
        # 1. Normalizar e ordenar segmentos por prioridade
        definitions: list[SegmentDefinition] = []
        for idx, item in enumerate(segments_input, start=1):
            if isinstance(item, SegmentDefinition):
                definitions.append(item)
            elif isinstance(item, dict):
                definitions.append(SegmentDefinition.from_dict(item, default_order=idx))

        definitions.sort(key=lambda s: s.order)

        # Se não foram fornecidos segmentos, retorna padrão
        if not definitions:
            definitions = self.get_default_segments()

        # 2. Processar cada segmento sequencialmente mantendo subqueries dos anteriores
        previous_subqueries: list[Any] = []
        results: list[SegmentResult] = []
        total_unique_participants = 0
        total_participations = 0

        for segment in definitions:
            base_qs = Participacao.objects.select_related("pessoa", "evento", "instituicao")
            raw_qs = segment.filters.apply(base_qs)

            # Participantes brutos antes da exclusão
            raw_people_qs = raw_qs.values("pessoa_id").distinct()
            raw_participants_count = raw_people_qs.count()

            # Aplicação da exclusão sequencial no banco de dados
            effective_qs = raw_qs
            for prev_sq in previous_subqueries:
                effective_qs = effective_qs.exclude(pessoa_id__in=prev_sq)

            # Participantes e participações efetivas
            effective_people_qs = effective_qs.values("pessoa_id").distinct()
            effective_participants_count = effective_people_qs.count()
            excluded_participants_count = max(0, raw_participants_count - effective_participants_count)
            effective_participations_count = effective_qs.count()

            # Adiciona os participantes deste segmento à lista de exclusão dos próximos
            previous_subqueries.append(effective_people_qs)

            # Construção de KPIs e Gráficos
            if effective_participants_count == 0:
                kpis = SegmentKPIs(
                    raw_participants=raw_participants_count,
                    excluded_participants=excluded_participants_count,
                    participants=0,
                    participations=0,
                    eventos=0,
                    instituicoes=0,
                    media_participacoes=0.0,
                )
                charts_data = self._build_empty_charts_data()
                ranking_eventos: list[dict[str, Any]] = []
                is_empty = True
            else:
                aggregates = effective_qs.aggregate(
                    eventos=Count("evento_id", distinct=True),
                )
                total_eventos = aggregates["eventos"] or 0
                total_instituicoes = (
                    effective_qs.exclude(instituicao_id__isnull=True)
                    .aggregate(total=Count("instituicao_id", distinct=True))["total"]
                    or 0
                )
                media = (
                    round(effective_participations_count / effective_participants_count, 2)
                    if effective_participants_count > 0
                    else 0.0
                )

                kpis = SegmentKPIs(
                    raw_participants=raw_participants_count,
                    excluded_participants=excluded_participants_count,
                    participants=effective_participants_count,
                    participations=effective_participations_count,
                    eventos=total_eventos,
                    instituicoes=total_instituicoes,
                    media_participacoes=media,
                )

                charts_data = self._build_segment_charts_data(effective_qs)
                ranking_eventos = self._build_segment_ranking(effective_qs, limit=5)
                is_empty = False

                total_unique_participants += effective_participants_count
                total_participations += effective_participations_count

            results.append(
                SegmentResult(
                    definition=segment,
                    kpis=kpis,
                    charts_data=charts_data,
                    ranking_eventos=ranking_eventos,
                    is_empty=is_empty,
                )
            )

        return SegmentationAnalysisResult(
            segments=results,
            total_unique_participants_allocated=total_unique_participants,
            total_participations_allocated=total_participations,
            total_segments=len(results),
        )

    def _build_segment_charts_data(self, effective_qs) -> dict[str, Any]:
        """
        Gera os datasets dos gráficos com base estrita no conjunto efetivo.
        Distribuições de perfil (gênero, comunidade, UF) contam pessoas distintas,
        garantindo conformidade exata com o total de participantes efetivos.
        """
        # 1. Gênero (distinct pessoa_id)
        genero_map = dict(Genero.choices)
        genero_rows = (
            effective_qs.values("pessoa__genero")
            .annotate(total=Count("pessoa_id", distinct=True))
            .order_by("-total")
        )
        total_genero = sum(r["total"] for r in genero_rows) or 1
        genero_labels: list[str] = []
        genero_data: list[int] = []
        genero_percentages: list[float] = []
        for r in genero_rows:
            label = genero_map.get(r["pessoa__genero"], r["pessoa__genero"] or "Não Informado")
            val = r["total"]
            genero_labels.append(label)
            genero_data.append(val)
            genero_percentages.append(round((val / total_genero) * 100, 1))

        # 2. Comunidade Tradicional (distinct pessoa_id)
        comunidade_map = dict(ComunidadeTradicional.choices)
        comunidade_rows = (
            effective_qs.values("pessoa__comunidade_tradicional")
            .annotate(total=Count("pessoa_id", distinct=True))
            .order_by("-total")
        )
        comunidade_labels: list[str] = []
        comunidade_data: list[int] = []
        for r in comunidade_rows:
            label = comunidade_map.get(
                r["pessoa__comunidade_tradicional"],
                r["pessoa__comunidade_tradicional"] or "Não",
            )
            comunidade_labels.append(label)
            comunidade_data.append(r["total"])

        # 3. Estado (UF) do participante nos eventos (distinct pessoa_id)
        estado_map = dict(Estado.choices)
        estado_rows = (
            effective_qs.values("evento__estado")
            .annotate(total=Count("pessoa_id", distinct=True))
            .order_by("-total")
        )
        estado_labels: list[str] = []
        estado_data: list[int] = []
        for r in estado_rows:
            uf = r["evento__estado"] or "NI"
            estado_labels.append(uf)
            estado_data.append(r["total"])

        # 4. Meta Interna (contagem de participações efetivas)
        meta_map = dict(MetaInterna.choices)
        meta_rows = (
            effective_qs.values("evento__meta_interna")
            .annotate(total=Count("id"))
            .order_by("-total")
        )
        meta_labels: list[str] = []
        meta_data: list[int] = []
        for r in meta_rows:
            code = r["evento__meta_interna"]
            meta_labels.append(meta_map.get(code, code or "-"))
            meta_data.append(r["total"])

        # 5. Frente de Atuação (contagem de participações efetivas)
        frente_map = dict(FrenteResponsavel.choices)
        frente_rows = (
            effective_qs.values("evento__frente_responsavel")
            .annotate(total=Count("id"))
            .order_by("-total")
        )
        frente_labels: list[str] = []
        frente_data: list[int] = []
        for r in frente_rows:
            code = r["evento__frente_responsavel"]
            frente_labels.append(frente_map.get(code, code or "-"))
            frente_data.append(r["total"])

        return {
            "genero": {
                "labels": genero_labels,
                "data": genero_data,
                "percentages": genero_percentages,
            },
            "comunidade": {
                "labels": comunidade_labels,
                "data": comunidade_data,
            },
            "estado": {
                "labels": estado_labels,
                "data": estado_data,
            },
            "meta": {
                "labels": meta_labels,
                "data": meta_data,
            },
            "frente": {
                "labels": frente_labels,
                "data": frente_data,
            },
        }

    def _build_segment_ranking(self, effective_qs, limit: int = 5) -> list[dict[str, Any]]:
        """Top eventos com maior volume de participações do segmento efetivo."""
        rows = (
            effective_qs.values("evento__nome", "evento__estado", "evento__data")
            .annotate(total=Count("id"))
            .order_by("-total")[:limit]
        )
        ranking = []
        for r in rows:
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

    def _build_empty_charts_data(self) -> dict[str, Any]:
        """Estrutura vazia padrão para segmentos sem participantes."""
        return {
            "genero": {"labels": [], "data": [], "percentages": []},
            "comunidade": {"labels": [], "data": []},
            "estado": {"labels": [], "data": []},
            "meta": {"labels": [], "data": []},
            "frente": {"labels": [], "data": []},
        }
