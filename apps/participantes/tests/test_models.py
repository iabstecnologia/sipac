"""
Testes unitários e de integração para os models do SIPAC.
Valida criação, __str__, constraints de unicidade e integridade referencial (PROTECT / SET_NULL).
"""

from datetime import date
from django.db import IntegrityError
from django.db.models import ProtectedError
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


class ModelStrAndCreationTestCase(TestCase):
    """Testes de criação básica e representação textual (__str__)."""

    def setUp(self):
        self.pessoa = Pessoa.objects.create(
            cpf="12345678901",
            nome="João da Silva",
            data_nascimento=date(1985, 5, 20),
            genero=Genero.MASCULINO,
            comunidade_tradicional=ComunidadeTradicional.RIBEIRINHO,
        )
        self.instituicao = Instituicao.objects.create(nome="EMBRAPA")
        self.evento = Evento.objects.create(
            nome="Dia de Campo Sustentável",
            data=date(2026, 6, 15),
            frente_responsavel=FrenteResponsavel.CAMPO,
            estado=Estado.AM,
            meta_interna=MetaInterna.DCS,
        )
        self.participacao = Participacao.objects.create(
            codigo="PART-00001",
            pessoa=self.pessoa,
            evento=self.evento,
            tipo_participante=TipoParticipante.PRODUTOR_RURAL,
            instituicao=self.instituicao,
        )

    def test_pessoa_str_and_creation(self):
        self.assertEqual(str(self.pessoa), "João da Silva")
        self.assertEqual(self.pessoa.cpf, "12345678901")
        self.assertIsNotNone(self.pessoa.created_at)
        self.assertIsNotNone(self.pessoa.updated_at)

    def test_instituicao_str_and_creation(self):
        self.assertEqual(str(self.instituicao), "EMBRAPA")
        self.assertIsNotNone(self.instituicao.created_at)

    def test_evento_str_and_creation(self):
        self.assertEqual(str(self.evento), "Dia de Campo Sustentável (15/06/2026)")
        self.assertEqual(self.evento.estado, "AM")

    def test_participacao_str_and_creation(self):
        self.assertEqual(str(self.participacao), "PART-00001 - João da Silva")
        self.assertEqual(self.participacao.tipo_participante, TipoParticipante.PRODUTOR_RURAL)


class ModelUniquenessConstraintsTestCase(TestCase):
    """Testes de constraints de unicidade individual e composta."""

    def test_pessoa_cpf_unique(self):
        Pessoa.objects.create(
            cpf="99988877766",
            nome="Maria Souza",
            genero=Genero.FEMININO,
            comunidade_tradicional=ComunidadeTradicional.NAO,
        )
        with self.assertRaises(IntegrityError):
            Pessoa.objects.create(
                cpf="99988877766",
                nome="Outra Maria",
                genero=Genero.FEMININO,
                comunidade_tradicional=ComunidadeTradicional.NAO,
            )

    def test_instituicao_nome_unique(self):
        Instituicao.objects.create(nome="IABS")
        with self.assertRaises(IntegrityError):
            Instituicao.objects.create(nome="IABS")

    def test_participacao_codigo_unique(self):
        pessoa = Pessoa.objects.create(
            cpf="11122233344",
            nome="Carlos Pereira",
            genero=Genero.MASCULINO,
            comunidade_tradicional=ComunidadeTradicional.QUILOMBOLA,
        )
        evento = Evento.objects.create(
            nome="Encontro Regional",
            data=date(2026, 7, 10),
            frente_responsavel=FrenteResponsavel.ATER,
            estado=Estado.PA,
            meta_interna=MetaInterna.ENCONTROS_TEMATICOS,
        )
        Participacao.objects.create(
            codigo="PART-99999",
            pessoa=pessoa,
            evento=evento,
            tipo_participante=TipoParticipante.TECNICO_ATER,
        )
        with self.assertRaises(IntegrityError):
            Participacao.objects.create(
                codigo="PART-99999",
                pessoa=pessoa,
                evento=evento,
                tipo_participante=TipoParticipante.OUTROS,
            )

    def test_evento_composite_unique_constraint(self):
        Evento.objects.create(
            nome="Curso ATER Básico",
            data=date(2026, 8, 20),
            frente_responsavel=FrenteResponsavel.CAPACITACAO,
            estado=Estado.RO,
            meta_interna=MetaInterna.FORMACAO_ATECS,
        )
        # Mesma combinação (nome, data, frente, meta) deve violar a UniqueConstraint
        with self.assertRaises(IntegrityError):
            Evento.objects.create(
                nome="Curso ATER Básico",
                data=date(2026, 8, 20),
                frente_responsavel=FrenteResponsavel.CAPACITACAO,
                estado=Estado.AM,  # Mesmo com estado diferente, a chave composta proíbe
                meta_interna=MetaInterna.FORMACAO_ATECS,
            )

    def test_evento_allows_same_name_different_dates(self):
        ev1 = Evento.objects.create(
            nome="Seminário Florestal",
            data=date(2026, 9, 1),
            frente_responsavel=FrenteResponsavel.ATER,
            estado=Estado.AM,
            meta_interna=MetaInterna.ENCONTROS_TEMATICOS,
        )
        ev2 = Evento.objects.create(
            nome="Seminário Florestal",
            data=date(2026, 9, 2),  # Data diferente
            frente_responsavel=FrenteResponsavel.ATER,
            estado=Estado.AM,
            meta_interna=MetaInterna.ENCONTROS_TEMATICOS,
        )
        self.assertNotEqual(ev1.pk, ev2.pk)


class ModelReferentialIntegrityTestCase(TestCase):
    """Testes de integridade referencial: PROTECT para Pessoa/Evento e SET_NULL para Instituicao."""

    def setUp(self):
        self.pessoa = Pessoa.objects.create(
            cpf="55566677788",
            nome="Ana Lima",
            genero=Genero.FEMININO,
            comunidade_tradicional=ComunidadeTradicional.ASSENTADO,
        )
        self.evento = Evento.objects.create(
            nome="Oficina Técnica de Campo",
            data=date(2026, 10, 5),
            frente_responsavel=FrenteResponsavel.CAMPO,
            estado=Estado.DF,
            meta_interna=MetaInterna.OFICINA_LIDERANCA,
        )
        self.instituicao = Instituicao.objects.create(nome="FUNAI")
        self.participacao = Participacao.objects.create(
            codigo="PART-00777",
            pessoa=self.pessoa,
            evento=self.evento,
            tipo_participante=TipoParticipante.PRODUTOR_RURAL,
            instituicao=self.instituicao,
        )

    def test_cannot_delete_pessoa_with_participacoes_protected(self):
        """Pessoa com participações não pode ser deletada (PROTECT)."""
        with self.assertRaises(ProtectedError):
            self.pessoa.delete()

    def test_cannot_delete_evento_with_participacoes_protected(self):
        """Evento com participações não pode ser deletado (PROTECT)."""
        with self.assertRaises(ProtectedError):
            self.evento.delete()

    def test_deleting_instituicao_sets_null_on_participacao(self):
        """Instituição pode ser removida e a participação preserva histórico com instituicao=NULL."""
        self.instituicao.delete()
        self.participacao.refresh_from_db()
        self.assertIsNone(self.participacao.instituicao)
        self.assertEqual(Participacao.objects.filter(pk=self.participacao.pk).count(), 1)
