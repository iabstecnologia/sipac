"""
Model base abstrato para auditoria temporal de entidades do SIPAC.
"""

from django.db import models


class TimeStampedModel(models.Model):
    """
    Classe base abstrata que adiciona campos de timestamping automático:
    - created_at: Data/hora exata da persistência inicial do registro.
    - updated_at: Data/hora da última alteração de qualquer campo do registro.
    """

    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name="Criado em",
        help_text="Data e hora de inserção do registro no sistema.",
    )
    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name="Atualizado em",
        help_text="Data e hora da última modificação do registro.",
    )

    class Meta:
        abstract = True
