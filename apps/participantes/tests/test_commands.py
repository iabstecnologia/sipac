"""
Testes automatizados para os comandos de gerenciamento CLI do SIPAC.
Valida o comando importar_planilha com dry-run, tratamento de erros e auditoria.
"""

import io
from pathlib import Path
import tempfile
from openpyxl import Workbook
from django.core.management import call_command
from django.core.management.base import CommandError
from django.test import TestCase
from apps.participantes.models import Participacao, Pessoa


class ImportarPlanilhaCommandTestCase(TestCase):
    """Testes para o comando python manage.py importar_planilha."""

    def _create_sample_excel(self) -> str:
        """Cria um arquivo .xlsx temporário para testes."""
        wb = Workbook()
        ws = wb.active
        ws.title = "Planilha"

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
        ws.append(
            [
                "PART-99001",
                "Seminário Manejo Florestal",
                "CAMPO",
                "DCs",
                "15/06/2026",
                2026,
                "Lucas Silva",
                "00208935150",
                "20/05/1992",
                "Masculino",
                "Ribeirinho",
                "Produtor Rural",
                "Amazonas",
                "EMBRAPA",
            ]
        )

        tmp = tempfile.NamedTemporaryFile(suffix=".xlsx", delete=False)
        wb.save(tmp.name)
        tmp.close()
        return tmp.name

    def test_command_file_not_found(self):
        """Arquivo inexistente deve lançar CommandError amigável."""
        with self.assertRaises(CommandError) as ctx:
            call_command("importar_planilha", "arquivo_que_nao_existe_123.xlsx")
        self.assertIn("Arquivo não encontrado", str(ctx.exception))

    def test_command_dry_run(self):
        """Modo --dry-run não deve gravar nenhum registro no banco."""
        sample_path = self._create_sample_excel()
        out = io.StringIO()

        call_command("importar_planilha", sample_path, "--dry-run", stdout=out)

        output = out.getvalue()
        self.assertIn("MODO DRY-RUN ATIVO", output)
        self.assertIn("Linhas válidas para carga:    1", output)
        self.assertIn("Dry-run concluído com sucesso", output)
        self.assertEqual(Participacao.objects.count(), 0)

        Path(sample_path).unlink(missing_ok=True)

    def test_command_full_import_and_clear(self):
        """Execução completa deve persistir registros e exibir auditoria do banco."""
        sample_path = self._create_sample_excel()
        out = io.StringIO()

        call_command("importar_planilha", sample_path, "--clear", stdout=out)

        output = out.getvalue()
        self.assertIn("Total de participações gravadas: 1", output)
        self.assertIn("AUDITORIA FINAL DO BANCO DE DADOS", output)
        self.assertEqual(Participacao.objects.count(), 1)
        self.assertEqual(Pessoa.objects.count(), 1)

        Path(sample_path).unlink(missing_ok=True)
