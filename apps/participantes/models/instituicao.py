"""
Model de Instituição (Catálogo normalizado de órgãos e entidades).
"""

from django.db import models
from .base import TimeStampedModel


class Instituicao(TimeStampedModel):
    """
    Catálogo sanitizado de instituições parceiras, executoras ou contratantes.
    Identificador único: nome padronizado em uppercase.
    """

    nome = models.CharField(
        max_length=255,
        unique=True,
        verbose_name="Nome da instituição",
        help_text="Nome canônico da instituição em maiúsculas.",
    )

    class Meta:
        verbose_name = "Instituição"
        verbose_name_plural = "Instituições"
        ordering = ["nome"]

    def __str__(self) -> str:
        return self.nome
