"""
Sub-serviço do Pipeline de Importação do SIPAC.
"""

from .constants import (
    COMUNIDADE_MAPPING,
    EMPTY_VALUES,
    ESTADO_MAPPING,
    FRENTE_MAPPING,
    GENERO_MAPPING,
    HEADER_ALIASES,
    META_MAPPING,
    REQUIRED_CANONICAL_COLUMNS,
    TIPO_PARTICIPANTE_MAPPING,
)
from .importer import (
    DatabaseImporter,
)
from .normalizers import (
    UnparseableDate,
    normalize_ano,
    normalize_codigo,
    normalize_comunidade,
    normalize_cpf,
    normalize_date,
    normalize_estado,
    normalize_evento,
    normalize_frente,
    normalize_genero,
    normalize_instituicao,
    normalize_meta,
    normalize_nome,
    normalize_row,
    normalize_text,
    normalize_tipo_participante,
    strip_accents,
)
from .processor import (
    ImportacaoProcessor,
)
from .reader import (
    ExcelReader,
    ExcelReaderError,
    MissingRequiredColumnsError,
)
from .result import (
    ImportPreview,
    ImportResult,
    ProcessedRow,
    ValidationError,
)
from .service import (
    ImportacaoService,
)
from .validators import (
    validate_ano_consistencia,
    validate_choice,
    validate_codigo,
    validate_cpf,
    validate_data_evento,
    validate_data_nascimento,
    validate_evento_nome,
    validate_nome,
    validate_row,
)

__all__ = [
    "ExcelReader",
    "ExcelReaderError",
    "MissingRequiredColumnsError",
    "ValidationError",
    "ProcessedRow",
    "ImportPreview",
    "ImportResult",
    "ImportacaoProcessor",
    "DatabaseImporter",
    "ImportacaoService",
    "UnparseableDate",
    "EMPTY_VALUES",
    "REQUIRED_CANONICAL_COLUMNS",
    "HEADER_ALIASES",
    "GENERO_MAPPING",
    "COMUNIDADE_MAPPING",
    "TIPO_PARTICIPANTE_MAPPING",
    "FRENTE_MAPPING",
    "META_MAPPING",
    "ESTADO_MAPPING",
    "strip_accents",
    "normalize_text",
    "normalize_nome",
    "normalize_cpf",
    "normalize_codigo",
    "normalize_instituicao",
    "normalize_evento",
    "normalize_genero",
    "normalize_comunidade",
    "normalize_tipo_participante",
    "normalize_frente",
    "normalize_meta",
    "normalize_estado",
    "normalize_ano",
    "normalize_date",
    "normalize_row",
    "validate_cpf",
    "validate_data_nascimento",
    "validate_data_evento",
    "validate_choice",
    "validate_codigo",
    "validate_nome",
    "validate_evento_nome",
    "validate_ano_consistencia",
    "validate_row",
]
