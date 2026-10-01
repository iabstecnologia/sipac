"""
Testes unitários para as regras de validação de negócio do SIPAC.
Garante o cálculo do algoritmo de CPF, limites temporais de nascimento e atividade,
checagem rigorosa de escolhas (choices) e consistência anual.
"""

from datetime import date, timedelta
import unittest
from apps.participantes.models.choices import (
    ComunidadeTradicional,
    Estado,
    FrenteResponsavel,
    Genero,
    MetaInterna,
    TipoParticipante,
)
from apps.participantes.services.importacao.normalizers import UnparseableDate
from apps.participantes.services.importacao.validators import (
    validate_ano_consistencia,
    validate_choice,
    validate_codigo,
    validate_cpf,
    validate_data_evento,
    validate_data_nascimento,
    validate_evento_nome,
    validate_nome,
    validate_row,
)


class TestValidators(unittest.TestCase):
    """Bateria de testes unitários para a camada de validação."""

    def test_validate_cpf_valid(self):
        # CPFs matematicamente válidos
        valid_cpfs = [
            "00208935150",
            "81060360225",
            "94908990204",
            "03911951159",
            "78329175200",
        ]
        for cpf in valid_cpfs:
            with self.subTest(cpf=cpf):
                errors = validate_cpf(cpf)
                self.assertEqual(errors, [], f"CPF {cpf} deveria ser válido")

    def test_validate_cpf_missing_and_empty(self):
        self.assertEqual(validate_cpf(None)[0].code, "missing_cpf")
        self.assertEqual(validate_cpf("")[0].code, "missing_cpf")
        self.assertEqual(validate_cpf("   ")[0].code, "missing_cpf")

    def test_validate_cpf_invalid_length(self):
        errors = validate_cpf("12345")
        self.assertEqual(errors[0].code, "invalid_length")
        errors = validate_cpf("123456789012")
        self.assertEqual(errors[0].code, "invalid_length")

    def test_validate_cpf_repeated_digits(self):
        # Sequências de 11 dígitos idênticos passam pela soma de DV em alguns casos mas são formalmente proibidas
        for digit in "0123456789":
            cpf = digit * 11
            with self.subTest(cpf=cpf):
                errors = validate_cpf(cpf)
                self.assertTrue(len(errors) > 0)
                self.assertEqual(errors[0].code, "repeated_digits")

    def test_validate_cpf_invalid_dv(self):
        # 00208935150 é válido; mudando o último dígito para 1
        errors = validate_cpf("00208935151")
        self.assertEqual(len(errors), 1)
        self.assertEqual(errors[0].code, "invalid_dv")

        # Mudando o primeiro dígito verificador
        errors = validate_cpf("00208935160")
        self.assertEqual(len(errors), 1)
        self.assertEqual(errors[0].code, "invalid_dv")

    def test_validate_data_nascimento_valid_and_optional(self):
        # Campo opcional: None não gera erro
        self.assertEqual(validate_data_nascimento(None), [])

        # Data válida no passado
        self.assertEqual(validate_data_nascimento(date(1995, 6, 20)), [])
        self.assertEqual(validate_data_nascimento(date(1900, 1, 1)), [])
        self.assertEqual(validate_data_nascimento(date.today()), [])

    def test_validate_data_nascimento_unparseable(self):
        errors = validate_data_nascimento(UnparseableDate("29/061995"))
        self.assertEqual(len(errors), 1)
        self.assertEqual(errors[0].code, "invalid_date_format")

    def test_validate_data_nascimento_implausible_past(self):
        # Datas anteriores a 1900 são barradas (como 1693 identificado na planilha)
        errors = validate_data_nascimento(date(1693, 2, 10))
        self.assertEqual(len(errors), 1)
        self.assertEqual(errors[0].code, "implausible_past_date")

    def test_validate_data_nascimento_future(self):
        future_date = date.today() + timedelta(days=1)
        errors = validate_data_nascimento(future_date)
        self.assertEqual(len(errors), 1)
        self.assertEqual(errors[0].code, "future_date")

    def test_validate_data_evento_valid(self):
        self.assertEqual(validate_data_evento(date(2026, 6, 15)), [])

    def test_validate_data_evento_missing(self):
        # Obrigatória: None gera erro
        errors = validate_data_evento(None)
        self.assertEqual(len(errors), 1)
        self.assertEqual(errors[0].code, "missing_event_date")

    def test_validate_data_evento_unparseable(self):
        errors = validate_data_evento(UnparseableDate("NÃO INFORMADO"))
        self.assertEqual(len(errors), 1)
        self.assertEqual(errors[0].code, "invalid_event_date_format")

    def test_validate_data_evento_out_of_bounds(self):
        errors = validate_data_evento(date(1999, 12, 31))
        self.assertEqual(len(errors), 1)
        self.assertEqual(errors[0].code, "implausible_event_date")

    def test_validate_choice(self):
        # Sucesso
        self.assertEqual(validate_choice("M", Genero, "genero", "Gênero"), [])
        self.assertEqual(validate_choice("AM", Estado, "estado", "UF"), [])

        # Inválido
        errors = validate_choice("XYZ", Estado, "estado", "UF")
        self.assertEqual(len(errors), 1)
        self.assertEqual(errors[0].code, "invalid_estado")

        # Nulo
        errors = validate_choice(None, Estado, "estado", "UF")
        self.assertEqual(len(errors), 1)
        self.assertEqual(errors[0].code, "missing_estado")

    def test_validate_codigo(self):
        self.assertEqual(validate_codigo("PART-00001"), [])
        self.assertEqual(validate_codigo(None)[0].code, "missing_codigo")
        self.assertEqual(validate_codigo("   ")[0].code, "missing_codigo")

    def test_validate_nome(self):
        self.assertEqual(validate_nome("João da Silva"), [])
        self.assertEqual(validate_nome(None)[0].code, "missing_nome")
        self.assertEqual(validate_nome("")[0].code, "missing_nome")

    def test_validate_evento_nome(self):
        self.assertEqual(validate_evento_nome("Dia de Campo"), [])
        self.assertEqual(validate_evento_nome(None)[0].code, "missing_evento")
        self.assertEqual(validate_evento_nome("")[0].code, "missing_evento")

    def test_validate_ano_consistencia(self):
        # Mesmo ano
        self.assertEqual(validate_ano_consistencia(2026, date(2026, 8, 20)), [])

        # Ano divergente
        errors = validate_ano_consistencia(2025, date(2026, 8, 20))
        self.assertEqual(len(errors), 1)
        self.assertEqual(errors[0].code, "inconsistent_year")

        # Ano não informado não quebra consistência
        self.assertEqual(validate_ano_consistencia(None, date(2026, 8, 20)), [])

    def test_validate_row_valid(self):
        valid_row = {
            "codigo": "PART-00001",
            "evento": "Dia de Campo",
            "frente_responsavel": FrenteResponsavel.CAMPO.value,
            "meta_interna": MetaInterna.DCS.value,
            "data_evento": date(2026, 6, 15),
            "ano": 2026,
            "nome": "João da Silva",
            "cpf": "52998224725",
            "data_nascimento": date(1985, 3, 10),
            "genero": Genero.MASCULINO.value,
            "comunidade_tradicional": ComunidadeTradicional.RIBEIRINHO.value,
            "tipo_participante": TipoParticipante.PRODUTOR_RURAL.value,
            "estado": Estado.AM.value,
            "instituicao": "EMBRAPA",
        }
        errors = validate_row(valid_row)
        self.assertEqual(errors, [])

    def test_validate_row_multiple_errors(self):
        invalid_row = {
            "codigo": "",  # missing_codigo
            "evento": None,  # missing_evento
            "frente_responsavel": "FRENTE_INEXISTENTE",  # invalid_frente_responsavel
            "meta_interna": MetaInterna.DCS.value,
            "data_evento": None,  # missing_event_date
            "ano": 2026,
            "nome": "",  # missing_nome
            "cpf": "00000000000",  # repeated_digits
            "data_nascimento": date(1850, 1, 1),  # implausible_past_date
            "genero": "INVALID",  # invalid_genero
            "comunidade_tradicional": ComunidadeTradicional.NAO.value,
            "tipo_participante": TipoParticipante.PRODUTOR_RURAL.value,
            "estado": "XX",  # invalid_estado
            "instituicao": None,  # válido ser None
        }
        errors = validate_row(invalid_row)
        error_codes = [e.code for e in errors]

        self.assertIn("missing_codigo", error_codes)
        self.assertIn("missing_evento", error_codes)
        self.assertIn("missing_nome", error_codes)
        self.assertIn("missing_event_date", error_codes)
        self.assertIn("repeated_digits", error_codes)
        self.assertIn("implausible_past_date", error_codes)
        self.assertIn("invalid_frente_responsavel", error_codes)
        self.assertIn("invalid_genero", error_codes)
        self.assertIn("invalid_estado", error_codes)
