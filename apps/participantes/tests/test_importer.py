"""
Testes de integração para a camada de persistência e orquestração do SIPAC.
Valida o DatabaseImporter (transações atômicas, upsert de Pessoa, deduplicação de Evento,
rollback integral em falhas) e a fachada ImportacaoService (Fase 1 Preview e Fase 2 Importer).
"""

from datetime import date
import io
from openpyxl import Workbook
from django.test import TestCase
from apps.participantes.models import (
    ComunidadeTradicional,
    Estado,
    FrenteResponsavel,
    Genero,
    Instituicao,
    MetaInterna,
    Participacao,
    Pessoa,
    TipoParticipante,
    Evento,
)
from apps.participantes.services.importacao import (
    DatabaseImporter,
    ImportacaoService,
    ProcessedRow,
)


class DatabaseImporterTestCase(TestCase):
    """Testes de persistência transacional com DatabaseImporter."""

    def setUp(self):
        self.importer = DatabaseImporter()
        self.valid_row_1 = {
            "codigo": "PART-00101",
            "evento": "Capacitação ATER Florestal",
            "frente_responsavel": FrenteResponsavel.ATER.value,
            "meta_interna": MetaInterna.ENCONTROS_TEMATICOS.value,
            "data_evento": date(2026, 7, 10),
            "ano": 2026,
            "nome": "Marcos Vinicius",
            "cpf": "00208935150",
            "data_nascimento": date(1988, 4, 15),
            "genero": Genero.MASCULINO.value,
            "comunidade_tradicional": ComunidadeTradicional.RIBEIRINHO.value,
            "tipo_participante": TipoParticipante.PRODUTOR_RURAL.value,
            "estado": Estado.AM.value,
            "instituicao": "EMBRAPA",
        }
        self.valid_row_2 = {
            "codigo": "PART-00102",
            "evento": "Capacitação ATER Florestal",  # Mesmo evento
            "frente_responsavel": FrenteResponsavel.ATER.value,
            "meta_interna": MetaInterna.ENCONTROS_TEMATICOS.value,
            "data_evento": date(2026, 7, 10),
            "ano": 2026,
            "nome": "Fernanda Lima",
            "cpf": "81060360225",
            "data_nascimento": None,  # Nascimento nulo legítimo
            "genero": Genero.FEMININO.value,
            "comunidade_tradicional": ComunidadeTradicional.NAO.value,
            "tipo_participante": TipoParticipante.TECNICO_ATER.value,
            "estado": Estado.AM.value,
            "instituicao": None,  # Instituição nula legítima
        }

    def test_persist_atomic_success(self):
        """Valida inserção atômica bem sucedida com relacionamentos corretos."""
        rows = [self.valid_row_1, self.valid_row_2]
        result = self.importer.persist_atomic(rows)

        self.assertTrue(result.success)
        self.assertEqual(result.total_imported, 2)
        self.assertEqual(len(result.errors), 0)

        # Checa registros criados
        self.assertEqual(Pessoa.objects.count(), 2)
        self.assertEqual(Evento.objects.count(), 1)  # Deduplicação bem sucedida
        self.assertEqual(Instituicao.objects.count(), 1)  # Apenas EMBRAPA criada
        self.assertEqual(Participacao.objects.count(), 2)

        # Checa integridade de chaves estrangeiras
        part1 = Participacao.objects.get(codigo="PART-00101")
        self.assertEqual(part1.pessoa.cpf, "00208935150")
        self.assertEqual(part1.pessoa.nome, "Marcos Vinicius")
        self.assertEqual(part1.instituicao.nome, "EMBRAPA")
        self.assertEqual(part1.evento.nome, "Capacitação ATER Florestal")

        part2 = Participacao.objects.get(codigo="PART-00102")
        self.assertEqual(part2.pessoa.cpf, "81060360225")
        self.assertIsNone(part2.instituicao)
        self.assertEqual(part2.evento, part1.evento)

    def test_pessoa_update_or_create(self):
        """Valida que linhas subsequentes com mesmo CPF atualizam dados de Pessoa."""
        # Primeira inserção
        self.importer.persist_atomic([self.valid_row_1])
        pessoa = Pessoa.objects.get(cpf="00208935150")
        self.assertEqual(pessoa.nome, "Marcos Vinicius")

        # Segunda linha com mesmo CPF e nome corrigido/atualizado
        row_atualizada = dict(self.valid_row_1)
        row_atualizada["codigo"] = "PART-00103"
        row_atualizada["nome"] = "Marcos Vinicius Silva"
        row_atualizada["data_evento"] = date(2026, 7, 11)  # Outro evento

        result = self.importer.persist_atomic([row_atualizada])
        self.assertTrue(result.success)

        # Pessoa não duplicou, mas teve o nome atualizado
        self.assertEqual(Pessoa.objects.count(), 1)
        pessoa.refresh_from_db()
        self.assertEqual(pessoa.nome, "Marcos Vinicius Silva")
        self.assertEqual(Participacao.objects.count(), 2)

    def test_rollback_on_failure(self):
        """Valida rollback total se houver colisão de chave primária/código."""
        # Insere a primeira linha
        self.importer.persist_atomic([self.valid_row_1])
        self.assertEqual(Participacao.objects.count(), 1)

        # Tenta inserir lote onde a segunda linha tenta recriar o mesmo código PART-00101
        conflicting_row = dict(self.valid_row_2)
        conflicting_row["codigo"] = "PART-00101"  # Viola unique=True de Participacao

        new_row = {
            "codigo": "PART-00104",
            "evento": "Oficina Nova",
            "frente_responsavel": FrenteResponsavel.CAMPO.value,
            "meta_interna": MetaInterna.DCS.value,
            "data_evento": date(2026, 9, 1),
            "ano": 2026,
            "nome": "Ana Paula",
            "cpf": "94908990204",
            "data_nascimento": None,
            "genero": Genero.FEMININO.value,
            "comunidade_tradicional": ComunidadeTradicional.NAO.value,
            "tipo_participante": TipoParticipante.PRODUTOR_RURAL.value,
            "estado": Estado.PA.value,
            "instituicao": "NOVA_INST",
        }

        # Submete lote com conflito
        result = self.importer.persist_atomic([new_row, conflicting_row])
        self.assertFalse(result.success)
        self.assertEqual(result.total_imported, 0)
        self.assertTrue(len(result.errors) > 0)

        # new_row NÃO deve ter sido gravada no banco devido ao rollback
        self.assertFalse(Participacao.objects.filter(codigo="PART-00104").exists())
        self.assertFalse(Pessoa.objects.filter(cpf="94908990204").exists())
        self.assertFalse(Instituicao.objects.filter(nome="NOVA_INST").exists())


class ImportacaoServiceTestCase(TestCase):
    """Testes da fachada ImportacaoService (Fase 1 e Fase 2)."""

    def _create_test_workbook_bytes(self) -> io.BytesIO:
        """Cria um arquivo .xlsx em memória com 2 linhas válidas e 1 linha inválida."""
        wb = Workbook()
        ws = wb.active
        ws.title = "Participações"

        # Cabeçalhos canônicos da planilha
        headers = [
            "COD PARTICIPAÇÃO",
            "EVENTO",
            "FRENTE RESPONSÁVAEL",
            "METAS INTERNAS",
            "DATA DA ATIVIDADE",
            "ANO",
            "NOME DO PARTICIPANTE",
            "CPF",
            "DATA DE NASCIMENTO",
            "GÊNERO",
            "FAZ PARTE DE COMUNIDADE TRADICIONAL",
            "TIPO DO PARTICIPANTE",
            "ESTADO",
            "INSTITUIÇÃO",
        ]
        ws.append(headers)

        # Linha 1: 100% Válida
        ws.append(
            [
                "PART-01001",
                "Seminário de Agroecologia",
                "CAMPO",
                "DCs",
                "15/06/2026",
                2026,
                "Lucas Mendes",
                "00208935150",
                "20/05/1992",
                "Masculino",
                "Ribeirinho",
                "Produtor Rural",
                "Amazonas",
                "EMBRAPA",
            ]
        )

        # Linha 2: Inválida (CPF com DV errado e data do evento ausente)
        ws.append(
            [
                "PART-01002",
                "Seminário de Agroecologia",
                "CAMPO",
                "DCs",
                "NÃO INFORMADO",
                2026,
                "Juliana Rocha",
                "11111111111",
                "10/02/1985",
                "Feminino",
                "Não",
                "Produtor Rural",
                "Amazonas",
                "-",
            ]
        )

        # Linha 3: 100% Válida
        ws.append(
            [
                "PART-01003",
                "Oficina de Bioeconomia",
                "ATER",
                "Encontros Temáticos/ Seminários (inclui GGEs)",
                "20/08/2026",
                2026,
                "Beatriz Santos",
                "81060360225",
                "12/11/1990",
                "Feminino",
                "Quilombola",
                "Técnico de ATER",
                "Pará",
                "IABS",
            ]
        )

        stream = io.BytesIO()
        wb.save(stream)
        stream.seek(0)
        return stream

    def test_service_processar_preview_phase_1(self):
        """Fase 1: Executa leitura e pré-validação sem persistir nada no banco."""
        excel_stream = self._create_test_workbook_bytes()
        service = ImportacaoService()

        preview = service.processar_preview(excel_stream)

        # Verifica totais diagnósticos
        self.assertEqual(preview.total_rows, 3)
        self.assertEqual(preview.valid_rows, 2)
        self.assertEqual(preview.invalid_rows, 1)

        # Garante que NENHUM dado foi persistido no banco
        self.assertEqual(Pessoa.objects.count(), 0)
        self.assertEqual(Evento.objects.count(), 0)
        self.assertEqual(Instituicao.objects.count(), 0)
        self.assertEqual(Participacao.objects.count(), 0)

        # Verifica identificação correta de erros na linha 2
        linha_invalida = preview.rows[1]
        self.assertFalse(linha_invalida.is_valid)
        error_codes = [e.code for e in linha_invalida.errors]
        self.assertIn("repeated_digits", error_codes)
        self.assertIn("missing_event_date", error_codes)

    def test_service_executar_importacao_phase_2(self):
        """Fase 2: Grava apenas as linhas válidas sob transação atômica."""
        excel_stream = self._create_test_workbook_bytes()
        service = ImportacaoService()

        # Fase 1
        preview = service.processar_preview(excel_stream)
        valid_rows = [r for r in preview.rows if r.is_valid]
        self.assertEqual(len(valid_rows), 2)

        # Fase 2
        result = service.executar_importacao(valid_rows)

        self.assertTrue(result.success)
        self.assertEqual(result.total_imported, 2)
        self.assertEqual(len(result.errors), 0)

        # Persistência confirmada no banco
        self.assertEqual(Participacao.objects.count(), 2)
        self.assertEqual(Pessoa.objects.count(), 2)
        self.assertEqual(Evento.objects.count(), 2)
        self.assertEqual(Instituicao.objects.count(), 2)
        self.assertTrue(Participacao.objects.filter(codigo="PART-01001").exists())
        self.assertTrue(Participacao.objects.filter(codigo="PART-01003").exists())
        self.assertFalse(Participacao.objects.filter(codigo="PART-01002").exists())
