"""
DTOs para o serviço de Segmentação de Participantes do SIPAC.
Encapsulam configurações de segmentos, métricas de transparência e resultados analíticos.
"""

from dataclasses import asdict, dataclass, field
from typing import Any
from apps.participantes.services.dashboard.filters import DashboardFilter


@dataclass
class SegmentDefinition:
    """
    Define os parâmetros de um segmento individual com sua prioridade de alocação.
    """

    id: str
    name: str
    order: int
    filters: DashboardFilter = field(default_factory=DashboardFilter)

    @classmethod
    def from_dict(cls, data: dict[str, Any], default_order: int = 1) -> "SegmentDefinition":
        seg_id = str(data.get("id") or f"seg_{default_order}")
        name = str(data.get("name") or f"Segmento {default_order}").strip()
        
        raw_order = data.get("order", default_order)
        try:
            order = int(raw_order)
        except (ValueError, TypeError):
            order = default_order

        raw_filters = data.get("filters", {})
        if isinstance(raw_filters, DashboardFilter):
            filter_dto = raw_filters
        elif isinstance(raw_filters, dict):
            filter_dto = DashboardFilter.from_dict(raw_filters)
        else:
            filter_dto = DashboardFilter()

        return cls(
            id=seg_id,
            name=name,
            order=order,
            filters=filter_dto,
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "name": self.name,
            "order": self.order,
            "filters": self.filters.to_dict(),
        }


@dataclass
class SegmentKPIs:
    """
    Indicadores quantitativos e de transparência do segmento.
    """

    raw_participants: int = 0
    excluded_participants: int = 0
    participants: int = 0
    participations: int = 0
    eventos: int = 0
    instituicoes: int = 0
    media_participacoes: float = 0.0

    @property
    def retention_percentage(self) -> float:
        """Percentual de retenção de participantes (efetivo / bruto)."""
        if self.raw_participants <= 0:
            return 0.0
        return round((self.participants / self.raw_participants) * 100, 1)

    def to_dict(self) -> dict[str, Any]:
        res = asdict(self)
        res["retention_percentage"] = self.retention_percentage
        return res


@dataclass
class SegmentResult:
    """
    Resultado consolidado de um segmento após a aplicação das regras de exclusão sequencial.
    """

    definition: SegmentDefinition
    kpis: SegmentKPIs
    charts_data: dict[str, Any] = field(default_factory=dict)
    ranking_eventos: list[dict[str, Any]] = field(default_factory=list)
    is_empty: bool = False

    def to_dict(self) -> dict[str, Any]:
        return {
            "order": self.definition.order,
            "id": self.definition.id,
            "name": self.definition.name,
            "filters": self.definition.filters.to_dict(),
            "raw_participants": self.kpis.raw_participants,
            "excluded_participants": self.kpis.excluded_participants,
            "participants": self.kpis.participants,
            "participations": self.kpis.participations,
            "kpis": self.kpis.to_dict(),
            "charts": self.charts_data,
            "ranking_eventos": self.ranking_eventos,
            "is_empty": self.is_empty,
        }


@dataclass
class SegmentationAnalysisResult:
    """
    Resultado global de uma análise contendo múltiplos segmentos ordenados.
    """

    segments: list[SegmentResult] = field(default_factory=list)
    total_unique_participants_allocated: int = 0
    total_participations_allocated: int = 0
    total_segments: int = 0

    def to_dict(self) -> dict[str, Any]:
        return {
            "segments": [seg.to_dict() for seg in self.segments],
            "total_unique_participants_allocated": self.total_unique_participants_allocated,
            "total_participations_allocated": self.total_participations_allocated,
            "total_segments": self.total_segments,
        }
