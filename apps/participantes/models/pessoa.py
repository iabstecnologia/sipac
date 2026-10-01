"""
Model de Pessoa física (Cadastro único de participantes).
"""

from django.db import models
from .base import TimeStampedModel
from .choices import ComunidadeTradicional, Genero


class Pessoa(TimeStampedModel):
    """
    Representa o cidadão participante de eventos e atividades.
    Chave Natural: CPF (11 dígitos, sem máscara).
    """

    cpf = models.CharField(
        max_length=11,
        unique=True,
        verbose_name="CPF",
        help_text="Identificador único (11 dígitos, apenas números).",
    )
    nome = models.CharField(
        max_length=255,
        verbose_name="Nome completo",
        help_text="Nome completo do participante.",
    )
    data_nascimento = models.DateField(
        null=True,
        blank=True,
        verbose_name="Data de nascimento",
        help_text="Data de nascimento (opcional).",
    )
    genero = models.CharField(
        max_length=2,
        choices=Genero.choices,
        verbose_name="Gênero",
    )
    comunidade_tradicional = models.CharField(
        max_length=20,
        choices=ComunidadeTradicional.choices,
        verbose_name="Comunidade tradicional",
    )

    class Meta:
        verbose_name = "Pessoa"
        verbose_name_plural = "Pessoas"
        ordering = ["nome"]

    def __str__(self) -> str:
        return self.nome
