"""
Customização do Django Admin para as entidades do SIPAC.
Configurado com busca, filtros analíticos, paginação e otimização de queries.
"""

from django.contrib import admin
from django.db.models import Count
from .models import Evento, Instituicao, Participacao, Pessoa


@admin.register(Pessoa)
class PessoaAdmin(admin.ModelAdmin):
    """Admin para cadastro único de Pessoas (Participantes)."""

    list_display = (
        "cpf",
        "nome",
        "data_nascimento",
        "genero",
        "comunidade_tradicional",
        "total_participacoes",
        "created_at",
    )
    search_fields = (
        "cpf",
        "nome",
    )
    list_filter = (
        "genero",
        "comunidade_tradicional",
    )
    ordering = ("nome",)
    list_per_page = 25
    readonly_fields = (
        "created_at",
        "updated_at",
    )

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        return qs.annotate(participacoes_count=Count("participacoes"))

    @admin.display(description="Total Participações", ordering="participacoes_count")
    def total_participacoes(self, obj):
        return obj.participacoes_count


@admin.register(Instituicao)
class InstituicaoAdmin(admin.ModelAdmin):
    """Admin para catálogo sanitizado de Instituições."""

    list_display = (
        "nome",
        "total_participacoes",
        "created_at",
    )
    search_fields = ("nome",)
    ordering = ("nome",)
    list_per_page = 25
    readonly_fields = (
        "created_at",
        "updated_at",
    )

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        return qs.annotate(participacoes_count=Count("participacoes"))

    @admin.display(description="Participações Vinculadas", ordering="participacoes_count")
    def total_participacoes(self, obj):
        return obj.participacoes_count


@admin.register(Evento)
class EventoAdmin(admin.ModelAdmin):
    """Admin para Atividades e Eventos de ATER."""

    list_display = (
        "nome",
        "data",
        "estado",
        "frente_responsavel",
        "meta_interna",
        "total_participantes",
        "created_at",
    )
    search_fields = ("nome",)
    list_filter = (
        "estado",
        "frente_responsavel",
        "meta_interna",
        "data",
    )
    date_hierarchy = "data"
    ordering = ("-data", "nome")
    list_per_page = 25
    readonly_fields = (
        "created_at",
        "updated_at",
    )

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        return qs.annotate(participantes_count=Count("participacoes"))

    @admin.display(description="Participantes", ordering="participantes_count")
    def total_participantes(self, obj):
        return obj.participantes_count


@admin.register(Participacao)
class ParticipacaoAdmin(admin.ModelAdmin):
    """Admin para o Fato Participação (Relação Pessoa <-> Evento)."""

    list_display = (
        "codigo",
        "pessoa",
        "evento_nome",
        "evento_data",
        "evento_estado",
        "tipo_participante",
        "instituicao",
    )
    search_fields = (
        "codigo",
        "pessoa__cpf",
        "pessoa__nome",
        "evento__nome",
    )
    list_filter = (
        "tipo_participante",
        "evento__estado",
        "evento__frente_responsavel",
        "evento__meta_interna",
    )
    autocomplete_fields = (
        "pessoa",
        "evento",
        "instituicao",
    )
    list_per_page = 25
    readonly_fields = (
        "created_at",
        "updated_at",
    )

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        return qs.select_related("pessoa", "evento", "instituicao")

    @admin.display(description="Evento", ordering="evento__nome")
    def evento_nome(self, obj):
        return obj.evento.nome

    @admin.display(description="Data", ordering="evento__data")
    def evento_data(self, obj):
        return obj.evento.data.strftime("%d/%m/%Y") if obj.evento and obj.evento.data else "-"

    @admin.display(description="UF", ordering="evento__estado")
    def evento_estado(self, obj):
        return obj.evento.estado if obj.evento else "-"
