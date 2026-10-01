"""
DTO e sanitização dos filtros analíticos do Dashboard do SIPAC.
Responsável por capturar parâmetros GET da requisição HTTP,
validar contra enums do sistema e aplicar filtros aos QuerySets do ORM.
"""

from dataclasses import dataclass
from typing import Any
from urllib.parse import urlencode
from django.db.models import Q, QuerySet
from apps.participantes.models.choices import (
    ComunidadeTradicional,
    Estado,
    FrenteResponsavel,
    Genero,
    MetaInterna,
    TipoParticipante,
)


@dataclass
class DashboardFilter:
    """
    DTO para encapsular os filtros dinâmicos selecionados pelo usuário.
    """

    ano: int | None = None
    estado: str | None = None
    frente: str | None = None
    meta: str | None = None
    tipo_participante: str | None = None
    instituicao: str | None = None
    genero: str | None = None
    comunidade: str | None = None
    busca: str | None = None

    @classmethod
    def from_dict(cls, params: dict[str, Any]) -> "DashboardFilter":
        """
        Constrói o DTO sanitizando e validando os parâmetros fornecidos.
        Descarta valores vazios ou não correspondentes aos choices permitidos.
        """
        # 1. Ano
        ano_val: int | None = None
        raw_ano = str(params.get("ano", "")).strip()
        if raw_ano and raw_ano.isdigit():
            try:
                ano_val = int(raw_ano)
            except (ValueError, TypeError):
                ano_val = None

        # 2. Estado (UF)
        estado_val: str | None = None
        raw_estado = str(params.get("estado", "")).strip().upper()
        if raw_estado in Estado.values:
            estado_val = raw_estado

        # 3. Frente Responsável
        frente_val: str | None = None
        raw_frente = str(params.get("frente", "")).strip().upper()
        if raw_frente in FrenteResponsavel.values:
            frente_val = raw_frente

        # 4. Meta Interna
        meta_val: str | None = None
        raw_meta = str(params.get("meta", "")).strip().upper()
        if raw_meta in MetaInterna.values:
            meta_val = raw_meta

        # 5. Tipo do Participante
        tipo_val: str | None = None
        raw_tipo = str(params.get("tipo_participante", "")).strip().upper()
        if raw_tipo in TipoParticipante.values:
            tipo_val = raw_tipo

        # 6. Gênero
        genero_val: str | None = None
        raw_genero = str(params.get("genero", "")).strip().upper()
        if raw_genero in Genero.values:
            genero_val = raw_genero

        # 7. Comunidade Tradicional
        comunidade_val: str | None = None
        raw_comunidade = str(params.get("comunidade", "")).strip().upper()
        if raw_comunidade in ComunidadeTradicional.values:
            comunidade_val = raw_comunidade

        # 8. Instituição
        instituicao_val: str | None = None
        raw_inst = str(params.get("instituicao", "")).strip()
        if raw_inst:
            instituicao_val = raw_inst

        # 9. Busca textual (nome, CPF, evento)
        busca_val: str | None = None
        raw_busca = str(params.get("busca", "")).strip()
        if raw_busca:
            busca_val = raw_busca

        return cls(
            ano=ano_val,
            estado=estado_val,
            frente=frente_val,
            meta=meta_val,
            tipo_participante=tipo_val,
            instituicao=instituicao_val,
            genero=genero_val,
            comunidade=comunidade_val,
            busca=busca_val,
        )

    @classmethod
    def from_request(cls, request) -> "DashboardFilter":
        """Instancia o DTO a partir dos query params do request Django."""
        return cls.from_dict(request.GET.dict())

    def apply(self, queryset: QuerySet) -> QuerySet:
        """
        Aplica as condições de filtro acumuladas a um QuerySet de Participacao.
        """
        qs = queryset

        if self.ano is not None:
            qs = qs.filter(evento__data__year=self.ano)

        if self.estado is not None:
            qs = qs.filter(evento__estado=self.estado)

        if self.frente is not None:
            qs = qs.filter(evento__frente_responsavel=self.frente)

        if self.meta is not None:
            qs = qs.filter(evento__meta_interna=self.meta)

        if self.tipo_participante is not None:
            qs = qs.filter(tipo_participante=self.tipo_participante)

        if self.genero is not None:
            qs = qs.filter(pessoa__genero=self.genero)

        if self.comunidade is not None:
            qs = qs.filter(pessoa__comunidade_tradicional=self.comunidade)

        if self.instituicao is not None:
            qs = qs.filter(instituicao__nome__iexact=self.instituicao)

        if self.busca is not None:
            # Busca textual resiliente com remoção de pontuação para CPFs
            termo = self.busca
            termo_numerico = "".join(c for c in termo if c.isdigit())
            busca_q = (
                Q(pessoa__nome__icontains=termo)
                | Q(evento__nome__icontains=termo)
                | Q(codigo__icontains=termo)
            )
            if termo_numerico:
                busca_q |= Q(pessoa__cpf__icontains=termo_numerico)
            qs = qs.filter(busca_q)

        return qs

    @property
    def is_active(self) -> bool:
        """Indica se há pelo menos um filtro ativo aplicado."""
        return any(
            [
                self.ano is not None,
                self.estado is not None,
                self.frente is not None,
                self.meta is not None,
                self.tipo_participante is not None,
                self.instituicao is not None,
                self.genero is not None,
                self.comunidade is not None,
                self.busca is not None,
            ]
        )

    def to_dict(self) -> dict[str, Any]:
        """Converte os filtros ativos para dicionário simples."""
        return {
            "ano": self.ano,
            "estado": self.estado,
            "frente": self.frente,
            "meta": self.meta,
            "tipo_participante": self.tipo_participante,
            "instituicao": self.instituicao,
            "genero": self.genero,
            "comunidade": self.comunidade,
            "busca": self.busca,
        }

    def as_query_string(self, exclude: str | None = None) -> str:
        """Gera a query string URL mantendo os parâmetros atuais, exceto o parâmetro indicado."""
        params = {}
        for k, v in self.to_dict().items():
            if v is not None and k != exclude:
                params[k] = v
        return urlencode(params)
