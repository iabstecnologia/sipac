"""
Testes automatizados para os controladores web (CBVs) do SIPAC.
Valida o fluxo completo de upload (Fase 1), exibição de diagnóstico (Preview),
confirmação e persistência atômica (Fase 2) e cancelamento.
"""

from datetime import date
import io
import json
from pathlib import Path
from openpyxl import Workbook
from django.conf import settings
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import Client, TestCase
from django.urls import reverse
from apps.participantes.models import Participacao, Pessoa


class ImportacaoViewsTestCase(TestCase):
    """Testes de integração para as CBVs de importação."""

    def setUp(self):
        self.client = Client()

    def _generate_valid_workbook(self) -> SimpleUploadedFile:
        """Gera um arquivo .xlsx válido com 2 linhas válidas e 1 inválida."""
        wb = Workbook()
        ws = wb.active
        ws.title = "Participações"

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

        # Linha 1 válida
        ws.append(
            [
                "PART-09001",
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

        # Linha 2 inválida (CPF inválido e data não informada)
        ws.append(
            [
                "PART-09002",
                "Seminário Manejo Florestal",
                "CAMPO",
                "DCs",
                "NÃO INFORMADO",
                2026,
                "Pedro Alves",
                "00000000000",
                "29/061995",  # Data corrompida -> UnparseableDate
                "Masculino",
                "Não",
                "Produtor Rural",
                "Amazonas",
                "-",
            ]
        )

        # Linha 3 válida
        ws.append(
            [
                "PART-09003",
                "Encontro Regional ATER",
                "ATER",
                "Encontros Temáticos/ Seminários (inclui GGEs)",
                "20/08/2026",
                2026,
                "Mariana Costa",
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
        return SimpleUploadedFile(
            name="planilha_teste.xlsx",
            content=stream.read(),
            content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        )

    def test_upload_view_get(self):
        """GET /importacao/ deve carregar o formulário com status 200."""
        response = self.client.get(reverse("participantes:importacao_upload"))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "participantes/importacao/upload.html")
        self.assertIn("form", response.context)

    def test_upload_view_post_valid_file(self):
        """POST com arquivo válido executa a Fase 1 e redireciona para a prévia."""
        uploaded_file = self._generate_valid_workbook()
        response = self.client.post(
            reverse("participantes:importacao_upload"),
            {"arquivo": uploaded_file},
        )
        self.assertRedirects(response, reverse("participantes:importacao_preview"))

        # Sessão deve conter o ID da importação e o resumo
        session = self.client.session
        self.assertIn("current_import_id", session)
        self.assertIn("import_preview_summary", session)
        summary = session["import_preview_summary"]
        self.assertEqual(summary["total_rows"], 3)
        self.assertEqual(summary["valid_rows"], 2)
        self.assertEqual(summary["invalid_rows"], 1)

    def test_upload_view_post_invalid_file(self):
        """POST sem arquivo ou com arquivo inválido deve re-renderizar o form com erros."""
        invalid_file = SimpleUploadedFile("teste.csv", b"col1,col2", content_type="text/csv")
        response = self.client.post(
            reverse("participantes:importacao_upload"),
            {"arquivo": invalid_file},
        )
        self.assertEqual(response.status_code, 200)
        self.assertFormError(response.context["form"], "arquivo", "Arquivos CSV não são suportados diretamente. Por favor, utilize o formato Excel (.xlsx).")

    def test_preview_view_without_session(self):
        """Acesso à prévia sem sessão ativa deve redirecionar para a tela de upload."""
        response = self.client.get(reverse("participantes:importacao_preview"))
        self.assertRedirects(response, reverse("participantes:importacao_upload"))

    def test_preview_view_with_session_and_filters(self):
        """Acesso à prévia com sessão ativa renderiza a tabela paginada e respeita filtros."""
        # 1. Faz upload inicial
        uploaded_file = self._generate_valid_workbook()
        self.client.post(
            reverse("participantes:importacao_upload"),
            {"arquivo": uploaded_file},
        )

        # 2. Acessa a prévia (filtro padrão: todos)
        response = self.client.get(reverse("participantes:importacao_preview"))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "participantes/importacao/preview.html")
        self.assertEqual(response.context["total_rows"], 3)
        self.assertEqual(response.context["valid_rows"], 2)
        self.assertEqual(response.context["invalid_rows"], 1)
        self.assertEqual(len(response.context["page_obj"]), 3)

        # 3. Filtro apenas válidos
        res_validos = self.client.get(
            reverse("participantes:importacao_preview"),
            {"status": "validos"},
        )
        self.assertEqual(res_validos.status_code, 200)
        self.assertEqual(len(res_validos.context["page_obj"]), 2)

        # 4. Filtro apenas inconsistentes
        res_invalidos = self.client.get(
            reverse("participantes:importacao_preview"),
            {"status": "invalidos"},
        )
        self.assertEqual(res_invalidos.status_code, 200)
        self.assertEqual(len(res_invalidos.context["page_obj"]), 1)

    def test_confirmar_view_post_success(self):
        """POST /importacao/confirmar/ grava linhas válidas sob transação e redireciona para resultado."""
        # 1. Faz upload
        uploaded_file = self._generate_valid_workbook()
        self.client.post(
            reverse("participantes:importacao_upload"),
            {"arquivo": uploaded_file},
        )

        # 2. Confirmação da importação
        response = self.client.post(reverse("participantes:importacao_confirmar"))
        self.assertRedirects(response, reverse("participantes:importacao_resultado"))

        # 3. Verifica persistência no banco
        self.assertEqual(Participacao.objects.count(), 2)
        self.assertEqual(Pessoa.objects.count(), 2)
        self.assertTrue(Participacao.objects.filter(codigo="PART-09001").exists())
        self.assertTrue(Participacao.objects.filter(codigo="PART-09003").exists())
        self.assertFalse(Participacao.objects.filter(codigo="PART-09002").exists())

        # 4. Verifica resultado na tela de resultado
        res_resultado = self.client.get(reverse("participantes:importacao_resultado"))
        self.assertEqual(res_resultado.status_code, 200)
        self.assertTemplateUsed(res_resultado, "participantes/importacao/resultado.html")
        self.assertEqual(res_resultado.context["resultado"]["total_imported"], 2)

    def test_confirmar_view_get_redirects_to_preview(self):
        """GET em confirmar deve redirecionar para a prévia (apenas POST permitido)."""
        uploaded_file = self._generate_valid_workbook()
        self.client.post(
            reverse("participantes:importacao_upload"),
            {"arquivo": uploaded_file},
        )
        response = self.client.get(reverse("participantes:importacao_confirmar"))
        self.assertRedirects(response, reverse("participantes:importacao_preview"))

    def test_cancelar_view_post(self):
        """POST em cancelar limpa a sessão e arquivos temporários e volta ao upload."""
        # 1. Upload
        uploaded_file = self._generate_valid_workbook()
        self.client.post(
            reverse("participantes:importacao_upload"),
            {"arquivo": uploaded_file},
        )
        import_id = self.client.session.get("current_import_id")
        self.assertIsNotNone(import_id)

        # 2. Cancelar
        response = self.client.post(reverse("participantes:importacao_cancelar"))
        self.assertRedirects(response, reverse("participantes:importacao_upload"))

        # 3. Sessão deve estar limpa
        session = self.client.session
        self.assertNotIn("current_import_id", session)


class DashboardViewTestCase(TestCase):
    """Testes de integração para a DashboardView."""

    def setUp(self):
        self.client = Client()

    def test_dashboard_view_get(self):
        """GET / deve renderizar o dashboard com status 200 e contexto completo."""
        response = self.client.get(reverse("participantes:home"))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "participantes/dashboard/index.html")

        # Verifica estruturas presentes no contexto
        self.assertIn("kpis", response.context)
        self.assertIn("ranking_estados", response.context)
        self.assertIn("ranking_eventos", response.context)
        self.assertIn("charts_data", response.context)
        self.assertIn("filter_options", response.context)
        self.assertIn("filters", response.context)
        self.assertIn("is_filtered", response.context)

    def test_dashboard_view_filtered(self):
        """GET /?estado=AM deve aplicar filtros e sinalizar is_filtered=True."""
        response = self.client.get(reverse("participantes:home"), {"estado": "AM"})
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.context["is_filtered"])
        self.assertEqual(response.context["filters"].estado, "AM")

