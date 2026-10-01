from django.urls import path
from .views.dashboard import DashboardView

from .views.segmentacao import SegmentacaoDashboardView
from .views.importacao import (
    ImportacaoCancelarView,
    ImportacaoConfirmarView,
    ImportacaoPreviewView,
    ImportacaoResultadoView,
    ImportacaoUploadView,
)

app_name = "participantes"

urlpatterns = [
    path("", DashboardView.as_view(), name="home"),
    path("dashboard/", DashboardView.as_view(), name="dashboard"),
    path("segmentacao/", SegmentacaoDashboardView.as_view(), name="segmentacao"),
    path("importacao/", ImportacaoUploadView.as_view(), name="importacao_upload"),

    path("importacao/preview/", ImportacaoPreviewView.as_view(), name="importacao_preview"),
    path("importacao/confirmar/", ImportacaoConfirmarView.as_view(), name="importacao_confirmar"),
    path("importacao/resultado/", ImportacaoResultadoView.as_view(), name="importacao_resultado"),
    path("importacao/cancelar/", ImportacaoCancelarView.as_view(), name="importacao_cancelar"),
]
