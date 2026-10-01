"""
Testes unitários dos normalizadores de dados do SIPAC.
Garante o comportamento de funções puras de saneamento, conversões resilientes de tipos
e tratamento de números seriais do Excel e datas corrompidas.
"""

from datetime import date, datetime
import unittest
from apps.participantes.models.choices import (
    ComunidadeTradicional,
    Estado,
    FrenteResponsavel,
    Genero,
    MetaInterna,
    TipoParticipante,
)
from apps.participantes.services.importacao.normalizers import (
    UnparseableDate,
    normalize_ano,
    normalize_codigo,
    normalize_comunidade,
    normalize_cpf,
    normalize_date,
    normalize_estado,
    normalize_evento,
    normalize_frente,
    normalize_genero,
    normalize_instituicao,
    normalize_meta,
    normalize_nome,
    normalize_row,
    normalize_text,
    normalize_tipo_participante,
    strip_accents,
)


class TestNormalizers(unittest.TestCase):
    """Testes unitários para as funções puras de normalização."""

    def test_strip_accents(self):
        self.assertEqual(strip_accents("Capacitação"), "Capacitacao")
        self.assertEqual(strip_accents("Rondônia"), "Rondonia")
        self.assertEqual(strip_accents("GÊNERO"), "GENERO")
        self.assertEqual(strip_accents(""), "")

    def test_normalize_text(self):
        self.assertEqual(normalize_text("  Texto   com   espaços  "), "Texto com espaços")
        self.assertEqual(normalize_text("Linha 1\nLinha 2\tLinha 3"), "Linha 1 Linha 2 Linha 3")
        self.assertIsNone(normalize_text(None))
        self.assertIsNone(normalize_text(""))
        self.assertIsNone(normalize_text("   "))
        self.assertIsNone(normalize_text("-"))
        self.assertIsNone(normalize_text("NÃO INFORMADO"))
        self.assertIsNone(normalize_text("não informado"))
        self.assertIsNone(normalize_text("(ilegível)"))

    def test_normalize_nome(self):
        self.assertEqual(normalize_nome("  Maria   Aparecida  da  Silva "), "Maria Aparecida da Silva")
        self.assertIsNone(normalize_nome(None))
        self.assertIsNone(normalize_nome(""))

    def test_normalize_cpf(self):
        self.assertEqual(normalize_cpf("123.456.789-01"), "12345678901")
        self.assertEqual(normalize_cpf(" 002.089.351-50 "), "00208935150")
        self.assertEqual(normalize_cpf("CPF: 12345678901"), "12345678901")
        self.assertIsNone(normalize_cpf(None))
        self.assertIsNone(normalize_cpf(""))
        self.assertIsNone(normalize_cpf("-"))
        self.assertIsNone(normalize_cpf("NÃO INFORMADO"))

    def test_normalize_codigo(self):
        self.assertEqual(normalize_codigo("part-00001"), "PART-00001")
        self.assertEqual(normalize_codigo("  PART-08135  "), "PART-08135")
        self.assertIsNone(normalize_codigo(None))
        self.assertIsNone(normalize_codigo(""))

    def test_normalize_instituicao(self):
        self.assertEqual(normalize_instituicao("iabs"), "IABS")
        self.assertEqual(normalize_instituicao("  Embrapa  "), "EMBRAPA")
        self.assertIsNone(normalize_instituicao(None))
        self.assertIsNone(normalize_instituicao(""))
        self.assertIsNone(normalize_instituicao("-"))
        self.assertIsNone(normalize_instituicao("Não Informado"))
        self.assertIsNone(normalize_instituicao("NÃO INFORMADO"))

    def test_normalize_evento(self):
        self.assertEqual(normalize_evento("  Oficina   de   Manejo  "), "Oficina de Manejo")
        self.assertIsNone(normalize_evento(None))

    def test_normalize_genero(self):
        self.assertEqual(normalize_genero("Masculino"), Genero.MASCULINO.value)
        self.assertEqual(normalize_genero("MASCULINO"), Genero.MASCULINO.value)
        self.assertEqual(normalize_genero("M"), Genero.MASCULINO.value)
        self.assertEqual(normalize_genero("Feminino"), Genero.FEMININO.value)
        self.assertEqual(normalize_genero("F"), Genero.FEMININO.value)
        self.assertEqual(normalize_genero("Não informado"), Genero.NAO_INFORMADO.value)
        self.assertEqual(normalize_genero("NI"), Genero.NAO_INFORMADO.value)
        self.assertIsNone(normalize_genero(None))

    def test_normalize_comunidade(self):
        self.assertEqual(normalize_comunidade("Não"), ComunidadeTradicional.NAO.value)
        self.assertEqual(normalize_comunidade("NAO"), ComunidadeTradicional.NAO.value)
        self.assertEqual(normalize_comunidade("Ribeirinho"), ComunidadeTradicional.RIBEIRINHO.value)
        self.assertEqual(normalize_comunidade("Indígena"), ComunidadeTradicional.INDIGENA.value)
        self.assertEqual(normalize_comunidade("INDIGENA"), ComunidadeTradicional.INDIGENA.value)
        self.assertEqual(normalize_comunidade("Quilombola"), ComunidadeTradicional.QUILOMBOLA.value)
        self.assertEqual(normalize_comunidade("Assentados"), ComunidadeTradicional.ASSENTADO.value)
        self.assertEqual(normalize_comunidade("Assentado"), ComunidadeTradicional.ASSENTADO.value)
        self.assertEqual(normalize_comunidade("Outros"), ComunidadeTradicional.OUTROS.value)
        self.assertIsNone(normalize_comunidade(None))

    def test_normalize_tipo_participante(self):
        self.assertEqual(
            normalize_tipo_participante("PRODUTOR (A) RURAL"),
            TipoParticipante.PRODUTOR_RURAL.value,
        )
        self.assertEqual(
            normalize_tipo_participante("Produtor Rural"),
            TipoParticipante.PRODUTOR_RURAL.value,
        )
        self.assertEqual(
            normalize_tipo_participante("TÉCNICO DE ATER"),
            TipoParticipante.TECNICO_ATER.value,
        )
        self.assertEqual(
            normalize_tipo_participante("Tecnico de ATER"),
            TipoParticipante.TECNICO_ATER.value,
        )
        self.assertEqual(
            normalize_tipo_participante("Outros"),
            TipoParticipante.OUTROS.value,
        )
        self.assertIsNone(normalize_tipo_participante(None))

    def test_normalize_frente(self):
        self.assertEqual(normalize_frente("Campo"), FrenteResponsavel.CAMPO.value)
        self.assertEqual(normalize_frente("CAMPO"), FrenteResponsavel.CAMPO.value)
        self.assertEqual(normalize_frente("ATER"), FrenteResponsavel.ATER.value)
        self.assertEqual(normalize_frente("Capacitação"), FrenteResponsavel.CAPACITACAO.value)
        self.assertEqual(normalize_frente("CME"), FrenteResponsavel.CME.value)
        self.assertEqual(
            normalize_frente("ATER/Capacitação"),
            FrenteResponsavel.ATER_CAPACITACAO.value,
        )
        self.assertIsNone(normalize_frente(None))

    def test_normalize_meta(self):
        self.assertEqual(normalize_meta("DCs"), MetaInterna.DCS.value)
        self.assertEqual(normalize_meta("DCS"), MetaInterna.DCS.value)
        self.assertEqual(
            normalize_meta("Encontros Temáticos/ Seminários (inclui GGEs)"),
            MetaInterna.ENCONTROS_TEMATICOS.value,
        )
        self.assertEqual(
            normalize_meta("Cursos Presenciais/ Formação de ATECs"),
            MetaInterna.FORMACAO_ATECS.value,
        )
        self.assertEqual(
            normalize_meta("EAD Introdutório"),
            MetaInterna.EAD_INTRODUTORIO.value,
        )
        self.assertEqual(
            normalize_meta("Oficina de Liderança"),
            MetaInterna.OFICINA_LIDERANCA.value,
        )
        self.assertEqual(
            normalize_meta("EAD Avançado"),
            MetaInterna.EAD_AVANCADO.value,
        )
        self.assertIsNone(normalize_meta(None))

    def test_normalize_estado(self):
        self.assertEqual(normalize_estado("Amazonas"), Estado.AM.value)
        self.assertEqual(normalize_estado("AMAZONAS"), Estado.AM.value)
        self.assertEqual(normalize_estado("AM"), Estado.AM.value)
        self.assertEqual(normalize_estado("Pará"), Estado.PA.value)
        self.assertEqual(normalize_estado("PARA"), Estado.PA.value)
        self.assertEqual(normalize_estado("Rondônia"), Estado.RO.value)
        self.assertEqual(normalize_estado("Distrito Federal"), Estado.DF.value)
        self.assertIsNone(normalize_estado(None))

    def test_normalize_ano(self):
        self.assertEqual(normalize_ano(2026), 2026)
        self.assertEqual(normalize_ano("2026"), 2026)
        self.assertEqual(normalize_ano(2026.0), 2026)
        self.assertIsNone(normalize_ano(None))
        self.assertIsNone(normalize_ano("NÃO INFORMADO"))
        self.assertIsNone(normalize_ano("abc"))

    def test_normalize_date(self):
        # Date e datetime nativos
        self.assertEqual(normalize_date(date(2026, 6, 15)), date(2026, 6, 15))
        self.assertEqual(normalize_date(datetime(2026, 6, 15, 10, 30)), date(2026, 6, 15))

        # Serial Excel numérico (ex: 46261 -> 2026-08-27)
        self.assertEqual(normalize_date(46261), date(2026, 8, 27))
        self.assertEqual(normalize_date(46261.0), date(2026, 8, 27))
        self.assertEqual(normalize_date("46261"), date(2026, 8, 27))

        # Strings formatadas
        self.assertEqual(normalize_date("15/06/2026"), date(2026, 6, 15))
        self.assertEqual(normalize_date("15-06-2026"), date(2026, 6, 15))
        self.assertEqual(normalize_date("2026-06-15"), date(2026, 6, 15))
        self.assertEqual(normalize_date("06/15/2026"), date(2026, 6, 15))
        self.assertEqual(normalize_date(".07/09/2000"), date(2000, 9, 7))
        self.assertEqual(normalize_date("15062026"), date(2026, 6, 15))

        # Ausências legítimas
        self.assertIsNone(normalize_date(None))
        self.assertIsNone(normalize_date(""))
        self.assertIsNone(normalize_date("   "))
        self.assertIsNone(normalize_date("-"))
        self.assertIsNone(normalize_date("NÃO INFORMADO"))
        self.assertIsNone(normalize_date("NÃO INFORMADA"))

        # Formatos corrompidos retornam UnparseableDate
        res = normalize_date("29/061995")
        self.assertIsInstance(res, UnparseableDate)
        self.assertEqual(str(res), "29/061995")

        res_invalid = normalize_date("data_corrompida")
        self.assertIsInstance(res_invalid, UnparseableDate)

    def test_normalize_row(self):
        raw_row = {
            "codigo": " part-00010 ",
            "evento": "  Curso Manejo  ",
            "frente_responsavel": "Campo",
            "meta_interna": "DCs",
            "data_evento": 46261,
            "ano": "2026",
            "nome": "  Carlos  Alberto ",
            "cpf": " 123.456.789-01 ",
            "data_nascimento": " 10/05/1990 ",
            "genero": "Masculino",
            "comunidade_tradicional": "Ribeirinho",
            "tipo_participante": "Produtor Rural",
            "estado": "Amazonas",
            "instituicao": "  iabs ",
        }
        normalized = normalize_row(raw_row)

        self.assertEqual(normalized["codigo"], "PART-00010")
        self.assertEqual(normalized["evento"], "Curso Manejo")
        self.assertEqual(normalized["frente_responsavel"], "CAMPO")
        self.assertEqual(normalized["meta_interna"], "DCS")
        self.assertEqual(normalized["data_evento"], date(2026, 8, 27))
        self.assertEqual(normalized["ano"], 2026)
        self.assertEqual(normalized["nome"], "Carlos Alberto")
        self.assertEqual(normalized["cpf"], "12345678901")
        self.assertEqual(normalized["data_nascimento"], date(1990, 5, 10))
        self.assertEqual(normalized["genero"], "M")
        self.assertEqual(normalized["comunidade_tradicional"], "RIBEIRINHO")
        self.assertEqual(normalized["tipo_participante"], "PRODUTOR_RURAL")
        self.assertEqual(normalized["estado"], "AM")
        self.assertEqual(normalized["instituicao"], "IABS")
