"""
Controlador Web do Dashboard de Segmentação de Participantes.
CBV TemplateView responsável por receber as configurações de segmentos,
invocar o SegmentacaoService e renderizar os resultados analíticos.
"""

import json
from typing import Any
from django.contrib import messages
from django.shortcuts import redirect
from django.views.generic import TemplateView
from apps.participantes.services.dashboard.queries import DashboardQueries
from apps.participantes.services.segmentacao import (
    SegmentacaoService,
)


class SegmentacaoDashboardView(TemplateView):
    """
    CBV fina para a interface de Segmentação de Participantes.
    Isola a orquestração HTTP sem conter regras de agregação analítica no controller.
    """

    template_name = "participantes/segmentacao/index.html"

    def get_service(self) -> SegmentacaoService:
        return SegmentacaoService()

    def get(self, request, *args, **kwargs):
        service = self.get_service()
        
        # Recupera configuração da sessão ou carrega segmentos padrão
        segments_config = request.session.get("segmentacao_config")
        if not segments_config:
            default_segments = service.get_default_segments()
            segments_config = [seg.to_dict() for seg in default_segments]

        analysis = service.run_segmentation(segments_config)
        filter_options = DashboardQueries.get_filter_options()

        context = self.get_context_data(
            analysis=analysis,
            segments_config=segments_config,
            filter_options=filter_options,
            analysis_json=analysis.to_dict(),
        )
        return self.render_to_response(context)

    def post(self, request, *args, **kwargs):
        service = self.get_service()
        action = request.POST.get("action")

        # 1. Ação de Resetar para a configuração padrão
        if action == "reset":
            if "segmentacao_config" in request.session:
                del request.session["segmentacao_config"]
            messages.success(request, "Configuração de segmentos redefinida para o padrão.")
            return redirect("participantes:segmentacao")

        # 2. Leitura do payload JSON dos segmentos
        raw_payload = request.POST.get("segments_payload", "").strip()
        segments_config: list[dict[str, Any]] = []

        if raw_payload:
            try:
                segments_config = json.loads(raw_payload)
            except (json.JSONDecodeError, TypeError, ValueError) as err:
                messages.warning(
                    request,
                    f"Formato inválido de configuração recebido. Utilizando padrão. ({err})",
                )
                segments_config = []

        if not segments_config:
            default_segments = service.get_default_segments()
            segments_config = [seg.to_dict() for seg in default_segments]

        # Salva na sessão para persistir estado entre requisições do usuário
        request.session["segmentacao_config"] = segments_config

        # Executa a segmentação sob as novas prioridades e filtros
        analysis = service.run_segmentation(segments_config)
        filter_options = DashboardQueries.get_filter_options()

        context = self.get_context_data(
            analysis=analysis,
            segments_config=segments_config,
            filter_options=filter_options,
            analysis_json=analysis.to_dict(),
        )
        messages.success(request, f"Análise concluída com sucesso para {len(segments_config)} segmento(s).")
        return self.render_to_response(context)
