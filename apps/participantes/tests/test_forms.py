"""
Testes unitários para os formulários de entrada de dados do SIPAC.
Valida o formulário ImportacaoUploadForm contra extensões, limites de tamanho e integridade binária.
"""

import io
from openpyxl import Workbook
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase
from apps.participantes.forms.importacao import (
    MAX_UPLOAD_SIZE_BYTES,
    ImportacaoUploadForm,
)


class ImportacaoUploadFormTestCase(TestCase):
    """Bateria de testes para ImportacaoUploadForm."""

    def _generate_valid_xlsx_file(self) -> SimpleUploadedFile:
        """Gera um arquivo .xlsx mínimo válido em memória."""
        wb = Workbook()
        ws = wb.active
        ws.title = "Planilha1"
        ws.append(["COLUNA_1", "COLUNA_2"])
        ws.append(["VALOR_1", "VALOR_2"])
        stream = io.BytesIO()
        wb.save(stream)
        stream.seek(0)
        return SimpleUploadedFile(
            name="participacoes_valido.xlsx",
            content=stream.read(),
            content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        )

    def test_form_valid_xlsx(self):
        """Arquivo .xlsx legítimo com dados e cabeçalho ZIP válido deve ser aceito."""
        uploaded_file = self._generate_valid_xlsx_file()
        form = ImportacaoUploadForm(data={}, files={"arquivo": uploaded_file})
        self.assertTrue(form.is_valid(), f"Erros do form: {form.errors}")
        cleaned_file = form.cleaned_data["arquivo"]
        self.assertEqual(cleaned_file.name, "participacoes_valido.xlsx")

    def test_form_missing_file(self):
        """Submissão sem arquivo deve gerar erro de campo obrigatório."""
        form = ImportacaoUploadForm(data={}, files={})
        self.assertFalse(form.is_valid())
        self.assertIn("arquivo", form.errors)

    def test_form_empty_file(self):
        """Arquivo com 0 bytes deve ser rejeitado."""
        empty_file = SimpleUploadedFile(
            name="vazio.xlsx",
            content=b"",
            content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        )
        form = ImportacaoUploadForm(data={}, files={"arquivo": empty_file})
        self.assertFalse(form.is_valid())
        self.assertIn("O arquivo enviado está vazio", form.errors["arquivo"][0])

    def test_form_invalid_extension_csv(self):
        """Arquivo com extensão .csv deve ser rejeitado com mensagem específica."""
        csv_file = SimpleUploadedFile(
            name="dados.csv",
            content=b"col1,col2\nval1,val2",
            content_type="text/csv",
        )
        form = ImportacaoUploadForm(data={}, files={"arquivo": csv_file})
        self.assertFalse(form.is_valid())
        self.assertIn("Arquivos CSV não são suportados", form.errors["arquivo"][0])

    def test_form_invalid_extension_xls(self):
        """Arquivo com extensão legada .xls deve ser rejeitado com mensagem explicativa."""
        xls_file = SimpleUploadedFile(
            name="antigo.xls",
            content=b"fake content",
            content_type="application/vnd.ms-excel",
        )
        form = ImportacaoUploadForm(data={}, files={"arquivo": xls_file})
        self.assertFalse(form.is_valid())
        self.assertIn("O formato legado .xls não é suportado", form.errors["arquivo"][0])

    def test_form_invalid_extension_pdf(self):
        """Outras extensões não permitidas devem ser barradas."""
        pdf_file = SimpleUploadedFile(
            name="documento.pdf",
            content=b"%PDF-1.4...",
            content_type="application/pdf",
        )
        form = ImportacaoUploadForm(data={}, files={"arquivo": pdf_file})
        self.assertFalse(form.is_valid())
        self.assertIn("Formato de arquivo não suportado", form.errors["arquivo"][0])

    def test_form_fake_xlsx_corrupted(self):
        """Arquivo com extensão .xlsx mas sem cabeçalho binário PK deve ser rejeitado."""
        fake_file = SimpleUploadedFile(
            name="fraude.xlsx",
            content=b"Este nao eh um zip nem excel",
            content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        )
        form = ImportacaoUploadForm(data={}, files={"arquivo": fake_file})
        self.assertFalse(form.is_valid())
        self.assertIn("não possui uma estrutura válida", form.errors["arquivo"][0])

    def test_form_file_too_large(self):
        """Arquivo que excede o limite máximo configurado deve ser rejeitado."""
        # Cria um arquivo simulado com tamanho artificial excedendo MAX_UPLOAD_SIZE_BYTES
        oversized_content = b"PK\x03\x04" + b"0" * 100
        oversized_file = SimpleUploadedFile(
            name="pesado.xlsx",
            content=oversized_content,
            content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        )
        # Simula tamanho além do limite
        oversized_file.size = MAX_UPLOAD_SIZE_BYTES + 1024

        form = ImportacaoUploadForm(data={}, files={"arquivo": oversized_file})
        self.assertFalse(form.is_valid())
        self.assertIn("excedendo o limite máximo", form.errors["arquivo"][0])
