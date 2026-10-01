"""
Leitor streaming de planilhas Excel (.xlsx) para o SIPAC.
Responsável exclusivamente por converter o arquivo bruto em estruturas Python (dict).
"""

from pathlib import Path
from typing import Any, BinaryIO
import openpyxl
from .constants import HEADER_ALIASES, REQUIRED_CANONICAL_COLUMNS


class ExcelReaderError(Exception):
    """Exceção base para erros ocorridos durante a leitura da planilha."""

    pass


class MissingRequiredColumnsError(ExcelReaderError):
    """Exceção levantada quando faltam colunas obrigatórias na planilha."""

    def __init__(self, missing_columns: list[str]):
        self.missing_columns = missing_columns
        super().__init__(
            f"A planilha não contém as seguintes colunas obrigatórias: "
            f"{', '.join(sorted(missing_columns))}"
        )


class ExcelReader:
    """
    Leitor de planilhas Excel (.xlsx) em streaming.
    - Utiliza openpyxl em modo read_only=True e data_only=True.
    - Normaliza os nomes de cabeçalho através de HEADER_ALIASES.
    - Valida a presença de todas as colunas canônicas obrigatórias.
    - Descarta automaticamente linhas vazias ao final do arquivo.
    - NÃO aplica regras de negócio nem manipula tipos de dados.
    """

    def __init__(self, required_columns: frozenset[str] = REQUIRED_CANONICAL_COLUMNS):
        self.required_columns = required_columns

    @staticmethod
    def _is_row_empty(values: tuple[Any, ...]) -> bool:
        """Verifica se uma tupla de valores de célula está completamente em branco."""
        for v in values:
            if v is not None and str(v).strip() != "":
                return False
        return True

    @staticmethod
    def _clean_header_text(header_val: Any) -> str:
        """Limpa e padroniza a string de cabeçalho para cruzamento com aliases."""
        if header_val is None:
            return ""
        return " ".join(str(header_val).strip().split()).upper()

    def read(self, file_source: str | Path | BinaryIO) -> list[dict[str, Any]]:
        """
        Lê a planilha e retorna uma lista de registros brutos.

        Retorno:
        [
            {
                "row_number": 2,
                "data": {
                    "codigo": "PART-00001",
                    "evento": "...",
                    "data_evento": 46261,
                    ...
                }
            },
            ...
        ]
        """
        try:
            wb = openpyxl.load_workbook(file_source, read_only=True, data_only=True)
        except Exception as exc:
            raise ExcelReaderError(f"Não foi possível abrir o arquivo Excel: {exc}") from exc

        try:
            sheet = wb.active
            if sheet is None:
                raise ExcelReaderError("A planilha informada não possui nenhuma aba ativa.")

            rows_iter = sheet.iter_rows(values_only=True)

            # 1. Leitura e validação da primeira linha (Cabeçalho)
            try:
                header_row = next(rows_iter)
            except StopIteration:
                raise ExcelReaderError("A planilha informada está vazia.") from None

            if not header_row or self._is_row_empty(header_row):
                raise ExcelReaderError("O cabeçalho da planilha (linha 1) está vazio.")

            col_canonical_keys: list[str | None] = []
            found_canonical_keys: set[str] = set()

            for cell_val in header_row:
                cleaned_title = self._clean_header_text(cell_val)
                if not cleaned_title:
                    col_canonical_keys.append(None)
                    continue

                canonical_key = HEADER_ALIASES.get(cleaned_title, cleaned_title.lower())
                col_canonical_keys.append(canonical_key)
                found_canonical_keys.add(canonical_key)

            # 2. Checagem de colunas obrigatórias
            missing_cols = self.required_columns - found_canonical_keys
            if missing_cols:
                raise MissingRequiredColumnsError(list(missing_cols))

            # 3. Leitura dos registros de dados (a partir da linha 2)
            results: list[dict[str, Any]] = []

            for row_idx, row_values in enumerate(rows_iter, start=2):
                if not row_values or self._is_row_empty(row_values):
                    # Descarte de linhas em branco
                    continue

                row_dict: dict[str, Any] = {}
                for col_idx, col_key in enumerate(col_canonical_keys):
                    if col_key is not None:
                        val = row_values[col_idx] if col_idx < len(row_values) else None
                        row_dict[col_key] = val

                results.append(
                    {
                        "row_number": row_idx,
                        "data": row_dict,
                    }
                )

            return results

        finally:
            wb.close()
