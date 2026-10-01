"""
Persistência transacional do pipeline de importação do SIPAC.
Responsável exclusivamente por gravar os registros válidos no banco de dados sob transaction.atomic().
"""

from datetime import date
from typing import Any
from django.db import transaction
from apps.participantes.models import (
    Evento,
    Instituicao,
    Participacao,
    Pessoa,
)
from .result import ImportResult, ProcessedRow


class DatabaseImporter:
    """
    Persistência sob transação atômica completa:
    1. Upsert em Pessoa (update_or_create por CPF).
    2. Get or create em Instituicao (apenas para nomes não nulos).
    3. Get or create em Evento pela tupla lógica (nome, data, frente, meta).
    4. Criação das Participações vinculando as chaves estrangeiras.
    Em caso de qualquer falha ou violação de integridade, executa rollback total automático.
    """

    def persist_atomic(
        self,
        rows: list[ProcessedRow] | list[dict[str, Any]],
    ) -> ImportResult:
        """
        Executa a gravação em lote de todas as linhas válidas informadas.
        Se ocorrer qualquer exceção, a transação é revertida na íntegra.
        """
        # Filtra apenas linhas válidas
        valid_items: list[dict[str, Any]] = []
        for r in rows:
            if isinstance(r, ProcessedRow):
                if r.is_valid:
                    valid_items.append(r.data)
            elif isinstance(r, dict):
                valid_items.append(r)

        if not valid_items:
            return ImportResult(
                success=True,
                total_imported=0,
                errors=["Nenhum registro válido fornecido para importação."],
            )

        try:
            with transaction.atomic():
                # Caches de sessão em memória para acelerar resolução de FKs O(1)
                pessoa_cache: dict[str, Pessoa] = {}
                instituicao_cache: dict[str, Instituicao] = {}
                evento_cache: dict[tuple[str, date, str, str], Evento] = {}

                participacoes_to_create: list[Participacao] = []

                for data in valid_items:
                    # Normaliza datas caso tenham sido desserializadas de JSON como strings ISO
                    data_evento = data["data_evento"]
                    if isinstance(data_evento, str):
                        data_evento = date.fromisoformat(data_evento)

                    data_nascimento = data.get("data_nascimento")
                    if isinstance(data_nascimento, str):
                        data_nascimento = date.fromisoformat(data_nascimento)

                    # 1. Pessoa (upsert por CPF: versão mais recente da linha atualiza o cadastro)
                    cpf = data["cpf"]
                    pessoa, _ = Pessoa.objects.update_or_create(
                        cpf=cpf,
                        defaults={
                            "nome": data["nome"],
                            "data_nascimento": data_nascimento,
                            "genero": data["genero"],
                            "comunidade_tradicional": data["comunidade_tradicional"],
                        },
                    )

                    # 2. Instituição (get_or_create se informado)
                    instituicao = None
                    inst_nome = data.get("instituicao")
                    if inst_nome:
                        if inst_nome not in instituicao_cache:
                            inst_obj, _ = Instituicao.objects.get_or_create(
                                nome=inst_nome
                            )
                            instituicao_cache[inst_nome] = inst_obj
                        instituicao = instituicao_cache[inst_nome]

                    # 3. Evento (get_or_create por chave composta)
                    evento_key = (
                        data["evento"],
                        data_evento,
                        data["frente_responsavel"],
                        data["meta_interna"],
                    )
                    if evento_key not in evento_cache:
                        evento_obj, _ = Evento.objects.get_or_create(
                            nome=data["evento"],
                            data=data_evento,
                            frente_responsavel=data["frente_responsavel"],
                            meta_interna=data["meta_interna"],
                            defaults={"estado": data["estado"]},
                        )
                        evento_cache[evento_key] = evento_obj
                    else:
                        evento_obj = evento_cache[evento_key]

                    # 4. Instanciação da Participação
                    participacoes_to_create.append(
                        Participacao(
                            codigo=data["codigo"],
                            pessoa=pessoa,
                            evento=evento_obj,
                            tipo_participante=data["tipo_participante"],
                            instituicao=instituicao,
                        )
                    )

                # Persistência em lote de alta performance
                Participacao.objects.bulk_create(
                    participacoes_to_create,
                    batch_size=1000,
                )

                return ImportResult(
                    success=True,
                    total_imported=len(participacoes_to_create),
                    errors=[],
                )

        except Exception as exc:
            return ImportResult(
                success=False,
                total_imported=0,
                errors=[f"Falha na transação de importação: {exc}"],
            )
