"""
Catálogos de TextChoices oficiais do domínio do SIPAC.
Centraliza todos os enums e escolhas controladas do sistema.
"""

from django.db import models


class Genero(models.TextChoices):
    MASCULINO = "M", "Masculino"
    FEMININO = "F", "Feminino"
    NAO_INFORMADO = "NI", "Não informado"


class ComunidadeTradicional(models.TextChoices):
    NAO = "NAO", "Não"
    INDIGENA = "INDIGENA", "Indígena"
    RIBEIRINHO = "RIBEIRINHO", "Ribeirinho"
    QUILOMBOLA = "QUILOMBOLA", "Quilombola"
    ASSENTADO = "ASSENTADO", "Assentado"
    OUTROS = "OUTROS", "Outros"


class Estado(models.TextChoices):
    AC = "AC", "Acre"
    AL = "AL", "Alagoas"
    AP = "AP", "Amapá"
    AM = "AM", "Amazonas"
    BA = "BA", "Bahia"
    CE = "CE", "Ceará"
    DF = "DF", "Distrito Federal"
    ES = "ES", "Espírito Santo"
    GO = "GO", "Goiás"
    MA = "MA", "Maranhão"
    MT = "MT", "Mato Grosso"
    MS = "MS", "Mato Grosso do Sul"
    MG = "MG", "Minas Gerais"
    PA = "PA", "Pará"
    PB = "PB", "Paraíba"
    PR = "PR", "Paraná"
    PE = "PE", "Pernambuco"
    PI = "PI", "Piauí"
    RJ = "RJ", "Rio de Janeiro"
    RN = "RN", "Rio Grande do Norte"
    RS = "RS", "Rio Grande do Sul"
    RO = "RO", "Rondônia"
    RR = "RR", "Roraima"
    SC = "SC", "Santa Catarina"
    SP = "SP", "São Paulo"
    SE = "SE", "Sergipe"
    TO = "TO", "Tocantins"


class FrenteResponsavel(models.TextChoices):
    ATER = "ATER", "ATER"
    CAPACITACAO = "CAPACITACAO", "CAPACITAÇÃO"
    CME = "CME", "CME"
    CAMPO = "CAMPO", "CAMPO"
    ATER_CAPACITACAO = "ATER_CAPACITACAO", "ATER/Capacitação"


class MetaInterna(models.TextChoices):
    DCS = "DCS", "DCs"
    ENCONTROS_TEMATICOS = (
        "ENCONTROS_TEMATICOS",
        "Encontros Temáticos/ Seminários (inclui GGEs)",
    )
    FORMACAO_ATECS = (
        "FORMACAO_ATECS",
        "Cursos Presenciais/ Formação de ATECs",
    )
    EAD_INTRODUTORIO = "EAD_INTRODUTORIO", "EAD Introdutório"
    OFICINA_LIDERANCA = "OFICINA_LIDERANCA", "Oficina de Liderança"
    EAD_AVANCADO = "EAD_AVANCADO", "EAD Avançado"


class TipoParticipante(models.TextChoices):
    PRODUTOR_RURAL = "PRODUTOR_RURAL", "Produtor(a) Rural"
    TECNICO_ATER = "TECNICO_ATER", "Técnico de ATER"
    OUTROS = "OUTROS", "Outros"
