"""
Validadores puros de regra de negócio do pipeline de importação do SIPAC.
Regra de ouro: o validador NUNCA altera nem sanitiza dados; apenas audita os dados já normalizados.
"""

from datetime import date
from typing import Any
from django.db import models
from apps.participantes.models.choices import (
    ComunidadeTradicional,
    Estado,
    FrenteResponsavel,
    Genero,
    MetaInterna,
    TipoParticipante,
)
from .normalizers import UnparseableDate
from .result import ValidationError


def validate_cpf(cpf: str | None) -> list[ValidationError]:
    """
    Valida o CPF conforme o algoritmo oficial de dígitos verificadores da Receita Federal:
    - Obrigatoriedade (não pode ser nulo ou vazio).
    - Extensão exata de 11 dígitos numéricos.
    - Rejeição de sequências com 11 dígitos repetidos (ex: '11111111111').
    - Cálculo matemático e conferência dos dois dígitos verificadores (DV1 e DV2).
    """
    if cpf is None or not cpf.strip():
        return [
            ValidationError(
                field="cpf",
                code="missing_cpf",
                message="CPF do participante é obrigatório.",
            )
        ]

    cpf_digits = cpf.strip()

    if not cpf_digits.isdigit() or len(cpf_digits) != 11:
        return [
            ValidationError(
                field="cpf",
                code="invalid_length",
                message=f"CPF possui {len(cpf_digits)} dígitos (esperado exatamente 11 dígitos).",
            )
        ]

    # Rejeita dígitos repetidos conhecidos (ex: 00000000000, 11111111111...)
    if cpf_digits == cpf_digits[0] * 11:
        return [
            ValidationError(
                field="cpf",
                code="repeated_digits",
                message="CPF composto por dígitos repetidos é matematicamente inválido.",
            )
        ]

    # Cálculo do primeiro dígito verificador
    sum_1 = sum(int(cpf_digits[i]) * (10 - i) for i in range(9))
    rem_1 = (sum_1 * 10) % 11
    expected_dv1 = 0 if rem_1 == 10 else rem_1

    if expected_dv1 != int(cpf_digits[9]):
        return [
            ValidationError(
                field="cpf",
                code="invalid_dv",
                message="Dígito verificador do CPF inválido.",
            )
        ]

    # Cálculo do segundo dígito verificador
    sum_2 = sum(int(cpf_digits[i]) * (11 - i) for i in range(10))
    rem_2 = (sum_2 * 10) % 11
    expected_dv2 = 0 if rem_2 == 10 else rem_2

    if expected_dv2 != int(cpf_digits[10]):
        return [
            ValidationError(
                field="cpf",
                code="invalid_dv",
                message="Dígito verificador do CPF inválido.",
            )
        ]

    return []


def validate_data_nascimento(dt: Any) -> list[ValidationError]:
    """
    Valida a data de nascimento da pessoa física:
    - Ausência é válida (None) pois data_nascimento é campo opcional no modelo.
    - Valores ilegíveis geram erro.
    - Validação de plausibilidade: data não pode ser anterior a 01/01/1900 nem futura.
    """
    if dt is None:
        return []

    if isinstance(dt, UnparseableDate):
        return [
            ValidationError(
                field="data_nascimento",
                code="invalid_date_format",
                message=f"Data de nascimento com formato ilegível ou corrompido: '{dt}'.",
            )
        ]

    if isinstance(dt, (date,)):
        if dt < date(1900, 1, 1):
            return [
                ValidationError(
                    field="data_nascimento",
                    code="implausible_past_date",
                    message=f"Data de nascimento implausível ({dt.strftime('%d/%m/%Y')} é anterior ao ano 1900).",
                )
            ]

        if dt > date.today():
            return [
                ValidationError(
                    field="data_nascimento",
                    code="future_date",
                    message=f"Data de nascimento não pode ser no futuro ({dt.strftime('%d/%m/%Y')}).",
                )
            ]

        return []

    return [
        ValidationError(
            field="data_nascimento",
            code="invalid_type",
            message="Tipo de dado inválido para data de nascimento.",
        )
    ]


def validate_data_evento(dt: Any) -> list[ValidationError]:
    """
    Valida a data da atividade/evento:
    - Obrigatória (não pode ser nula).
    - Valores ilegíveis (como 'NÃO INFORMADO') geram erro impeditivo.
    - Validação de verossimilhança cronológica.
    """
    if dt is None:
        return [
            ValidationError(
                field="data_evento",
                code="missing_event_date",
                message="Data da atividade é obrigatória para cadastro do Evento.",
            )
        ]

    if isinstance(dt, UnparseableDate):
        return [
            ValidationError(
                field="data_evento",
                code="invalid_event_date_format",
                message=f"Data da atividade com formato ilegível ou ausente: '{dt}'.",
            )
        ]

    if isinstance(dt, (date,)):
        if dt < date(2000, 1, 1) or dt > date(2100, 1, 1):
            return [
                ValidationError(
                    field="data_evento",
                    code="implausible_event_date",
                    message=f"Data da atividade fora do intervalo operacional aceito: {dt.strftime('%d/%m/%Y')}.",
                )
            ]
        return []

    return [
        ValidationError(
            field="data_evento",
            code="invalid_type",
            message="Tipo de dado inválido para data da atividade.",
        )
    ]


def validate_choice(
    value: Any,
    choice_cls: type[models.TextChoices],
    field_name: str,
    field_label: str,
) -> list[ValidationError]:
    """
    Verifica se um valor pertence ao catálogo oficial de TextChoices correspondente.
    """
    if value is None:
        return [
            ValidationError(
                field=field_name,
                code=f"missing_{field_name}",
                message=f"O campo '{field_label}' é obrigatório.",
            )
        ]

    valid_values = choice_cls.values
    if value not in valid_values:
        return [
            ValidationError(
                field=field_name,
                code=f"invalid_{field_name}",
                message=f"Valor '{value}' não é reconhecido para {field_label}.",
            )
        ]

    return []


def validate_codigo(codigo: str | None) -> list[ValidationError]:
    """Valida obrigatoriedade do código de participação."""
    if not codigo or not str(codigo).strip():
        return [
            ValidationError(
                field="codigo",
                code="missing_codigo",
                message="Código da participação é obrigatório.",
            )
        ]
    return []


def validate_nome(nome: str | None) -> list[ValidationError]:
    """Valida obrigatoriedade do nome do participante."""
    if not nome or not str(nome).strip():
        return [
            ValidationError(
                field="nome",
                code="missing_nome",
                message="Nome do participante é obrigatório.",
            )
        ]
    return []


def validate_evento_nome(evento: str | None) -> list[ValidationError]:
    """Valida obrigatoriedade do nome do evento/atividade."""
    if not evento or not str(evento).strip():
        return [
            ValidationError(
                field="evento",
                code="missing_evento",
                message="Título/nome do evento é obrigatório.",
            )
        ]
    return []


def validate_ano_consistencia(
    ano: int | None,
    data_evento: Any,
) -> list[ValidationError]:
    """
    Valida se o ano indicado na coluna 'ANO' corresponde ao ano da data da atividade.
    """
    if ano is not None and isinstance(data_evento, date):
        if ano != data_evento.year:
            return [
                ValidationError(
                    field="ano",
                    code="inconsistent_year",
                    message=f"Ano informado ({ano}) diverge do ano real da atividade ({data_evento.year}).",
                )
            ]
    return []


def validate_row(normalized_data: dict[str, Any]) -> list[ValidationError]:
    """
    Coordena todas as validações de regras de negócio sobre uma linha já normalizada.
    Retorna a lista completa de erros (vazia se a linha for 100% válida).
    """
    errors: list[ValidationError] = []

    # 1. Código da Participação
    errors.extend(validate_codigo(normalized_data.get("codigo")))

    # 2. Dados da Pessoa
    errors.extend(validate_cpf(normalized_data.get("cpf")))
    errors.extend(validate_nome(normalized_data.get("nome")))
    errors.extend(validate_data_nascimento(normalized_data.get("data_nascimento")))
    errors.extend(
        validate_choice(
            normalized_data.get("genero"),
            Genero,
            field_name="genero",
            field_label="Gênero",
        )
    )
    errors.extend(
        validate_choice(
            normalized_data.get("comunidade_tradicional"),
            ComunidadeTradicional,
            field_name="comunidade_tradicional",
            field_label="Comunidade tradicional",
        )
    )

    # 3. Dados do Evento
    errors.extend(validate_evento_nome(normalized_data.get("evento")))
    data_evento = normalized_data.get("data_evento")
    errors.extend(validate_data_evento(data_evento))
    errors.extend(
        validate_choice(
            normalized_data.get("frente_responsavel"),
            FrenteResponsavel,
            field_name="frente_responsavel",
            field_label="Frente responsável",
        )
    )
    errors.extend(
        validate_choice(
            normalized_data.get("meta_interna"),
            MetaInterna,
            field_name="meta_interna",
            field_label="Meta interna",
        )
    )
    errors.extend(
        validate_choice(
            normalized_data.get("estado"),
            Estado,
            field_name="estado",
            field_label="Estado (UF)",
        )
    )

    # 4. Dados da Participação
    errors.extend(
        validate_choice(
            normalized_data.get("tipo_participante"),
            TipoParticipante,
            field_name="tipo_participante",
            field_label="Tipo do participante",
        )
    )

    # 5. Consistência entre Ano e Data
    errors.extend(
        validate_ano_consistencia(
            normalized_data.get("ano"),
            data_evento,
        )
    )

    return errors
