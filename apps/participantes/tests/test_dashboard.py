"""
Testes automatizados para a camada analítica do Dashboard (Fase 5).
Valida a sanitização de filtros (filters.py), agregações otimizadas do ORM (queries.py)
e a consolidação de dados e gráficos (service.py).
"""

from datetime import date
from django.test import TestCase
from apps.participantes.models import (
    ComunidadeTradicional,
    Estado,
    Evento,
    FrenteResponsavel,
    Genero,
    Instituicao,
    MetaInterna,
    Participacao,
    Pessoa,
    TipoParticipante,
)
from apps.participantes.services.dashboard import (
    DashboardFilter,
    DashboardQueries,
    DashboardService,
)


class DashboardFilterTestCase(TestCase):
    """Testes para o DTO de filtros DashboardFilter."""

    def test_filter_sanitization_valid(self):
        data = {
            "ano": "2026",
            "estado": "am",  # Deve normalizar para uppercase AM
            "frente": "campo",  # Deve normalizar para uppercase CAMPO
            "meta": "dcs",  # Deve normalizar para DCS
            "tipo_participante": "produtor_rural",
            "genero": "m",
            "comunidade": "ribeirinho",
            "instituicao": " Embrapa ",
            "busca": " Lucas Silva ",
        }
        f = DashboardFilter.from_dict(data)

        self.assertEqual(f.ano, 2026)
        self.assertEqual(f.estado, Estado.AM.value)
        self.assertEqual(f.frente, FrenteResponsavel.CAMPO.value)
        self.assertEqual(f.meta, MetaInterna.DCS.value)
        self.assertEqual(f.tipo_participante, TipoParticipante.PRODUTOR_RURAL.value)
        self.assertEqual(f.genero, Genero.MASCULINO.value)
        self.assertEqual(f.comunidade, ComunidadeTradicional.RIBEIRINHO.value)
        self.assertEqual(f.instituicao, "Embrapa")
        self.assertEqual(f.busca, "Lucas Silva")
        self.assertTrue(f.is_active)

    def test_filter_sanitization_invalid_discarded(self):
        data = {
            "ano": "ano_invalido",
            "estado": "UF_FALSA",
            "frente": "FRENTE_FALSA",
            "meta": "META_FALSA",
            "tipo_participante": "TIPO_FALSO",
            "genero": "X",
            "comunidade": "COMUNIDADE_FALSA",
            "instituicao": "   ",
            "busca": "   ",
        }
        f = DashboardFilter.from_dict(data)

        self.assertIsNone(f.ano)
        self.assertIsNone(f.estado)
        self.assertIsNone(f.frente)
        self.assertIsNone(f.meta)
        self.assertIsNone(f.tipo_participante)
        self.assertIsNone(f.genero)
        self.assertIsNone(f.comunidade)
        self.assertIsNone(f.instituicao)
        self.assertIsNone(f.busca)
        self.assertFalse(f.is_active)

    def test_filter_as_query_string(self):
        f = DashboardFilter(ano=2026, estado="AM", frente="CAMPO")
        qs = f.as_query_string()
        self.assertIn("ano=2026", qs)
        self.assertIn("estado=AM", qs)
        self.assertIn("frente=CAMPO", qs)

        # Excluir parâmetro específico
        qs_no_ano = f.as_query_string(exclude="ano")
        self.assertNotIn("ano=2026", qs_no_ano)
        self.assertIn("estado=AM", qs_no_ano)


class DashboardQueriesAndServiceTestCase(TestCase):
    """Testes integrados de agregações analíticas e consolidação de indicadores."""

    def setUp(self):
        # 1. Pessoas
        self.p1 = Pessoa.objects.create(
            cpf="00208935150",
            nome="Lucas Silva",
            data_nascimento=date(1990, 5, 20),
            genero=Genero.MASCULINO,
            comunidade_tradicional=ComunidadeTradicional.RIBEIRINHO,
        )
        self.p2 = Pessoa.objects.create(
            cpf="81060360225",
            nome="Mariana Costa",
            data_nascimento=date(1985, 3, 15),
            genero=Genero.FEMININO,
            comunidade_tradicional=ComunidadeTradicional.QUILOMBOLA,
        )
        self.p3 = Pessoa.objects.create(
            cpf="94908990204",
            nome="Alex Santos",
            data_nascimento=None,
            genero=Genero.NAO_INFORMADO,
            comunidade_tradicional=ComunidadeTradicional.NAO,
        )

        # 2. Instituições
        self.inst1 = Instituicao.objects.create(nome="EMBRAPA")
        self.inst2 = Instituicao.objects.create(nome="IABS")

        # 3. Eventos
        self.e1 = Evento.objects.create(
            nome="Dia de Campo Florestal",
            data=date(2026, 6, 15),
            frente_responsavel=FrenteResponsavel.CAMPO,
            meta_interna=MetaInterna.DCS,
            estado=Estado.AM,
        )
        self.e2 = Evento.objects.create(
            nome="Curso ATER Básico",
            data=date(2026, 7, 20),
            frente_responsavel=FrenteResponsavel.ATER,
            meta_interna=MetaInterna.ENCONTROS_TEMATICOS,
            estado=Estado.PA,
        )

        # 4. Participações
        # P1 participa de 2 eventos
        Participacao.objects.create(
            codigo="PART-001",
            pessoa=self.p1,
            evento=self.e1,
            tipo_participante=TipoParticipante.PRODUTOR_RURAL,
            instituicao=self.inst1,
        )
        Participacao.objects.create(
            codigo="PART-002",
            pessoa=self.p1,
            evento=self.e2,
            tipo_participante=TipoParticipante.PRODUTOR_RURAL,
            instituicao=self.inst1,
        )
        # P2 participa de 1 evento
        Participacao.objects.create(
            codigo="PART-003",
            pessoa=self.p2,
            evento=self.e1,
            tipo_participante=TipoParticipante.TECNICO_ATER,
            instituicao=self.inst2,
        )
        # P3 participa de 1 evento sem instituicao
        Participacao.objects.create(
            codigo="PART-004",
            pessoa=self.p3,
            evento=self.e2,
            tipo_participante=TipoParticipante.OUTROS,
            instituicao=None,
        )

        self.service = DashboardService()
        self.queries = DashboardQueries()

    def test_kpis_calculation(self):
        """Valida totalizadores macro e média de participações por pessoa."""
        data = self.service.get_dashboard_data()
        kpis = data["kpis"]

        self.assertEqual(kpis["total_participacoes"], 4)
        self.assertEqual(kpis["total_pessoas_unicas"], 3)
        self.assertEqual(kpis["total_eventos"], 2)
        self.assertEqual(kpis["total_instituicoes"], 2)
        # 4 participações divididas por 3 pessoas = 1.33
        self.assertEqual(kpis["media_participacoes_por_pessoa"], 1.33)

    def test_distribuicao_genero(self):
        """Valida contagem e percentual por gênero."""
        data = self.service.get_dashboard_data()
        genero_chart = data["charts_data"]["genero"]

        # P1 (Masculino) tem 2 participações; P2 (Feminino) tem 1; P3 (Não Informado) tem 1.
        self.assertIn("Masculino", genero_chart["labels"])
        idx_masc = genero_chart["labels"].index("Masculino")
        self.assertEqual(genero_chart["data"][idx_masc], 2)
        self.assertEqual(genero_chart["percentages"][idx_masc], 50.0)

    def test_distribuicao_comunidade(self):
        """Valida contagem por comunidade tradicional."""
        data = self.service.get_dashboard_data()
        comunidade_chart = data["charts_data"]["comunidade"]

        self.assertIn("Ribeirinho", comunidade_chart["labels"])
        idx_rib = comunidade_chart["labels"].index("Ribeirinho")
        self.assertEqual(comunidade_chart["data"][idx_rib], 2)

    def test_distribuicao_estado_and_ranking(self):
        """Valida agregação por Estado (UF) e ordenação do ranking."""
        data = self.service.get_dashboard_data()
        ranking = data["ranking_estados"]

        self.assertEqual(len(ranking), 2)
        ufs = [r["uf"] for r in ranking]
        self.assertIn("AM", ufs)
        self.assertIn("PA", ufs)
        # Cada estado teve 2 participações
        self.assertEqual(ranking[0]["total"], 2)
        self.assertEqual(ranking[1]["total"], 2)

    def test_distribuicao_frente_and_meta(self):
        """Valida agregações por Frente e Meta."""
        data = self.service.get_dashboard_data()
        frente_chart = data["charts_data"]["frente"]
        meta_chart = data["charts_data"]["meta"]

        self.assertIn("CAMPO", frente_chart["labels"])
        self.assertIn("ATER", frente_chart["labels"])

    def test_evolucao_temporal(self):
        """Valida agregação cronológica mês a mês."""
        data = self.service.get_dashboard_data()
        evolucao = data["charts_data"]["evolucao"]

        # Junho e Julho de 2026
        self.assertIn("06/2026", evolucao["labels"])
        self.assertIn("07/2026", evolucao["labels"])
        idx_jun = evolucao["labels"].index("06/2026")
        self.assertEqual(evolucao["data"][idx_jun], 2)

    def test_filtering_by_estado(self):
        """Filtro por estado deve restringir KPIs e gráficos apenas para aquele estado."""
        filtro_am = DashboardFilter(estado="AM")
        data = self.service.get_dashboard_data(filtro_am)
        kpis = data["kpis"]

        self.assertTrue(data["is_filtered"])
        self.assertEqual(kpis["total_participacoes"], 2)
        self.assertEqual(kpis["total_pessoas_unicas"], 2)  # P1 e P2 no evento AM
        self.assertEqual(kpis["total_eventos"], 1)  # Apenas evento E1

    def test_filtering_by_busca_textual(self):
        """Busca textual por nome deve filtrar participações de Lucas Silva."""
        filtro_busca = DashboardFilter(busca="Lucas")
        data = self.service.get_dashboard_data(filtro_busca)
        kpis = data["kpis"]

        self.assertEqual(kpis["total_participacoes"], 2)
        self.assertEqual(kpis["total_pessoas_unicas"], 1)

    def test_filtering_by_ano(self):
        """Filtro por ano deve retornar apenas dados daquele ano."""
        filtro_2026 = DashboardFilter(ano=2026)
        data = self.service.get_dashboard_data(filtro_2026)
        self.assertEqual(data["kpis"]["total_participacoes"], 4)

        filtro_2025 = DashboardFilter(ano=2025)
        data_vazio = self.service.get_dashboard_data(filtro_2025)
        self.assertEqual(data_vazio["kpis"]["total_participacoes"], 0)
        self.assertEqual(data_vazio["kpis"]["total_pessoas_unicas"], 0)
        self.assertEqual(data_vazio["kpis"]["media_participacoes_por_pessoa"], 0.0)
