"""
Processador e orquestrador do pipeline de importação do SIPAC.
Coordena normalização, validações de campo e detecção de duplicidades/conflitos relacionais em lote.
"""

from datetime import date
from typing import Any
from apps.participantes.models import Evento, Participacao
from .normalizers import normalize_row
from .result import ProcessedRow, ValidationError
from .validators import validate_row


class ImportacaoProcessor:
    """
    Orquestrador de saneamento e integridade:
    - Executa a sequência: Dados Brutos -> Normalização -> Validação -> ProcessedRow.
    - Audita unicidade de código de participação dentro da planilha e contra o banco.
    - Audita consistência geográfica do evento (conflito de estados para mesma atividade).
    """

    def __init__(self, check_database: bool = True):
        self.check_database = check_database

    def process_row(
        self,
        raw_data: dict[str, Any],
        row_number: int,
    ) -> ProcessedRow:
        """Processa uma única linha isolada (sem contexto de lote)."""
        normalized = normalize_row(raw_data)
        errors = validate_row(normalized)
        return ProcessedRow(
            row_number=row_number,
            codigo=normalized.get("codigo"),
            data=normalized,
            errors=errors,
        )

    def process_batch(
        self,
        raw_rows: list[dict[str, Any]],
    ) -> list[ProcessedRow]:
        """
        Processa uma lista completa de linhas brutas extraídas pelo ExcelReader:
        - Carrega índices em memória para evitar queries repetitivas (N+1).
        - Detecta códigos de participação duplicados dentro do próprio arquivo.
        - Detecta códigos já existentes no banco de dados.
        - Detecta conflitos de estado para a mesma atividade/evento.
        """
        # 1. Carregamento de chaves já existentes no banco para validação O(1)
        existing_db_codes: set[str] = set()
        existing_db_events: dict[tuple[str, date, str, str], str] = {}

        if self.check_database:
            existing_db_codes = set(
                Participacao.objects.values_list("codigo", flat=True)
            )
            for ev in Evento.objects.values(
                "nome", "data", "frente_responsavel", "meta_interna", "estado"
            ):
                key = (
                    ev["nome"],
                    ev["data"],
                    ev["frente_responsavel"],
                    ev["meta_interna"],
                )
                existing_db_events[key] = ev["estado"]

        # 2. Rastreamento de unicidade interna do lote
        seen_batch_codes: dict[str, int] = {}
        seen_batch_events: dict[tuple[str, date, str, str], tuple[str, int]] = {}

        processed_rows: list[ProcessedRow] = []

        # 3. Iteração linha a linha
        for item in raw_rows:
            row_number = item["row_number"]
            raw_data = item["data"]

            # Etapa A: Normalização
            normalized = normalize_row(raw_data)

            # Etapa B: Validações Intrínsecas da Linha
            errors = validate_row(normalized)

            # Etapa C: Validação de Unicidade do Código de Participação
            codigo = normalized.get("codigo")
            if codigo:
                # Duplicidade dentro do próprio arquivo
                if codigo in seen_batch_codes:
                    first_row = seen_batch_codes[codigo]
                    errors.append(
                        ValidationError(
                            field="codigo",
                            code="duplicate_code_in_file",
                            message=(
                                f"Código '{codigo}' duplicado na planilha "
                                f"(primeira ocorrência na linha {first_row})."
                            ),
                        )
                    )
                else:
                    seen_batch_codes[codigo] = row_number

                # Duplicidade contra o banco de dados
                if self.check_database and codigo in existing_db_codes:
                    errors.append(
                        ValidationError(
                            field="codigo",
                            code="duplicate_code_in_database",
                            message=f"Código '{codigo}' já cadastrado no banco de dados.",
                        )
                    )

            # Etapa D: Detecção de Conflito de Estados em Eventos Idênticos
            ev_nome = normalized.get("evento")
            ev_data = normalized.get("data_evento")
            ev_frente = normalized.get("frente_responsavel")
            ev_meta = normalized.get("meta_interna")
            ev_estado = normalized.get("estado")

            # Apenas audita se os campos identificadores do evento forem válidos
            if (
                ev_nome
                and isinstance(ev_data, date)
                and ev_frente
                and ev_meta
                and ev_estado
            ):
                event_key = (ev_nome, ev_data, ev_frente, ev_meta)

                # Conflito de estado dentro do arquivo em lote
                if event_key in seen_batch_events:
                    prev_uf, prev_row = seen_batch_events[event_key]
                    if ev_estado != prev_uf:
                        errors.append(
                            ValidationError(
                                field="estado",
                                code="event_state_conflict",
                                message=(
                                    f"Conflito de localidade no evento '{ev_nome}': "
                                    f"associado a '{ev_estado}', mas na linha {prev_row} "
                                    f"foi registrado com estado '{prev_uf}'."
                                ),
                            )
                        )
                else:
                    seen_batch_events[event_key] = (ev_estado, row_number)

                # Conflito de estado contra o banco de dados
                if self.check_database and event_key in existing_db_events:
                    db_uf = existing_db_events[event_key]
                    if ev_estado != db_uf:
                        errors.append(
                            ValidationError(
                                field="estado",
                                code="event_state_conflict_db",
                                message=(
                                    f"Conflito de localidade com o banco: evento '{ev_nome}' "
                                    f"está salvo com UF '{db_uf}', mas a planilha indica '{ev_estado}'."
                                ),
                            )
                        )

            processed_rows.append(
                ProcessedRow(
                    row_number=row_number,
                    codigo=codigo,
                    data=normalized,
                    errors=errors,
                )
            )

        return processed_rows
