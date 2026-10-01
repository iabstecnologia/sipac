"""
Estruturas de dados (Dataclasses / DTOs) do pipeline de importação do SIPAC.
Garante tipagem estrita e desacoplamento total entre Services, Views e Templates.
"""

from collections import Counter
from dataclasses import dataclass, field
from typing import Any


@dataclass(frozen=True)
class ValidationError:
    """
    Representa uma incongruência pontual identificada em um campo de uma linha.
    """

    field: str
    code: str
    message: str

    def to_dict(self) -> dict[str, str]:
        return {
            "field": self.field,
            "code": self.code,
            "message": self.message,
        }


@dataclass
class ProcessedRow:
    """
    Representa o resultado do processamento de uma linha individual da planilha.
    """

    row_number: int
    codigo: str | None
    data: dict[str, Any]
    errors: list[ValidationError] = field(default_factory=list)

    @property
    def is_valid(self) -> bool:
        """Indica se a linha está 100% apta para gravação (sem erros)."""
        return len(self.errors) == 0

    def to_dict(self) -> dict[str, Any]:
        serialized_data = {}
        for k, v in self.data.items():
            if hasattr(v, "isoformat"):
                serialized_data[k] = v.isoformat()
            elif hasattr(v, "raw_value"):
                serialized_data[k] = str(v.raw_value)
            else:
                serialized_data[k] = v

        return {
            "row_number": self.row_number,
            "codigo": self.codigo,
            "data": serialized_data,
            "errors": [err.to_dict() for err in self.errors],
            "is_valid": self.is_valid,
        }


@dataclass
class ImportPreview:
    """
    Diagnóstico completo gerado na Fase 1 (Pré-validação).
    Consolida métricas e permite visualização prévia antes de qualquer gravação no banco.
    """

    total_rows: int
    valid_rows: int
    invalid_rows: int
    rows: list[ProcessedRow]
    error_summary: dict[str, int] = field(default_factory=dict)

    @classmethod
    def from_processed_rows(cls, rows: list[ProcessedRow]) -> "ImportPreview":
        total = len(rows)
        valid = sum(1 for r in rows if r.is_valid)
        invalid = total - valid

        # Sumarizar erros mais frequentes
        error_counter: Counter[str] = Counter()
        for r in rows:
            for err in r.errors:
                error_counter[f"{err.field}: {err.message}"] += 1

        return cls(
            total_rows=total,
            valid_rows=valid,
            invalid_rows=invalid,
            rows=rows,
            error_summary=dict(error_counter.most_common(10)),
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "total_rows": self.total_rows,
            "valid_rows": self.valid_rows,
            "invalid_rows": self.invalid_rows,
            "error_summary": self.error_summary,
            "sample_errors": [
                r.to_dict() for r in self.rows if not r.is_valid
            ][:100],  # Amostra das primeiras 100 com erro para auditoria
        }


@dataclass
class ImportResult:
    """
    Resultado final da Fase 2 (Persistência Transacional no Banco de Dados).
    """

    success: bool
    total_imported: int
    errors: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "success": self.success,
            "total_imported": self.total_imported,
            "errors": self.errors,
        }
