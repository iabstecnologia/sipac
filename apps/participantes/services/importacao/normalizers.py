"""
Normalizadores puros do pipeline de importação do SIPAC.
Funções puras responsáveis por padronizar tipos e representações de dados.
Regra de ouro: o normalizador NUNCA emite exceções de regra de negócio nem rejeita linhas.
"""

from datetime import date, datetime
import re
from typing import Any
import unicodedata
from openpyxl.utils.datetime import from_excel
from .constants import (
    COMUNIDADE_MAPPING,
    EMPTY_VALUES,
    ESTADO_MAPPING,
    FRENTE_MAPPING,
    GENERO_MAPPING,
    META_MAPPING,
    TIPO_PARTICIPANTE_MAPPING,
)


class UnparseableDate:
    """
    Marcador para datas com conteúdo preenchido que não puderam ser convertidas.
    Permite que o validador diferencie ausência legítima (None) de formato corrompido.
    """

    def __init__(self, raw_value: Any):
        self.raw_value = str(raw_value)

    def __repr__(self) -> str:
        return f"UnparseableDate({self.raw_value!r})"

    def __str__(self) -> str:
        return self.raw_value


def strip_accents(text: str) -> str:
    """Remove acentos gráficos de uma string para comparação fonética/canônica."""
    return "".join(
        c for c in unicodedata.normalize("NFD", text) if unicodedata.category(c) != "Mn"
    )


def normalize_text(value: Any) -> str | None:
    """
    Sanitiza strings genéricas:
    - Converte múltiplos espaços e quebras de linha em espaço único.
    - Aplica strip nas extremidades.
    - Converte representações de vazio (EMPTY_VALUES) em None.
    """
    if value is None:
        return None

    cleaned = " ".join(str(value).strip().split())
    if not cleaned or cleaned.upper() in EMPTY_VALUES:
        return None

    return cleaned


def normalize_nome(value: Any) -> str | None:
    """
    Normaliza nome de pessoa física:
    Preserva maiúsculas e minúsculas originais, eliminando apenas espaços excedentes.
    """
    return normalize_text(value)


def normalize_cpf(value: Any) -> str | None:
    """
    Normaliza CPF:
    Remove toda e qualquer pontuação, letra ou caractere especial, mantendo apenas dígitos numéricos.
    Não altera o número de dígitos (a validação de 11 dígitos cabe ao Validator).
    """
    if value is None:
        return None

    cleaned = normalize_text(value)
    if cleaned is None:
        return None

    digits = re.sub(r"\D", "", cleaned)
    if not digits:
        return None

    return digits


def normalize_codigo(value: Any) -> str | None:
    """
    Normaliza código de identificação da participação:
    Converte para uppercase sanitizado (ex: 'part-00001' -> 'PART-00001').
    """
    cleaned = normalize_text(value)
    if cleaned is None:
        return None
    return cleaned.upper()


def normalize_instituicao(value: Any) -> str | None:
    """
    Normaliza nome de instituição:
    Converte para uppercase sanitizado. Ausências conhecidas tornam-se None (NULL no banco).
    """
    if value is None:
        return None

    cleaned = normalize_text(value)
    if cleaned is None or cleaned.upper() in EMPTY_VALUES:
        return None

    return cleaned.upper()


def normalize_evento(value: Any) -> str | None:
    """
    Normaliza título de evento:
    Preserva acentuação e apresentação original, limpando espaços.
    """
    return normalize_text(value)


def normalize_genero(value: Any) -> str | None:
    """
    Mapeia valores de gênero da planilha para as choices internas ('M', 'F', 'NI').
    """
    if value is None:
        return None

    cleaned = " ".join(str(value).strip().split())
    if not cleaned:
        return None

    key = strip_accents(cleaned.upper())
    if key in GENERO_MAPPING:
        return GENERO_MAPPING[key]

    if cleaned.upper() in EMPTY_VALUES:
        return Genero.NAO_INFORMADO.value

    return cleaned


def normalize_comunidade(value: Any) -> str | None:
    """
    Mapeia valores de comunidade tradicional para as choices internas.
    """
    cleaned = normalize_text(value)
    if cleaned is None:
        return None

    key = strip_accents(cleaned.upper())
    return COMUNIDADE_MAPPING.get(key, cleaned)


def normalize_tipo_participante(value: Any) -> str | None:
    """
    Mapeia papel do participante (Produtor, Técnico, Outros).
    """
    cleaned = normalize_text(value)
    if cleaned is None:
        return None

    key = strip_accents(cleaned.upper())
    # Normaliza variações de parenteses
    key_no_paren = " ".join(re.sub(r"[()]", "", key).split())
    return TIPO_PARTICIPANTE_MAPPING.get(key_no_paren, TIPO_PARTICIPANTE_MAPPING.get(key, cleaned))


def normalize_frente(value: Any) -> str | None:
    """
    Mapeia frente responsável (ex: 'Campo' -> 'CAMPO', 'ATER/Capacitação' -> 'ATER_CAPACITACAO').
    """
    cleaned = normalize_text(value)
    if cleaned is None:
        return None

    key = strip_accents(cleaned.upper())
    return FRENTE_MAPPING.get(key, cleaned.upper())


def normalize_meta(value: Any) -> str | None:
    """
    Mapeia metas internas do projeto.
    """
    cleaned = normalize_text(value)
    if cleaned is None:
        return None

    key = strip_accents(cleaned.upper())
    return META_MAPPING.get(key, cleaned)


def normalize_estado(value: Any) -> str | None:
    """
    Mapeia nome do estado (por extenso ou sigla) para a UF canônica de 2 letras.
    """
    cleaned = normalize_text(value)
    if cleaned is None:
        return None

    key = strip_accents(cleaned.upper())
    return ESTADO_MAPPING.get(key, cleaned.upper())


def normalize_ano(value: Any) -> int | None:
    """
    Normaliza a coluna ANO para inteiro comparativo.
    """
    if value is None:
        return None

    if isinstance(value, (int, float)):
        return int(value)

    cleaned = normalize_text(value)
    if cleaned is None:
        return None

    try:
        return int(float(cleaned))
    except (ValueError, TypeError):
        return None


def normalize_date(value: Any) -> date | UnparseableDate | None:
    """
    Normaliza representações de data para objetos datetime.date.
    Suporta:
    - datetime.datetime e datetime.date
    - Números seriais do Excel (inteiros/floats, ex: 46261)
    - Strings em formatos brasileiros (DD/MM/YYYY, DD-MM-YYYY), ISO (YYYY-MM-DD), Americano (MM/DD/YYYY)
    - Ausências legítimas retornam None
    - Valores corrompidos ou ilegíveis retornam UnparseableDate
    """
    if value is None:
        return None

    # Caso 1: datetime ou date nativo
    if isinstance(value, datetime):
        return value.date()
    if isinstance(value, date):
        return value

    # Caso 2: número serial numérico do Excel
    if isinstance(value, (int, float)):
        try:
            return from_excel(float(value)).date()
        except Exception:
            return UnparseableDate(value)

    # Caso 3: String
    if isinstance(value, str):
        cleaned = value.strip().strip(".")
        if not cleaned or cleaned.upper() in EMPTY_VALUES:
            return None

        # Se for string de dígitos seriais do Excel (ex: '46261')
        if cleaned.isdigit() and len(cleaned) <= 5:
            try:
                return from_excel(float(cleaned)).date()
            except Exception:
                return UnparseableDate(value)

        # Se for string de 8 dígitos concatenados sem barra (ex: '15021992')
        if cleaned.isdigit() and len(cleaned) == 8:
            try:
                return datetime.strptime(cleaned, "%d%m%Y").date()
            except ValueError:
                return UnparseableDate(value)

        # Formatos textuais suportados
        date_formats = (
            "%d/%m/%Y",
            "%d-%m-%Y",
            "%Y-%m-%d",
            "%m/%d/%Y",
            "%d/%m/%y",
            "%m/%d/%y",
        )

        for fmt in date_formats:
            try:
                return datetime.strptime(cleaned, fmt).date()
            except ValueError:
                continue

        return UnparseableDate(value)

    return UnparseableDate(value)


def normalize_row(raw_data: dict[str, Any]) -> dict[str, Any]:
    """
    Recebe um dicionário com os campos brutos de uma linha e aplica
    todos os normalizadores especializados, produzindo a linha normalizada canônica.
    """
    return {
        "codigo": normalize_codigo(raw_data.get("codigo")),
        "evento": normalize_evento(raw_data.get("evento")),
        "frente_responsavel": normalize_frente(raw_data.get("frente_responsavel")),
        "meta_interna": normalize_meta(raw_data.get("meta_interna")),
        "data_evento": normalize_date(raw_data.get("data_evento")),
        "ano": normalize_ano(raw_data.get("ano")),
        "nome": normalize_nome(raw_data.get("nome")),
        "cpf": normalize_cpf(raw_data.get("cpf")),
        "data_nascimento": normalize_date(raw_data.get("data_nascimento")),
        "genero": normalize_genero(raw_data.get("genero")),
        "comunidade_tradicional": normalize_comunidade(raw_data.get("comunidade_tradicional")),
        "tipo_participante": normalize_tipo_participante(raw_data.get("tipo_participante")),
        "estado": normalize_estado(raw_data.get("estado")),
        "instituicao": normalize_instituicao(raw_data.get("instituicao")),
    }
