"""
Model de Participação (Tabela de fatos conectando Pessoa, Evento e Instituição).
"""

from django.db import models
from .base import TimeStampedModel
from .choices import TipoParticipante
from .evento import Evento
from .instituicao import Instituicao
from .pessoa import Pessoa


class Participacao(TimeStampedModel):
    """
    Registra a ocorrência da participação de uma Pessoa em um Evento.
    - codigo: Identificador único de origem (ex: 'PART-00001').
    - pessoa: Vínculo protegido com a Pessoa (PROTECT).
    - evento: Vínculo protegido com o Evento (PROTECT).
    - tipo_participante: Papel desempenhado nesta participação (Produtor, Técnico, etc.).
    - instituicao: Instituição opcional associada ao participante (SET_NULL).
    """

    codigo = models.CharField(
        max_length=50,
        unique=True,
        verbose_name="Código da participação",
        help_text="Identificador único de origem da participação (ex: PART-00001).",
    )
    pessoa = models.ForeignKey(
        Pessoa,
        on_delete=models.PROTECT,
        related_name="participacoes",
        verbose_name="Participante",
        help_text="Pessoa física cadastrada.",
    )
    evento = models.ForeignKey(
        Evento,
        on_delete=models.PROTECT,
        related_name="participacoes",
        verbose_name="Evento",
        help_text="Atividade realizada.",
    )
    tipo_participante = models.CharField(
        max_length=30,
        choices=TipoParticipante.choices,
        verbose_name="Tipo do participante",
        help_text="Papel do participante nesta atividade específica.",
    )
    instituicao = models.ForeignKey(
        Instituicao,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="participacoes",
        verbose_name="Instituição",
        help_text="Instituição associada ao participante (opcional).",
    )

    class Meta:
        verbose_name = "Participação"
        verbose_name_plural = "Participações"
        ordering = ["-evento__data", "codigo"]

    def __str__(self) -> str:
        return f"{self.codigo} - {self.pessoa.nome}"
