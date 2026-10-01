"""
Constantes, mapeamentos de enums e aliases de cabeçalho do pipeline de importação.
"""

from apps.participantes.models.choices import (
    ComunidadeTradicional,
    Estado,
    FrenteResponsavel,
    Genero,
    MetaInterna,
    TipoParticipante,
)

# Valores textuais que representam estritamente a ausência semântica de dado
EMPTY_VALUES: frozenset[str] = frozenset(
    {
        "",
        "-",
        "--",
        "---",
        "N/A",
        "NA",
        "NONE",
        "NULL",
        "NÃO INFORMADO",
        "NAO INFORMADO",
        "NÃO INFORMADA",
        "NAO INFORMADA",
        "(NÃO INFORMADO)",
        "(NAO INFORMADO)",
        "(NÃO INFORMADA)",
        "(NAO INFORMADA)",
        "(ILEGÍVEL)",
        "(ILEGIVEL)",
        "ILEGÍVEL",
        "ILEGIVEL",
        "SEM INFORMAÇÃO",
        "SEM INFORMACAO",
        ".",
    }
)

# Colunas canônicas esperadas da planilha
REQUIRED_CANONICAL_COLUMNS: frozenset[str] = frozenset(
    {
        "codigo",
        "evento",
        "frente_responsavel",
        "meta_interna",
        "data_evento",
        "nome",
        "cpf",
        "data_nascimento",
        "comunidade_tradicional",
        "tipo_participante",
        "genero",
        "estado",
        "instituicao",
    }
)

# Mapeamento de cabeçalhos brutos da planilha Excel para as chaves canônicas internas
HEADER_ALIASES: dict[str, str] = {
    # Código de participação
    "COD PARTICIPAÇÃO": "codigo",
    "COD PARTICIPACAO": "codigo",
    "CODIGO DA PARTICIPAÇÃO": "codigo",
    "CODIGO DA PARTICIPACAO": "codigo",
    "CÓDIGO DA PARTICIPAÇÃO": "codigo",
    "CODIGO": "codigo",
    "CÓDIGO": "codigo",
    # Evento
    "EVENTO": "evento",
    "NOME DO EVENTO": "evento",
    "ATIVIDADE": "evento",
    # Frente Responsável (inclui o cabeçalho original com erro de digitação)
    "FRENTE RESPONSÁVAEL": "frente_responsavel",
    "FRENTE RESPONSAVEL": "frente_responsavel",
    "FRENTE RESPONSÁVEL": "frente_responsavel",
    "FRENTE": "frente_responsavel",
    # Metas Internas
    "METAS INTERNAS": "meta_interna",
    "META INTERNA": "meta_interna",
    "METAS": "meta_interna",
    "META": "meta_interna",
    # Data da atividade
    "DATA DA ATIVIDADE": "data_evento",
    "DATA DO EVENTO": "data_evento",
    "DATA": "data_evento",
    # Ano (coluna de consistência)
    "ANO": "ano",
    # Participante (Nome)
    "PARTICIPANTE": "nome",
    "NOME": "nome",
    "NOME DO PARTICIPANTE": "nome",
    # CPF
    "CPF": "cpf",
    # Data de nascimento
    "DATA DE NASCIMENTO": "data_nascimento",
    "DT NASCIMENTO": "data_nascimento",
    "NASCIMENTO": "data_nascimento",
    # Comunidade tradicional
    "FAZ PARTE DE COMUNIDADE TRADICIONAL": "comunidade_tradicional",
    "COMUNIDADE TRADICIONAL": "comunidade_tradicional",
    # Tipo do participante
    "TIPO DO PARTICIPANTE": "tipo_participante",
    "TIPO DE PARTICIPANTE": "tipo_participante",
    "TIPO PARTICIPANTE": "tipo_participante",
    # Gênero
    "GÊNERO": "genero",
    "GENERO": "genero",
    "SEXO": "genero",
    # Estado (UF)
    "ESTADO": "estado",
    "UF": "estado",
    # Instituição
    "INSTITUIÇÃO": "instituicao",
    "INSTITUICAO": "instituicao",
    # Colunas auxiliares da planilha (ignoradas para persistência)
    "CONTADOR DE NOMES": "contador_nomes",
    "CONTADOR DE CPFS": "contador_cpfs",
    "CONTADORES DIFERENTES": "contadores_diferentes",
    "VALIDADOR CPF": "validador_cpf",
}

# Mapeamentos para choices controlados

GENERO_MAPPING: dict[str, str] = {
    "M": Genero.MASCULINO.value,
    "MASCULINO": Genero.MASCULINO.value,
    "F": Genero.FEMININO.value,
    "FEMININO": Genero.FEMININO.value,
    "NI": Genero.NAO_INFORMADO.value,
    "NAO INFORMADO": Genero.NAO_INFORMADO.value,
    "NÃO INFORMADO": Genero.NAO_INFORMADO.value,
}

COMUNIDADE_MAPPING: dict[str, str] = {
    "NAO": ComunidadeTradicional.NAO.value,
    "NÃO": ComunidadeTradicional.NAO.value,
    "INDIGENA": ComunidadeTradicional.INDIGENA.value,
    "INDÍGENA": ComunidadeTradicional.INDIGENA.value,
    "RIBEIRINHO": ComunidadeTradicional.RIBEIRINHO.value,
    "QUILOMBOLA": ComunidadeTradicional.QUILOMBOLA.value,
    "ASSENTADO": ComunidadeTradicional.ASSENTADO.value,
    "ASSENTADOS": ComunidadeTradicional.ASSENTADO.value,
    "OUTROS": ComunidadeTradicional.OUTROS.value,
    "OUTRO": ComunidadeTradicional.OUTROS.value,
}

TIPO_PARTICIPANTE_MAPPING: dict[str, str] = {
    "PRODUTOR RURAL": TipoParticipante.PRODUTOR_RURAL.value,
    "PRODUTOR (A) RURAL": TipoParticipante.PRODUTOR_RURAL.value,
    "PRODUTOR(A) RURAL": TipoParticipante.PRODUTOR_RURAL.value,
    "PRODUTOR A RURAL": TipoParticipante.PRODUTOR_RURAL.value,
    "PRODUTORA RURAL": TipoParticipante.PRODUTOR_RURAL.value,
    "TECNICO DE ATER": TipoParticipante.TECNICO_ATER.value,
    "TÉCNICO DE ATER": TipoParticipante.TECNICO_ATER.value,
    "TECNICO ATER": TipoParticipante.TECNICO_ATER.value,
    "OUTROS": TipoParticipante.OUTROS.value,
    "OUTRO": TipoParticipante.OUTROS.value,
}

FRENTE_MAPPING: dict[str, str] = {
    "ATER": FrenteResponsavel.ATER.value,
    "CAPACITACAO": FrenteResponsavel.CAPACITACAO.value,
    "CAPACITAÇÃO": FrenteResponsavel.CAPACITACAO.value,
    "CME": FrenteResponsavel.CME.value,
    "CAMPO": FrenteResponsavel.CAMPO.value,
    "ATER/CAPACITACAO": FrenteResponsavel.ATER_CAPACITACAO.value,
    "ATER/CAPACITAÇÃO": FrenteResponsavel.ATER_CAPACITACAO.value,
}

META_MAPPING: dict[str, str] = {
    "DCS": MetaInterna.DCS.value,
    "ENCONTROS TEMATICOS/ SEMINARIOS (INCLUI GGES)": MetaInterna.ENCONTROS_TEMATICOS.value,
    "ENCONTROS TEMÁTICOS/ SEMINÁRIOS (INCLUI GGES)": MetaInterna.ENCONTROS_TEMATICOS.value,
    "ENCONTROS TEMATICOS": MetaInterna.ENCONTROS_TEMATICOS.value,
    "CURSOS PRESENCIAIS/ FORMACAO DE ATECS": MetaInterna.FORMACAO_ATECS.value,
    "CURSOS PRESENCIAIS/ FORMAÇÃO DE ATECS": MetaInterna.FORMACAO_ATECS.value,
    "FORMACAO DE ATECS": MetaInterna.FORMACAO_ATECS.value,
    "EAD INTRODUTORIO": MetaInterna.EAD_INTRODUTORIO.value,
    "EAD INTRODUTÓRIO": MetaInterna.EAD_INTRODUTORIO.value,
    "OFICINA DE LIDERANCA": MetaInterna.OFICINA_LIDERANCA.value,
    "OFICINA DE LIDERANÇA": MetaInterna.OFICINA_LIDERANCA.value,
    "EAD AVANCADO": MetaInterna.EAD_AVANCADO.value,
    "EAD AVANÇADO": MetaInterna.EAD_AVANCADO.value,
}

ESTADO_MAPPING: dict[str, str] = {
    # Siglas diretas
    "AC": Estado.AC.value,
    "AL": Estado.AL.value,
    "AP": Estado.AP.value,
    "AM": Estado.AM.value,
    "BA": Estado.BA.value,
    "CE": Estado.CE.value,
    "DF": Estado.DF.value,
    "ES": Estado.ES.value,
    "GO": Estado.GO.value,
    "MA": Estado.MA.value,
    "MT": Estado.MT.value,
    "MS": Estado.MS.value,
    "MG": Estado.MG.value,
    "PA": Estado.PA.value,
    "PB": Estado.PB.value,
    "PR": Estado.PR.value,
    "PE": Estado.PE.value,
    "PI": Estado.PI.value,
    "RJ": Estado.RJ.value,
    "RN": Estado.RN.value,
    "RS": Estado.RS.value,
    "RO": Estado.RO.value,
    "RR": Estado.RR.value,
    "SC": Estado.SC.value,
    "SP": Estado.SP.value,
    "SE": Estado.SE.value,
    "TO": Estado.TO.value,
    # Nomes por extenso
    "ACRE": Estado.AC.value,
    "ALAGOAS": Estado.AL.value,
    "AMAPA": Estado.AP.value,
    "AMAPÁ": Estado.AP.value,
    "AMAZONAS": Estado.AM.value,
    "BAHIA": Estado.BA.value,
    "CEARA": Estado.CE.value,
    "CEARÁ": Estado.CE.value,
    "DISTRITO FEDERAL": Estado.DF.value,
    "ESPIRITO SANTO": Estado.ES.value,
    "ESPÍRITO SANTO": Estado.ES.value,
    "GOIAS": Estado.GO.value,
    "GOIÁS": Estado.GO.value,
    "MARANHAO": Estado.MA.value,
    "MARANHÃO": Estado.MA.value,
    "MATO GROSSO": Estado.MT.value,
    "MATO GROSSO DO SUL": Estado.MS.value,
    "MINAS GERAIS": Estado.MG.value,
    "PARA": Estado.PA.value,
    "PARÁ": Estado.PA.value,
    "PARAIBA": Estado.PB.value,
    "PARAÍBA": Estado.PB.value,
    "PARANA": Estado.PR.value,
    "PARANÁ": Estado.PR.value,
    "PERNAMBUCO": Estado.PE.value,
    "PIAUI": Estado.PI.value,
    "PIAUÍ": Estado.PI.value,
    "RIO DE JANEIRO": Estado.RJ.value,
    "RIO GRANDE DO NORTE": Estado.RN.value,
    "RIO GRANDE DO SUL": Estado.RS.value,
    "RONDONIA": Estado.RO.value,
    "RONDÔNIA": Estado.RO.value,
    "RORAIMA": Estado.RR.value,
    "SANTA CATARINA": Estado.SC.value,
    "SAO PAULO": Estado.SP.value,
    "SÃO PAULO": Estado.SP.value,
    "SERGIPE": Estado.SE.value,
    "TOCANTINS": Estado.TO.value,
}
