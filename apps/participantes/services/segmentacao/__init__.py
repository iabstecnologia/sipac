"""
Módulo do serviço de Segmentação de Participantes.
"""

from .dtos import (
    SegmentDefinition,
    SegmentKPIs,
    SegmentResult,
    SegmentationAnalysisResult,
)
from .service import SegmentacaoService

__all__ = [
    "SegmentDefinition",
    "SegmentKPIs",
    "SegmentResult",
    "SegmentationAnalysisResult",
    "SegmentacaoService",
]
