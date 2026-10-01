"""
Model de Evento (Atividades, capacitações e encontros de ATER).
"""

from django.db import models
from .base import TimeStampedModel
from .choices import Estado, FrenteResponsavel, MetaInterna


class Evento(TimeStampedModel):
    """
    Representa a atividade realizada no âmbito do projeto.
    Chave Composta Única: (nome, data, frente_responsavel, meta_interna).
    """

    nome = models.CharField(
        max_length=255,
        verbose_name="Nome da atividade",
        help_text="Título descritivo da atividade ou evento.",
    )
    data = models.DateField(
        verbose_name="Data da atividade",
        help_text="Data obrigatória em que a atividade foi realizada.",
    )
    frente_responsavel = models.CharField(
        max_length=30,
        choices=FrenteResponsavel.choices,
        verbose_name="Frente responsável",
    )
    estado = models.CharField(
        max_length=2,
        choices=Estado.choices,
        verbose_name="Estado (UF)",
    )
    meta_interna = models.CharField(
        max_length=80,
        choices=MetaInterna.choices,
        verbose_name="Meta interna",
    )

    class Meta:
        verbose_name = "Evento"
        verbose_name_plural = "Eventos"
        ordering = ["-data", "nome"]
        constraints = [
            models.UniqueConstraint(
                fields=["nome", "data", "frente_responsavel", "meta_interna"],
                name="unique_evento",
            )
        ]
        indexes = [
            models.Index(
                fields=["data"],
                name="evento_data_idx",
            ),
            models.Index(
                fields=["estado", "data"],
                name="evento_estado_data_idx",
            ),
        ]

    def __str__(self) -> str:
        return f"{self.nome} ({self.data.strftime('%d/%m/%Y') if self.data else 'Sem data'})"
