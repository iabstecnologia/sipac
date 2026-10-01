"""
Orquestrador central (Facade) do pipeline de importação do SIPAC.
Coordena a Fase 1 (Pré-validação e Diagnóstico) e a Fase 2 (Persistência Atômica).
"""

from pathlib import Path
from typing import Any, BinaryIO
from .importer import DatabaseImporter
from .processor import ImportacaoProcessor
from .reader import ExcelReader
from .result import ImportPreview, ImportResult, ProcessedRow


class ImportacaoService:
    """
    Fachada pública do módulo de importação.
    Isola a lógica operacional do Django HTTP / Views, permitindo execução tanto
    via requisições web quanto via comandos CLI ou tarefas em background.
    """

    def __init__(
        self,
        reader: ExcelReader | None = None,
        processor: ImportacaoProcessor | None = None,
        importer: DatabaseImporter | None = None,
    ):
        self.reader = reader or ExcelReader()
        self.processor = processor or ImportacaoProcessor(check_database=True)
        self.importer = importer or DatabaseImporter()

    def processar_preview(
        self,
        file_source: str | Path | BinaryIO,
    ) -> ImportPreview:
        """
        Fase 1: Leitura, normalização e pré-validação diagnóstica.
        - Lê as linhas do arquivo Excel.
        - Aplica os normalizadores especializados.
        - Executa as regras de validação e checagem de conflitos em lote.
        - Retorna um DTO ImportPreview completo com totalizadores e erros.
        - NÃO realiza qualquer alteração ou gravação no banco de dados.
        """
        raw_rows = self.reader.read(file_source)
        processed_rows = self.processor.process_batch(raw_rows)
        return ImportPreview.from_processed_rows(processed_rows)

    def executar_importacao(
        self,
        rows: list[ProcessedRow] | list[dict[str, Any]],
    ) -> ImportResult:
        """
        Fase 2: Persistência transacional atômica.
        - Grava todas as linhas válidas sob bloco transaction.atomic().
        - Garante rollback integral em caso de inconsistência no banco.
        - Retorna o DTO ImportResult com contagem de importados e status.
        """
        return self.importer.persist_atomic(rows)
