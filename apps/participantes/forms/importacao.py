"""
Formulário de upload para importação de planilhas de participações.
Valida extensão (.xlsx), limite de tamanho e cabeçalho binário (ZIP/OOXML).
"""

from django import forms
from django.core.exceptions import ValidationError

# Limite máximo padrão para upload da planilha: 25 MB
MAX_UPLOAD_SIZE_BYTES: int = 25 * 1024 * 1024
MAX_UPLOAD_SIZE_MB: int = 25

ALLOWED_EXTENSIONS: tuple[str, ...] = (".xlsx",)


class ImportacaoUploadForm(forms.Form):
    """
    Formulário para envio de planilha Excel (.xlsx) para auditoria e importação.
    """

    arquivo = forms.FileField(
        label="Planilha de Participações (.xlsx)",
        help_text=f"Envie o arquivo no formato Microsoft Excel (.xlsx). Tamanho máximo: {MAX_UPLOAD_SIZE_MB} MB.",
        widget=forms.FileInput(
            attrs={
                "class": "form-control",
                "accept": ".xlsx, application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                "id": "id_arquivo_planilha",
            }
        ),
    )

    def clean_arquivo(self):
        arquivo = self.cleaned_data.get("arquivo")

        if not arquivo:
            raise ValidationError(
                "Nenhum arquivo foi selecionado.",
                code="missing_file",
            )

        # 1. Validação de tamanho zero (arquivo vazio)
        if arquivo.size == 0:
            raise ValidationError(
                "O arquivo enviado está vazio (0 bytes).",
                code="empty_file",
            )

        # 2. Validação de tamanho máximo
        if arquivo.size > MAX_UPLOAD_SIZE_BYTES:
            size_mb = arquivo.size / (1024 * 1024)
            raise ValidationError(
                f"O arquivo selecionado possui {size_mb:.1f} MB, excedendo o limite máximo de {MAX_UPLOAD_SIZE_MB} MB.",
                code="file_too_large",
            )

        # 3. Validação de extensão estrita (.xlsx)
        filename = arquivo.name.lower()
        if not filename.endswith(ALLOWED_EXTENSIONS):
            if filename.endswith(".xls"):
                raise ValidationError(
                    "O formato legado .xls não é suportado. Por favor, salve a planilha como .xlsx antes do envio.",
                    code="legacy_xls_not_supported",
                )
            if filename.endswith(".csv"):
                raise ValidationError(
                    "Arquivos CSV não são suportados diretamente. Por favor, utilize o formato Excel (.xlsx).",
                    code="csv_not_supported",
                )
            raise ValidationError(
                "Formato de arquivo não suportado. O arquivo deve ter a extensão .xlsx.",
                code="invalid_extension",
            )

        # 4. Verificação de integridade básica (arquivos .xlsx são contêineres ZIP iniciando com b'PK')
        try:
            arquivo.seek(0)
            header = arquivo.read(4)
            arquivo.seek(0)  # Rebobina ponteiro para leitura subsequente
            if not header.startswith(b"PK"):
                raise ValidationError(
                    "O arquivo enviado não possui uma estrutura válida de planilha Excel (.xlsx).",
                    code="corrupted_or_fake_xlsx",
                )
        except Exception as exc:
            if isinstance(exc, ValidationError):
                raise
            raise ValidationError(
                "Não foi possível ler os metadados do arquivo enviado.",
                code="read_error",
            ) from exc

        return arquivo
