"""
Comando de linha de comando (CLI) para importação de planilhas de participações do SIPAC.
Permite execução automatizada, dry-run diagnóstica e auditoria de métricas no banco.
"""

from pathlib import Path
import time
from django.core.management.base import BaseCommand, CommandError
from apps.participantes.models import (
    Evento,
    Instituicao,
    Participacao,
    Pessoa,
)
from apps.participantes.services.importacao import ImportacaoService


class Command(BaseCommand):
    help = "Importa uma planilha de participações (.xlsx) aplicando o pipeline de 2 fases (Diagnóstico e Gravação Atômica)."

    def add_arguments(self, parser):
        parser.add_argument(
            "caminho_arquivo",
            nargs="?",
            default="sipac_participacoes.xlsx",
            type=str,
            help="Caminho para o arquivo .xlsx a ser importado (padrão: sipac_participacoes.xlsx).",
        )
        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="Executa apenas a Fase 1 de pré-validação diagnóstica, sem persistir nada no banco de dados.",
        )
        parser.add_argument(
            "--clear",
            action="store_true",
            help="Limpa todos os dados anteriores de Participação, Evento, Pessoa e Instituição antes da carga.",
        )
        parser.add_argument(
            "--report-invalid",
            action="store_true",
            help="Exibe no terminal a listagem detalhada de todas as linhas que apresentaram inconsistências.",
        )

    def handle(self, *args, **options):
        caminho_str = options["caminho_arquivo"]
        dry_run = options["dry_run"]
        clear_db = options["clear"]
        report_invalid = options["report_invalid"]

        file_path = Path(caminho_str).resolve()
        if not file_path.exists():
            raise CommandError(f"Arquivo não encontrado: '{file_path}'")

        self.stdout.write(self.style.NOTICE("=" * 70))
        self.stdout.write(self.style.NOTICE("SIPAC — Pipeline de Importação e Saneamento de Participações"))
        self.stdout.write(self.style.NOTICE("=" * 70))
        self.stdout.write(f"Arquivo de origem: {file_path.name}")
        self.stdout.write(f"Tamanho do arquivo: {file_path.stat().st_size / (1024 * 1024):.2f} MB")
        if dry_run:
            self.stdout.write(self.style.WARNING("MODO DRY-RUN ATIVO: Nenhuma alteração será feita no banco."))
        self.stdout.write("-" * 70)

        # 0. Limpeza prévia (se solicitada)
        if clear_db and not dry_run:
            self.stdout.write("Limpando registros existentes no banco de dados...")
            qtd_part, _ = Participacao.objects.all().delete()
            qtd_pes, _ = Pessoa.objects.all().delete()
            qtd_ev, _ = Evento.objects.all().delete()
            qtd_inst, _ = Instituicao.objects.all().delete()
            self.stdout.write(
                self.style.WARNING(
                    f"Banco limpo: {qtd_part} participações, {qtd_pes} pessoas, {qtd_ev} eventos, {qtd_inst} instituições removidos."
                )
            )
            self.stdout.write("-" * 70)

        # 1. Fase 1: Diagnóstico e Validação
        self.stdout.write("Iniciando FASE 1: Leitura streaming e pré-validação diagnóstica...")
        start_t1 = time.time()
        service = ImportacaoService()

        try:
            preview = service.processar_preview(file_path)
        except Exception as exc:
            raise CommandError(f"Erro fatal durante a leitura da planilha: {exc}") from exc

        duration_t1 = time.time() - start_t1
        self.stdout.write(self.style.SUCCESS(f"Fase 1 concluída em {duration_t1:.2f} segundos."))
        self.stdout.write(f"Total de linhas lidas:        {preview.total_rows:,}".replace(",", "."))
        self.stdout.write(self.style.SUCCESS(f"Linhas válidas para carga:    {preview.valid_rows:,}".replace(",", ".")))
        if preview.invalid_rows > 0:
            self.stdout.write(self.style.ERROR(f"Linhas com inconsistências:  {preview.invalid_rows:,}".replace(",", ".")))
        else:
            self.stdout.write(f"Linhas com inconsistências:  0")

        # Sumário de Erros Frequentes
        if preview.error_summary:
            self.stdout.write("\nPrincipais inconsistências identificadas:")
            for erro_msg, count in preview.error_summary.items():
                self.stdout.write(f"  • {erro_msg}: {count} ocorrências")

        # Relatório linha a linha de inconsistências (se solicitado)
        if report_invalid and preview.invalid_rows > 0:
            self.stdout.write("\n" + "-" * 70)
            self.stdout.write(self.style.ERROR("RELATÓRIO DETALHADO DE INCONSISTÊNCIAS:"))
            for r in preview.rows:
                if not r.is_valid:
                    erros_str = "; ".join(f"[{e.field}] {e.message}" for e in r.errors)
                    self.stdout.write(f"Linha {r.row_number:5d} | Código {r.codigo or 'N/A':10s} | Erros: {erros_str}")

        if dry_run:
            self.stdout.write("\n" + self.style.SUCCESS("Dry-run concluído com sucesso. Nenhuma gravação efetuada."))
            return

        if preview.valid_rows == 0:
            self.stdout.write(self.style.ERROR("\nNenhum registro válido apto para carga. Importação abortada."))
            return

        # 2. Fase 2: Persistência Atômica
        self.stdout.write("\n" + "-" * 70)
        self.stdout.write("Iniciando FASE 2: Persistência sob transação atômica completa...")
        start_t2 = time.time()

        valid_rows = [r for r in preview.rows if r.is_valid]
        result = service.executar_importacao(valid_rows)
        duration_t2 = time.time() - start_t2

        if not result.success:
            self.stdout.write(self.style.ERROR(f"FALHA NA TRANSAÇÃO: {result.errors}"))
            raise CommandError("A importação falhou e a transação foi revertida integralmente (Rollback).")

        self.stdout.write(self.style.SUCCESS(f"Fase 2 concluída em {duration_t2:.2f} segundos."))
        self.stdout.write(
            self.style.SUCCESS(f"Total de participações gravadas: {result.total_imported:,}".replace(",", "."))
        )

        # 3. Auditoria do Banco de Dados Pós-Importação
        self.stdout.write("\n" + "=" * 70)
        self.stdout.write(self.style.NOTICE("AUDITORIA FINAL DO BANCO DE DADOS"))
        self.stdout.write("=" * 70)
        total_pessoas = Pessoa.objects.count()
        total_eventos = Evento.objects.count()
        total_instituicoes = Instituicao.objects.count()
        total_participacoes = Participacao.objects.count()

        self.stdout.write(f"• Pessoas físicas cadastradas (CPFs únicos): {total_pessoas:,}".replace(",", "."))
        self.stdout.write(f"• Atividades/Eventos únicos consolidados:   {total_eventos:,}".replace(",", "."))
        self.stdout.write(f"• Instituições normalizadas no catálogo:    {total_instituicoes:,}".replace(",", "."))
        self.stdout.write(f"• Participações ativas vinculadas:          {total_participacoes:,}".replace(",", "."))

        # Teste de integridade referencial básica
        part_sem_pessoa = Participacao.objects.filter(pessoa__isnull=True).count()
        part_sem_evento = Participacao.objects.filter(evento__isnull=True).count()
        if part_sem_pessoa == 0 and part_sem_evento == 0:
            self.stdout.write(self.style.SUCCESS("• Integridade referencial: 100% íntegra (0 órfãos)."))
        else:
            self.stdout.write(self.style.ERROR(f"• Inconsistência referencial: {part_sem_pessoa} sem pessoa, {part_sem_evento} sem evento."))

        self.stdout.write("=" * 70)
        self.stdout.write(self.style.SUCCESS("Processo de importação finalizado com sucesso!"))
