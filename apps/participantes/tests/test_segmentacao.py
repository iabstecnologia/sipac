"""
Testes automatizados da regra de Segmentação de Participantes do SIPAC.
Valida o particionamento sequencial estrito por CPF (pessoa_id),
a inversão de prioridades, múltiplas participações, consistência de indicadores e Views.
"""

from datetime import date
from django.test import TestCase
from django.urls import reverse
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
from apps.participantes.services.dashboard.filters import DashboardFilter
from apps.participantes.services.segmentacao import (
    SegmentDefinition,
    SegmentacaoService,
)


class SegmentacaoServiceTests(TestCase):
    """
    Testes do Service de Segmentação cobrindo todas as regras matemáticas e de negócio.
    """

    def setUp(self):
        # 1. Criação de Eventos de teste
        self.evento_dcs = Evento.objects.create(
            nome="Dia de Campo Modelo",
            data=date(2025, 4, 15),
            frente_responsavel=FrenteResponsavel.ATER,
            estado=Estado.AM,
            meta_interna=MetaInterna.DCS,
        )
        self.evento_cursos = Evento.objects.create(
            nome="Curso Presencial Agroecologia",
            data=date(2025, 5, 20),
            frente_responsavel=FrenteResponsavel.ATER,
            estado=Estado.PA,
            meta_interna=MetaInterna.FORMACAO_ATECS,
        )
        self.evento_encontros = Evento.objects.create(
            nome="Encontro de Lideranças",
            data=date(2025, 6, 10),
            frente_responsavel=FrenteResponsavel.ATER,
            estado=Estado.RO,
            meta_interna=MetaInterna.ENCONTROS_TEMATICOS,
        )

        # 2. Criação de Pessoas com CPFs rastreáveis
        self.p1 = Pessoa.objects.create(
            cpf="11111111111",
            nome="Participante 01",
            genero=Genero.FEMININO,
            comunidade_tradicional=ComunidadeTradicional.RIBEIRINHO,
        )
        self.p2 = Pessoa.objects.create(
            cpf="22222222222",
            nome="Participante 02",
            genero=Genero.MASCULINO,
            comunidade_tradicional=ComunidadeTradicional.NAO,
        )
        self.p3 = Pessoa.objects.create(
            cpf="33333333333",
            nome="Participante 03",
            genero=Genero.FEMININO,
            comunidade_tradicional=ComunidadeTradicional.NAO,
        )
        self.p4 = Pessoa.objects.create(
            cpf="44444444444",
            nome="Participante 04",
            genero=Genero.MASCULINO,
            comunidade_tradicional=ComunidadeTradicional.RIBEIRINHO,
        )
        self.p5 = Pessoa.objects.create(
            cpf="55555555555",
            nome="Participante 05",
            genero=Genero.FEMININO,
            comunidade_tradicional=ComunidadeTradicional.NAO,
        )

        self.service = SegmentacaoService()

    def test_caso_1_sem_conflito(self):
        """
        Caso 1 — nenhum conflito:
        Segmento 1: CPF01, CPF02
        Segmento 2: CPF03, CPF04
        Resultado:
        Segmento 1 = CPF01, CPF02
        Segmento 2 = CPF03, CPF04
        """
        # P1 e P2 no Evento DCS
        Participacao.objects.create(codigo="PART-01", pessoa=self.p1, evento=self.evento_dcs, tipo_participante=TipoParticipante.PRODUTOR_RURAL)
        Participacao.objects.create(codigo="PART-02", pessoa=self.p2, evento=self.evento_dcs, tipo_participante=TipoParticipante.PRODUTOR_RURAL)

        # P3 e P4 no Evento Cursos
        Participacao.objects.create(codigo="PART-03", pessoa=self.p3, evento=self.evento_cursos, tipo_participante=TipoParticipante.PRODUTOR_RURAL)
        Participacao.objects.create(codigo="PART-04", pessoa=self.p4, evento=self.evento_cursos, tipo_participante=TipoParticipante.PRODUTOR_RURAL)

        seg1 = SegmentDefinition(id="s1", name="Segmento 1", order=1, filters=DashboardFilter(meta=MetaInterna.DCS))
        seg2 = SegmentDefinition(id="s2", name="Segmento 2", order=2, filters=DashboardFilter(meta=MetaInterna.FORMACAO_ATECS))

        result = self.service.run_segmentation([seg1, seg2])

        r1 = result.segments[0]
        r2 = result.segments[1]

        self.assertEqual(r1.kpis.raw_participants, 2)
        self.assertEqual(r1.kpis.excluded_participants, 0)
        self.assertEqual(r1.kpis.participants, 2)
        self.assertEqual(r1.kpis.participations, 2)

        self.assertEqual(r2.kpis.raw_participants, 2)
        self.assertEqual(r2.kpis.excluded_participants, 0)
        self.assertEqual(r2.kpis.participants, 2)
        self.assertEqual(r2.kpis.participations, 2)

        self.assertEqual(result.total_unique_participants_allocated, 4)

    def test_caso_2_com_conflito(self):
        """
        Caso 2 — conflito:
        Segmento 1: CPF01, CPF02, CPF03
        Segmento 2: CPF02, CPF03, CPF04
        Resultado:
        Segmento 1 = CPF01, CPF02, CPF03
        Segmento 2 = CPF04
        """
        # Segmento 1 (DCS): P1, P2, P3
        Participacao.objects.create(codigo="PART-01", pessoa=self.p1, evento=self.evento_dcs, tipo_participante=TipoParticipante.PRODUTOR_RURAL)
        Participacao.objects.create(codigo="PART-02", pessoa=self.p2, evento=self.evento_dcs, tipo_participante=TipoParticipante.PRODUTOR_RURAL)
        Participacao.objects.create(codigo="PART-03", pessoa=self.p3, evento=self.evento_dcs, tipo_participante=TipoParticipante.PRODUTOR_RURAL)

        # Segmento 2 (Cursos): P2, P3, P4
        Participacao.objects.create(codigo="PART-04", pessoa=self.p2, evento=self.evento_cursos, tipo_participante=TipoParticipante.PRODUTOR_RURAL)
        Participacao.objects.create(codigo="PART-05", pessoa=self.p3, evento=self.evento_cursos, tipo_participante=TipoParticipante.PRODUTOR_RURAL)
        Participacao.objects.create(codigo="PART-06", pessoa=self.p4, evento=self.evento_cursos, tipo_participante=TipoParticipante.PRODUTOR_RURAL)

        seg1 = SegmentDefinition(id="s1", name="Segmento 1", order=1, filters=DashboardFilter(meta=MetaInterna.DCS))
        seg2 = SegmentDefinition(id="s2", name="Segmento 2", order=2, filters=DashboardFilter(meta=MetaInterna.FORMACAO_ATECS))

        result = self.service.run_segmentation([seg1, seg2])

        r1 = result.segments[0]
        r2 = result.segments[1]

        # Segmento 1 mantém P1, P2, P3
        self.assertEqual(r1.kpis.raw_participants, 3)
        self.assertEqual(r1.kpis.excluded_participants, 0)
        self.assertEqual(r1.kpis.participants, 3)
        self.assertEqual(r1.kpis.participations, 3)

        # Segmento 2 tinha P2, P3, P4 bruto (3), mas P2 e P3 já foram para o S1. Efetivo = apenas P4 (1)
        self.assertEqual(r2.kpis.raw_participants, 3)
        self.assertEqual(r2.kpis.excluded_participants, 2)
        self.assertEqual(r2.kpis.participants, 1)
        self.assertEqual(r2.kpis.participations, 1)

        self.assertEqual(result.total_unique_participants_allocated, 4)

    def test_caso_3_tres_segmentos(self):
        """
        Caso 3 — três segmentos:
        Segmento 1: CPF01, CPF02
        Segmento 2: CPF02, CPF03, CPF04
        Segmento 3: CPF01, CPF04, CPF05
        Resultado:
        Segmento 1 = CPF01, CPF02
        Segmento 2 = CPF03, CPF04
        Segmento 3 = CPF05
        """
        # S1 (DCS): P1, P2
        Participacao.objects.create(codigo="C3-01", pessoa=self.p1, evento=self.evento_dcs, tipo_participante=TipoParticipante.PRODUTOR_RURAL)
        Participacao.objects.create(codigo="C3-02", pessoa=self.p2, evento=self.evento_dcs, tipo_participante=TipoParticipante.PRODUTOR_RURAL)

        # S2 (Cursos): P2, P3, P4
        Participacao.objects.create(codigo="C3-03", pessoa=self.p2, evento=self.evento_cursos, tipo_participante=TipoParticipante.PRODUTOR_RURAL)
        Participacao.objects.create(codigo="C3-04", pessoa=self.p3, evento=self.evento_cursos, tipo_participante=TipoParticipante.PRODUTOR_RURAL)
        Participacao.objects.create(codigo="C3-05", pessoa=self.p4, evento=self.evento_cursos, tipo_participante=TipoParticipante.PRODUTOR_RURAL)

        # S3 (Encontros): P1, P4, P5
        Participacao.objects.create(codigo="C3-06", pessoa=self.p1, evento=self.evento_encontros, tipo_participante=TipoParticipante.PRODUTOR_RURAL)
        Participacao.objects.create(codigo="C3-07", pessoa=self.p4, evento=self.evento_encontros, tipo_participante=TipoParticipante.PRODUTOR_RURAL)
        Participacao.objects.create(codigo="C3-08", pessoa=self.p5, evento=self.evento_encontros, tipo_participante=TipoParticipante.PRODUTOR_RURAL)

        seg1 = SegmentDefinition(id="s1", name="Segmento 1", order=1, filters=DashboardFilter(meta=MetaInterna.DCS))
        seg2 = SegmentDefinition(id="s2", name="Segmento 2", order=2, filters=DashboardFilter(meta=MetaInterna.FORMACAO_ATECS))
        seg3 = SegmentDefinition(id="s3", name="Segmento 3", order=3, filters=DashboardFilter(meta=MetaInterna.ENCONTROS_TEMATICOS))

        result = self.service.run_segmentation([seg1, seg2, seg3])

        r1 = result.segments[0]
        r2 = result.segments[1]
        r3 = result.segments[2]

        # S1: P1, P2 -> 2 participantes
        self.assertEqual(r1.kpis.participants, 2)
        self.assertEqual(r1.kpis.excluded_participants, 0)

        # S2: Bruto P2, P3, P4 (3). P2 já foi alocado em S1. Efetivo P3, P4 -> 2 participantes
        self.assertEqual(r2.kpis.raw_participants, 3)
        self.assertEqual(r2.kpis.excluded_participants, 1)
        self.assertEqual(r2.kpis.participants, 2)

        # S3: Bruto P1, P4, P5 (3). P1 em S1 e P4 em S2. Efetivo apenas P5 -> 1 participante
        self.assertEqual(r3.kpis.raw_participants, 3)
        self.assertEqual(r3.kpis.excluded_participants, 2)
        self.assertEqual(r3.kpis.participants, 1)

        self.assertEqual(result.total_unique_participants_allocated, 5)

    def test_caso_4_inversao_prioridade(self):
        """
        Caso 4 — alteração de prioridade (OBRIGATÓRIO):
        Segmento A: CPF01
        Segmento B: CPF01, CPF02
        Ordem A -> B:
        A = CPF01
        B = CPF02
        Depois inverter B -> A:
        B = CPF01, CPF02
        A = vazio
        """
        # Evento DCS = Seg A: P1
        Participacao.objects.create(codigo="CP-01", pessoa=self.p1, evento=self.evento_dcs, tipo_participante=TipoParticipante.PRODUTOR_RURAL)

        # Evento Cursos = Seg B: P1 e P2
        Participacao.objects.create(codigo="CP-02", pessoa=self.p1, evento=self.evento_cursos, tipo_participante=TipoParticipante.PRODUTOR_RURAL)
        Participacao.objects.create(codigo="CP-03", pessoa=self.p2, evento=self.evento_cursos, tipo_participante=TipoParticipante.PRODUTOR_RURAL)

        # 1. Ordem A (order=1) -> B (order=2)
        seg_a = SegmentDefinition(id="sa", name="Segmento A", order=1, filters=DashboardFilter(meta=MetaInterna.DCS))
        seg_b = SegmentDefinition(id="sb", name="Segmento B", order=2, filters=DashboardFilter(meta=MetaInterna.FORMACAO_ATECS))

        res_ab = self.service.run_segmentation([seg_a, seg_b])
        ra = res_ab.segments[0]
        rb = res_ab.segments[1]

        self.assertEqual(ra.kpis.participants, 1)  # P1
        self.assertEqual(ra.kpis.excluded_participants, 0)
        self.assertEqual(rb.kpis.participants, 1)  # apenas P2
        self.assertEqual(rb.kpis.excluded_participants, 1)  # P1 excluído

        # 2. Inverter Ordem: B (order=1) -> A (order=2)
        seg_b_first = SegmentDefinition(id="sb", name="Segmento B", order=1, filters=DashboardFilter(meta=MetaInterna.FORMACAO_ATECS))
        seg_a_second = SegmentDefinition(id="sa", name="Segmento A", order=2, filters=DashboardFilter(meta=MetaInterna.DCS))

        res_ba = self.service.run_segmentation([seg_b_first, seg_a_second])
        rb2 = res_ba.segments[0]
        ra2 = res_ba.segments[1]

        # B agora recebe P1 e P2 (2)
        self.assertEqual(rb2.kpis.participants, 2)
        self.assertEqual(rb2.kpis.excluded_participants, 0)

        # A tinha P1 bruto (1), mas P1 foi para o B. Portanto A fica vazio!
        self.assertEqual(ra2.kpis.raw_participants, 1)
        self.assertEqual(ra2.kpis.excluded_participants, 1)
        self.assertEqual(ra2.kpis.participants, 0)
        self.assertTrue(ra2.is_empty)

    def test_caso_5_multiplas_participacoes(self):
        """
        Caso 5 — testar múltiplas participações (OBRIGATÓRIO):
        Uma mesma Pessoa possui várias participações.
        Confirmar que:
        - a pessoa é alocada apenas uma vez;
        - suas participações são contabilizadas corretamente no segmento em que ela foi alocada;
        - ela não aparece em nenhum segmento posterior.
        """
        # Criar outro evento DCS
        evento_dcs_2 = Evento.objects.create(
            nome="Dia de Campo 2",
            data=date(2025, 4, 25),
            frente_responsavel=FrenteResponsavel.ATER,
            estado=Estado.AM,
            meta_interna=MetaInterna.DCS,
        )

        # P1 tem 3 participações no DCS: duas no evento 1, uma no evento 2
        Participacao.objects.create(codigo="MP-01", pessoa=self.p1, evento=self.evento_dcs, tipo_participante=TipoParticipante.PRODUTOR_RURAL)
        Participacao.objects.create(codigo="MP-02", pessoa=self.p1, evento=self.evento_dcs, tipo_participante=TipoParticipante.PRODUTOR_RURAL)
        Participacao.objects.create(codigo="MP-03", pessoa=self.p1, evento=evento_dcs_2, tipo_participante=TipoParticipante.PRODUTOR_RURAL)

        # P1 também tem 2 participações em Cursos (Seg 2)
        Participacao.objects.create(codigo="MP-04", pessoa=self.p1, evento=self.evento_cursos, tipo_participante=TipoParticipante.PRODUTOR_RURAL)
        Participacao.objects.create(codigo="MP-05", pessoa=self.p1, evento=self.evento_cursos, tipo_participante=TipoParticipante.PRODUTOR_RURAL)

        # P2 tem 1 participação em Cursos (Seg 2)
        Participacao.objects.create(codigo="MP-06", pessoa=self.p2, evento=self.evento_cursos, tipo_participante=TipoParticipante.PRODUTOR_RURAL)

        seg1 = SegmentDefinition(id="s1", name="Segmento 1", order=1, filters=DashboardFilter(meta=MetaInterna.DCS))
        seg2 = SegmentDefinition(id="s2", name="Segmento 2", order=2, filters=DashboardFilter(meta=MetaInterna.FORMACAO_ATECS))

        result = self.service.run_segmentation([seg1, seg2])

        r1 = result.segments[0]
        r2 = result.segments[1]

        # S1: P1 alocado apenas 1 vez, com 3 participações contabilizadas
        self.assertEqual(r1.kpis.participants, 1)
        self.assertEqual(r1.kpis.participations, 3)

        # S2: P1 foi alocado no S1, então não entra no S2!
        # Apenas P2 entra no S2, com 1 participação
        self.assertEqual(r2.kpis.raw_participants, 2)  # P1 e P2 atendiam
        self.assertEqual(r2.kpis.excluded_participants, 1)  # P1 excluído
        self.assertEqual(r2.kpis.participants, 1)  # apenas P2
        self.assertEqual(r2.kpis.participations, 1)  # apenas a participação de P2

    def test_caso_6_indicadores_recalculados_com_precisao(self):
        """
        Caso 6 — verificar que os gráficos e distribuições refletem rigorosamente
        o conjunto efetivo de pessoas e não dados brutos.
        """
        # P1 (Mulher, Comunidade Sim) no DCS
        Participacao.objects.create(codigo="IND-01", pessoa=self.p1, evento=self.evento_dcs, tipo_participante=TipoParticipante.PRODUTOR_RURAL)
        # P2 (Homem, Comunidade Não) no DCS
        Participacao.objects.create(codigo="IND-02", pessoa=self.p2, evento=self.evento_dcs, tipo_participante=TipoParticipante.PRODUTOR_RURAL)

        # P2 (Homem, Comunidade Não) e P3 (Mulher, Comunidade Não) em Cursos
        Participacao.objects.create(codigo="IND-03", pessoa=self.p2, evento=self.evento_cursos, tipo_participante=TipoParticipante.PRODUTOR_RURAL)
        Participacao.objects.create(codigo="IND-04", pessoa=self.p3, evento=self.evento_cursos, tipo_participante=TipoParticipante.PRODUTOR_RURAL)

        seg1 = SegmentDefinition(id="s1", name="Segmento 1", order=1, filters=DashboardFilter(meta=MetaInterna.DCS))
        seg2 = SegmentDefinition(id="s2", name="Segmento 2", order=2, filters=DashboardFilter(meta=MetaInterna.FORMACAO_ATECS))

        result = self.service.run_segmentation([seg1, seg2])
        r2 = result.segments[1]

        # Em S2, apenas P3 permanece (P2 já foi alocado em S1)
        self.assertEqual(r2.kpis.participants, 1)
        # Gráfico de Gênero de S2 deve conter apenas Feminino = 1
        genero_chart = r2.charts_data["genero"]
        self.assertEqual(sum(genero_chart["data"]), 1)
        self.assertIn("Feminino", genero_chart["labels"])
        idx_fem = genero_chart["labels"].index("Feminino")
        self.assertEqual(genero_chart["data"][idx_fem], 1)


class SegmentacaoViewTests(TestCase):
    """
    Testes de integração da CBV SegmentacaoDashboardView.
    """

    def setUp(self):
        self.url = reverse("participantes:segmentacao")

    def test_get_retorna_200_com_segmentos_padrao(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "participantes/segmentacao/index.html")
        self.assertIn("analysis", response.context)
        self.assertIn("segments_config", response.context)
        self.assertIn("filter_options", response.context)
        self.assertEqual(len(response.context["segments_config"]), 3)

    def test_post_com_reordenacao_e_analise(self):
        payload = [
            {
                "id": "custom_1",
                "name": "Meu Segmento 1",
                "order": 1,
                "filters": {"meta": "DCS"},
            },
            {
                "id": "custom_2",
                "name": "Meu Segmento 2",
                "order": 2,
                "filters": {"meta": "FORMACAO_ATECS"},
            },
        ]
        import json
        response = self.client.post(self.url, {"segments_payload": json.dumps(payload)})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.context["analysis"].segments), 2)
        self.assertEqual(response.context["analysis"].segments[0].definition.name, "Meu Segmento 1")

    def test_post_reset_restaura_padrao(self):
        response = self.client.post(self.url, {"action": "reset"})
        self.assertRedirects(response, self.url)
