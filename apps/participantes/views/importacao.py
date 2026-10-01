"""
Controladores web (CBVs finas) para o fluxo de importação do SIPAC.
Segue o padrão de Thin Views: delega leitura, validação e persistência
à camada de serviço (ImportacaoService).
"""

import json
from pathlib import Path
import uuid
from django.conf import settings
from django.contrib import messages
from django.core.paginator import Paginator
from django.shortcuts import redirect
from django.urls import reverse_lazy
from django.views import View
from django.views.generic import FormView, TemplateView
from apps.participantes.forms.importacao import ImportacaoUploadForm
from apps.participantes.services.importacao.service import ImportacaoService


def get_import_dir() -> Path:
    """Retorna o diretório seguro para armazenamento transitório das planilhas."""
    import_dir = Path(settings.MEDIA_ROOT) / "imports"
    import_dir.mkdir(parents=True, exist_ok=True)
    return import_dir


class ImportacaoUploadView(FormView):
    """
    CBV para envio do arquivo .xlsx e execução da Fase 1 (Preview).
    Processa a planilha sem realizar nenhuma alteração no banco de dados.
    """

    template_name = "participantes/importacao/upload.html"
    form_class = ImportacaoUploadForm
    success_url = reverse_lazy("participantes:importacao_preview")

    def form_valid(self, form):
        arquivo = form.cleaned_data["arquivo"]
        import_id = str(uuid.uuid4())
        import_dir = get_import_dir()

        # Salva o arquivo temporário em disco de forma segura
        file_path = import_dir / f"{import_id}.xlsx"
        with open(file_path, "wb+") as destination:
            for chunk in arquivo.chunks():
                destination.write(chunk)

        try:
            service = ImportacaoService()
            preview = service.processar_preview(file_path)

            # Persiste os dados processados em arquivo JSON transitório
            json_path = import_dir / f"{import_id}.json"
            preview_data = {
                "import_id": import_id,
                "filename": arquivo.name,
                "total_rows": preview.total_rows,
                "valid_rows": preview.valid_rows,
                "invalid_rows": preview.invalid_rows,
                "error_summary": preview.error_summary,
                "rows": [r.to_dict() for r in preview.rows],
            }
            with open(json_path, "w", encoding="utf-8") as f:
                json.dump(preview_data, f, ensure_ascii=False, default=str)

            # Armazena apenas chaves e sumário leve na sessão do usuário
            self.request.session["current_import_id"] = import_id
            self.request.session["import_preview_summary"] = {
                "import_id": import_id,
                "filename": arquivo.name,
                "total_rows": preview.total_rows,
                "valid_rows": preview.valid_rows,
                "invalid_rows": preview.invalid_rows,
                "error_summary": preview.error_summary,
            }

            messages.info(
                self.request,
                f"Arquivo '{arquivo.name}' analisado com sucesso! Confira o diagnóstico abaixo antes de confirmar a gravação.",
            )
            return redirect(self.success_url)

        except Exception as exc:
            # Em caso de erro na leitura/processamento, remove o arquivo salvo
            if file_path.exists():
                file_path.unlink()
            messages.error(
                self.request,
                f"Erro ao processar a planilha: {exc}",
            )
            return self.form_invalid(form)


class ImportacaoPreviewView(TemplateView):
    """
    CBV para exibição do diagnóstico pré-importação.
    Apresenta KPIs de qualidade, tabela paginada e filtros por status (todos/válidos/inválidos).
    """

    template_name = "participantes/importacao/preview.html"

    def get(self, request, *args, **kwargs):
        import_id = request.session.get("current_import_id")
        if not import_id:
            messages.warning(
                request,
                "Nenhum diagnóstico de importação ativo. Por favor, envie uma planilha.",
            )
            return redirect("participantes:importacao_upload")

        json_path = get_import_dir() / f"{import_id}.json"
        if not json_path.exists():
            messages.warning(
                request,
                "Os dados da sessão de importação expiraram. Por favor, envie o arquivo novamente.",
            )
            return redirect("participantes:importacao_upload")

        return super().get(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        import_id = self.request.session.get("current_import_id")
        json_path = get_import_dir() / f"{import_id}.json"

        with open(json_path, "r", encoding="utf-8") as f:
            preview_data = json.load(f)

        # Filtro de exibição por status
        status_filter = self.request.GET.get("status", "todos")
        all_rows = preview_data.get("rows", [])

        if status_filter == "validos":
            filtered_rows = [r for r in all_rows if r["is_valid"]]
        elif status_filter == "invalidos":
            filtered_rows = [r for r in all_rows if not r["is_valid"]]
        else:
            filtered_rows = all_rows
            status_filter = "todos"

        # Paginação das linhas (50 por página para performance ágil)
        paginator = Paginator(filtered_rows, 50)
        page_number = self.request.GET.get("page", 1)
        page_obj = paginator.get_page(page_number)

        context.update(
            {
                "import_id": import_id,
                "filename": preview_data.get("filename"),
                "total_rows": preview_data.get("total_rows", 0),
                "valid_rows": preview_data.get("valid_rows", 0),
                "invalid_rows": preview_data.get("invalid_rows", 0),
                "error_summary": preview_data.get("error_summary", {}),
                "status_filter": status_filter,
                "page_obj": page_obj,
                "total_filtered": len(filtered_rows),
                "can_confirm": preview_data.get("valid_rows", 0) > 0,
            }
        )
        return context


class ImportacaoConfirmarView(View):
    """
    CBV para acionar a Fase 2: Persistência Transacional no Banco de Dados.
    Aceita estritamente requisições POST com CSRF.
    """

    def post(self, request, *args, **kwargs):
        import_id = request.session.get("current_import_id")
        if not import_id:
            messages.error(
                request,
                "Sessão de importação expirada. Por favor, envie o arquivo novamente.",
            )
            return redirect("participantes:importacao_upload")

        json_path = get_import_dir() / f"{import_id}.json"
        if not json_path.exists():
            messages.error(
                request,
                "Arquivo de diagnóstico não encontrado. Por favor, reinicie a importação.",
            )
            return redirect("participantes:importacao_upload")

        with open(json_path, "r", encoding="utf-8") as f:
            preview_data = json.load(f)

        # Extrai apenas as linhas válidas para envio ao DatabaseImporter
        valid_rows = [
            row["data"] for row in preview_data.get("rows", []) if row.get("is_valid")
        ]

        if not valid_rows:
            messages.error(
                request,
                "Não existem registros válidos para importar neste arquivo.",
            )
            return redirect("participantes:importacao_preview")

        service = ImportacaoService()
        result = service.executar_importacao(valid_rows)

        if result.success:
            # Limpa arquivos transitórios
            excel_path = get_import_dir() / f"{import_id}.xlsx"
            if excel_path.exists():
                excel_path.unlink()
            if json_path.exists():
                json_path.unlink()

            # Salva sumário do resultado na sessão e limpa import_id ativo
            request.session["import_result"] = {
                "success": True,
                "total_imported": result.total_imported,
                "filename": preview_data.get("filename"),
                "total_original": preview_data.get("total_rows", 0),
                "invalid_discarded": preview_data.get("invalid_rows", 0),
            }
            if "current_import_id" in request.session:
                del request.session["current_import_id"]
            if "import_preview_summary" in request.session:
                del request.session["import_preview_summary"]

            messages.success(
                request,
                f"Importação realizada com sucesso! {result.total_imported} participações foram gravadas no banco de dados.",
            )
            return redirect("participantes:importacao_resultado")
        else:
            messages.error(
                request,
                f"Erro durante a gravação no banco: {'; '.join(result.errors)}",
            )
            return redirect("participantes:importacao_preview")

    def get(self, request, *args, **kwargs):
        """Redireciona tentativas de acesso GET para a tela de prévia."""
        return redirect("participantes:importacao_preview")


class ImportacaoResultadoView(TemplateView):
    """
    CBV para exibição da tela de sucesso após conclusão da importação.
    """

    template_name = "participantes/importacao/resultado.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        resultado = self.request.session.get("import_result")
        context["resultado"] = resultado
        return context


class ImportacaoCancelarView(View):
    """
    CBV para cancelamento voluntário do lote de importação.
    Remove os arquivos transitórios e limpa a sessão.
    """

    def post(self, request, *args, **kwargs):
        import_id = request.session.get("current_import_id")
        if import_id:
            excel_path = get_import_dir() / f"{import_id}.xlsx"
            json_path = get_import_dir() / f"{import_id}.json"
            if excel_path.exists():
                excel_path.unlink()
            if json_path.exists():
                json_path.unlink()
            del request.session["current_import_id"]

        if "import_preview_summary" in request.session:
            del request.session["import_preview_summary"]

        messages.info(request, "Processo de importação cancelado pelo usuário.")
        return redirect("participantes:importacao_upload")
