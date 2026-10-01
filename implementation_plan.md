# SIPAC — Sistema de Informações de Participação e Capacitação
## Plano de Trabalho e Implementação (Roadmap Executivo)

O **SIPAC** é uma aplicação web em Django voltada para o saneamento, importação estruturada e análise consolidada de participações em atividades e eventos de capacitação rural/ATER. O sistema substitui o controle manual em planilha por um banco relacional auditável e oferece dashboards executivos com filtros e indicadores para tomada de decisão.

---

## 1. Diagnóstico da Planilha Real (`sipac_participacoes.xlsx`)

A análise técnica executada diretamente sobre a planilha na raiz do projeto revelou as seguintes características e métricas reais:

* **Volume total:** 8.224 linhas no arquivo (1 linha de cabeçalho + **8.135 registros de dados preenchidos** + 88 linhas finais em branco que devem ser descartadas pelo `Reader`).
* **Código de Participação:** A coluna real no arquivo chama-se `COD PARTICIPAÇÃO`.
  * Possui 8.135 códigos únicos (`PART-00001` até `PART-08135`).
  * **0 duplicidades de código** na planilha atual.
* **Pessoas / CPFs:**
  * 4.398 CPFs únicos no universo de 8.135 participações.
  * Coluna auxiliar `VALIDADOR CPF` presente na planilha marca **8.036 VÁLIDOS** e **99 INVÁLIDOS** (CPFs com erro de digitação, letras 'RG', máscara truncada ou dígitos verificadores matematicamente incorretos).
* **Eventos:**
  * 187 nomes distintos de atividades/eventos.
  * 395 combinações únicas de `(Evento, Data, Frente, Meta)`.
  * **141 registros possuem `DATA DA ATIVIDADE = 'NÃO INFORMADO'`** (o que impossibilita a criação do Evento sem uma data ou sem regra de contingência).
  * **Conflito de Estados:** Foram identificados **7 eventos** com a mesma tupla `(Nome, Data, Frente, Meta)` associados a estados diferentes na planilha (ex.: *Dia de Campo 1* em `Amazonas` e `Rondônia`).
* **Datas (Atividade e Nascimento):**
  * Excel armazena grande parte das datas como inteiros seriais (ex.: `46261` = 16/08/2026), exigindo suporte nativo a seriais no `Normalizer`.
  * `DATA DE NASCIMENTO` contém 110 registros `'NÃO INFORMADA'`, strings de ausência (`'(não informado)'`, `'(ilegível)'`), anomalias de digitação (`'29/061995'`, `'.07/09/2000'`) e datas inverossímeis (`'10/02/1693'`, `'01/04/0378'`).
* **Instituições:**
  * 358 grafias distintas.
  * 2.440 registros com célula vazia + 875 registros `'Não Informado'` + 206 registros `'-'` + 199 registros `'NÃO INFORMADO'`. Todos devem normalizar para `None` (`NULL` no banco).
* **Campos Categóricos:**
  * `GÊNERO`: `MASCULINO`, `FEMININO`, `NÃO INFORMADO`, `Masculino` (normalizados para `M`, `F`, `NI`).
  * `COMUNIDADE TRADICIONAL`: `NÃO`, `RIBEIRINHO`, `INDÍGENA`, `OUTROS`, `ASSENTADOS`, `QUILOMBOLA`.
  * `FRENTE RESPONSÁVAEL` (com erro de digitação no cabeçalho): `ATER`, `CAPACITAÇÃO`, `CME`, `CAMPO`, `ATER/Capacitação`, `Campo`.
  * `METAS INTERNAS`: `DCs`, `Encontros Temáticos/ Seminários (inclui GGEs)`, `Cursos Presenciais/ Formação de ATECs`, `EAD Introdutório`, `Oficina de Liderança`, `EAD Avançado`.
  * `TIPO DO PARTICIPANTE`: `PRODUTOR (A) RURAL`, `OUTROS`, `TÉCNICO DE ATER`.
  * `ESTADO`: 15 representações (ex.: `Amazonas`, `AMAZONAS`, `Pará`, etc., mapeadas para siglas UF de 2 letras).

---

## 2. Decisões Arquiteturais e Alinhamentos

> [!IMPORTANT]
> **Versão do Django & Banco de Dados:**
> * O Django está atualmente na série **5.1 LTS / 5.2** (Django 6.0/6.1 ainda não foram lançados oficialmente). Utilizaremos `Django>=5.1` para máxima estabilidade e compatibilidade com o Python 3.12 instalado.
> * Configuraremos suporte duplo a banco de dados: **SQLite** por padrão para desenvolvimento local ágil e execução de testes isolados sem dependências externas, e **PostgreSQL** (via `psycopg` e `.env`) para ambientes de homologação/produção.

> [!WARNING]
> **Resolução dos Conflitos de Estado em Eventos:**
> O modelo define unicidade em `Evento` por `("nome", "data", "frente_responsavel", "meta_interna")` sem o `estado`. Como 7 eventos na planilha ocorrem em estados distintos com a mesma data e nome, a importação detectará inconsistência se o estado for diferente. No pipeline, esse cenário será tratado como erro de consistência ou o `estado` deve fazer parte da chave lógica do evento.

> [!NOTE]
> **Tratamento dos 141 Eventos com Data "NÃO INFORMADO":**
> Como `Evento.data` é `null=False`, esses registros serão barrados pelo `Validator` como erro impeditivo na Fase 1 (Pré-validação), permitindo ao usuário auditar a linha exata no relatório de inconsistências antes de qualquer gravação.

---

## 3. Plano de Trabalho Faseado

O projeto será implementado em **6 Fases lógicas e sequenciais**, garantindo validação contínua e cobertura de testes em cada marco:

```
FASE 1: Fundação do Projeto & Ambiente
    │
    ▼
FASE 2: Modelagem de Dados & Domínio
    │
    ▼
FASE 3: Engenharia do Pipeline de Importação (Core)
    │
    ▼
FASE 4: Interface Web de Importação (Upload, Preview e Persistência)
    │
    ▼
FASE 5: Engenharia do Dashboard Analítico
    │
    ▼
FASE 6: Refinamento, Auditoria & Documentação
```

---

### FASE 1: Fundação do Projeto & Infraestrutura Inicial
**Objetivo:** Estabelecer a estrutura física do repositório, ambiente virtual, configurações modularizadas e baseline visual.

* [x] **Passo 1.1: Inicialização do Ambiente e Dependências**
  * Criar/confirmar o virtualenv Python 3.12 (`.venv`).
  * Criar `requirements.txt` com as bibliotecas essenciais:
    * `Django>=5.1,<6.0`
    * `openpyxl>=3.1.2`
    * `psycopg[binary]>=3.2.0`
    * `python-dotenv>=1.0.1`
  * Configurar `.gitignore` robusto (incluindo `.env`, `.venv/`, `*.xlsx`, `db.sqlite3`, `media/`, `staticfiles/`).
  * Criar `.env.example` e `.env` local.
* [x] **Passo 1.2: Modularização dos Settings Django**
  * Estruturar `config/`:
    * `config/settings/base.py` (apps comuns, middleware, i18n para `pt-br`, tz `America/Sao_Paulo`, media/static).
    * `config/settings/local.py` (debug ativo, banco SQLite padrão ou postgres via env).
    * `config/settings/production.py` (segurança, WhiteNoise/Nginx, postgres).
  * Atualizar `manage.py`, `wsgi.py` e `asgi.py` para apontar para `config.settings.local`.
* [x] **Passo 1.3: Criação do App Central `apps/participantes`**
  * Criar diretório `apps/` com `__init__.py`.
  * Registrar `apps.participantes.apps.ParticipantesConfig` em `INSTALLED_APPS`.
* [x] **Passo 1.4: Layout Base e Assets CDN**
  * Criar template base global `templates/base.html` com Bootstrap 5.3 (CDN), Bootstrap Icons e bloco para Chart.js.
  * Criar estrutura de diretórios para `static/css`, `static/js` e `media/`.
  * Criar página inicial temporária (health check / boas-vindas).

---

### FASE 2: Modelagem de Dados & Domínio
**Objetivo:** Construir as entidades relacionais no banco de dados respeitando o dicionário de dados v1.0 e as regras de integridade referencial.

* [x] **Passo 2.1: Model Base e Catálogos de Choices**
  * Criar `apps/participantes/models/base.py`:
    * `TimeStampedModel` abstrato com `created_at` e `updated_at`.
  * Criar `apps/participantes/models/choices.py`:
    * `Genero` (`M`, `F`, `NI`).
    * `ComunidadeTradicional` (`NAO`, `INDIGENA`, `RIBEIRINHO`, `QUILOMBOLA`, `ASSENTADO`, `OUTROS`).
    * `Estado` (27 siglas UF oficiais do Brasil).
    * `FrenteResponsavel` (`ATER`, `CAPACITACAO`, `CME`, `CAMPO`, `ATER_CAPACITACAO`).
    * `MetaInterna` (`DCS`, `ENCONTROS_TEMATICOS`, `FORMACAO_ATECS`, `EAD_INTRODUTORIO`, `OFICINA_LIDERANCA`, `EAD_AVANCADO`).
    * `TipoParticipante` (`PRODUTOR_RURAL`, `TECNICO_ATER`, `OUTROS`).
* [x] **Passo 2.2: Models de Domínio**
  * `apps/participantes/models/pessoa.py`:
    * `Pessoa` (`cpf` unique char(11), `nome` char(255), `data_nascimento` date null, `genero` char(2), `comunidade_tradicional` char(20)).
  * `apps/participantes/models/instituicao.py`:
    * `Instituicao` (`nome` unique char(255)).
  * `apps/participantes/models/evento.py`:
    * `Evento` (`nome`, `data`, `frente_responsavel`, `estado`, `meta_interna`), `UniqueConstraint(fields=['nome', 'data', 'frente_responsavel', 'meta_interna'])` e índices em `data` e `(estado, data)`.
  * `apps/participantes/models/participacao.py`:
    * `Participacao` (`codigo` unique char(50), `pessoa` FK PROTECT, `evento` FK PROTECT, `tipo_participante` char(30), `instituicao` FK SET_NULL null=True).
* [x] **Passo 2.3: Configuração do Django Admin**
  * Registrar `PessoaAdmin`, `EventoAdmin`, `InstituicaoAdmin` e `ParticipacaoAdmin` com busca, filtros por estado/frente/meta e paginação.
* [x] **Passo 2.4: Migrations & Testes Unitários de Models**
  * Gerar e aplicar migrações iniciais (`makemigrations`, `migrate`).
  * Implementar testes em `apps/participantes/tests/test_models.py` validando constraints, unicidade e relacionamentos `PROTECT`/`SET_NULL`.

---

### FASE 3: Engenharia do Pipeline de Importação (Core Services)
**Objetivo:** Implementar o motor de leitura, normalização, validação e persistência atômica, isolado de HTTP e Views.

* [x] **Passo 3.1: Constantes e Estruturas de Resultado (`result.py` e `constants.py`)**
  * Definir `EMPTY_VALUES`, nomes de colunas esperados (`REQUIRED_COLUMNS`), aliases de cabeçalho (`COD PARTICIPAÇÃO` / `CODIGO DA PARTICIPAÇÃO`).
  * Implementar dataclasses:
    * `ValidationError(field, code, message)`
    * `ProcessedRow(row_number, codigo, data, errors)`
    * `ImportPreview(total_rows, valid_rows, invalid_rows, rows, error_summary)`
    * `ImportResult(success, total_imported, errors)`
* [x] **Passo 3.2: Leitor Excel Puro (`reader.py`)**
  * Implementar `ExcelReader` usando `openpyxl` em modo `read_only=True` para eficiência de memória.
  * Validação de presença das colunas obrigatórias.
  * Descarte automático de linhas completamente vazias ao final da planilha (como as 88 linhas detectadas).
* [x] **Passo 3.3: Normalizadores Granulares (`normalizers.py`)**
  * `normalize_text(val)`: remoção de whitespaces duplicados e trim.
  * `normalize_cpf(val)`: extração estrita de dígitos.
  * `normalize_codigo(val)`: trim e uppercase canônico (`PART-XXXXX`).
  * `normalize_nome(val)`: preservação de capitalização original com remoção de espaços espúrios.
  * `normalize_date(val)`: suporte híbrido para int/float serial do Excel (ex.: `46261`), strings brasileiras (`DD/MM/YYYY`) e isoformat.
  * `normalize_instituicao(val)`: padronização em uppercase sanitizado, convertendo strings vazias/ausências (`-`, `Não informado`) em `None`.
  * `normalize_choices`: mapeamento resiliente para `genero`, `estado` (nome por extenso -> sigla UF), `frente_responsavel`, `meta_interna` e `tipo_participante`.
* [x] **Passo 3.4: Validadores de Negócio (`validators.py`)**
  * `validate_cpf(val)`: comprimento exato de 11 dígitos e algoritmo matemático oficial de validação dos dígitos verificadores (DV).
  * `validate_data_nascimento(val)`: plausibilidade temporal (`1900 <= data <= hoje`) e regras para nulos permitidos.
  * `validate_data_evento(val)`: data obrigatória e válida.
  * `validate_choices(val, choice_cls)`: verificação rigorosa contra os enums oficiais.
  * `validate_ano_consistencia(ano_informado, data_evento)`: verificação de divergência entre a coluna `ANO` e o ano real da data.
* [x] **Passo 3.5: Processador e Detector de Conflitos (`processor.py`)**
  * Orquestrar linha a linha: `Reader -> Normalizer -> Validator -> ProcessedRow`.
  * Validar unicidade dos códigos de participação dentro do próprio arquivo em lote.
  * Detectar duplicidades lógicas e conflitos de estado no lote de eventos.
* [x] **Passo 3.6: Persistência Transacional (`importer.py`)**
  * Executar a importação dentro de bloco `transaction.atomic()`.
  * Ordem estrita:
    1. Upsert em `Pessoa` (`update_or_create` por CPF).
    2. Get or create em `Instituicao` (para valores não nulos).
    3. Get or create em `Evento` pela chave lógica composta `(nome, data, frente, meta)`.
    4. Bulk create ou create individual de `Participacao` associando as chaves estrangeiras.
* [x] **Passo 3.7: Orquestrador Central (`service.py`)**
  * `ImportacaoService`: interface única expondo `processar_preview(file_source)` e `executar_importacao(rows)` com injeção de dependência opcional.
* [x] **Passo 3.8: Testes Automatizados da Importação**
  * Criar bateria de testes unitários:
    * `test_normalizers.py`: testes com valores da planilha real (incluindo datas seriais e anomalias).
    * `test_validators.py`: validação de CPFs válidos/inválidos e datas de nascimento.
    * `test_importer.py`: teste de ponta a ponta com rollback em caso de falha e integridade de relacionamentos.

---

### FASE 4: Interface Web de Importação (Upload, Preview e Persistência)
**Objetivo:** Prover uma experiência de usuário clara, permitindo envio de arquivo, visualização do diagnóstico antes da gravação e relatório de erros linha a linha.

* [x] **Passo 4.1: Formulário de Upload (`forms/importacao.py`)**
  * Form Django com validação de extensão `.xlsx`, limite configurado de 25 MB e inspeção de cabeçalho binário (ZIP / OOXML).
* [x] **Passo 4.2: Views Baseadas em Classe (`views/importacao.py`)**
  * `ImportacaoUploadView`: tela inicial com drag-and-drop para envio da planilha e acionamento da Fase 1.
  * `ImportacaoPreviewView`: processa a Fase 1 (sem gravar no banco), exibe KPIs, tabela paginada e filtros por status.
  * `ImportacaoConfirmarView`: aciona a Fase 2 (`service.executar_importacao`) sob transação atômica e emite feedback visual.
  * `ImportacaoResultadoView` e `ImportacaoCancelarView`: telas de conclusão e cancelamento com limpeza de sessão.
* [x] **Passo 4.3: Templates de Importação**
  * `apps/participantes/templates/participantes/importacao/upload.html`.
  * `apps/participantes/templates/participantes/importacao/preview.html`.
  * `apps/participantes/templates/participantes/importacao/resultado.html`.

---

### FASE 5: Engenharia do Dashboard Analítico
**Objetivo:** Transformar os dados transacionais consolidados em inteligência analítica com gráficos interativos e filtros dinâmicos.

* [x] **Passo 5.1: Service de Métricas e Agregações (`services/dashboard/`)**
  * `filters.py`: classe `DashboardFilter` para capturar e sanitizar parâmetros GET (`ano`, `estado`, `frente`, `meta`, `tipo_participante`, `instituicao`, `genero`, `comunidade`, `busca`).
  * `queries.py`: queries otimizadas via ORM (`aggregate`, `annotate`, `Count` com `distinct=True`, `TruncMonth`):
    * Total de participações.
    * Total de pessoas únicas (CPFs distintos).
    * Total de eventos realizados.
    * Média de participações por pessoa.
    * Distribuição por Gênero e Comunidade Tradicional.
    * Participações por Estado (ranking e percentuais).
    * Participações por Frente Responsável e Meta Interna.
    * Evolução cronológica mensal.
    * Top 5 eventos com maior participação.
    * Opções disponíveis para menus suspensos de filtro.
  * `service.py`: `DashboardService` unificando filtros, agregações e geração do payload JSON para o Chart.js.
* [x] **Passo 5.2: View e Endpoints do Dashboard (`views/dashboard.py`)**
  * `DashboardView`: renderiza o painel principal com cards de resumo, formulário de filtros e dados estruturados em JSON para o Chart.js na rota raiz `/`.
* [x] **Passo 5.3: Interface e Visualização com Chart.js**
  * Template `apps/participantes/templates/participantes/dashboard/index.html` com grid responsivo Bootstrap 5.3, cards e canvases.
  * Módulo Vanilla JS `static/js/dashboard.js` integrando com segurança via `json_script`:
    * Gráfico de linha/área: Evolução temporal mês a mês.
    * Gráfico de rosca/donut: Distribuição por Gênero.
    * Gráfico de barras verticais: Participantes por Estado (UF).
    * Gráfico de rosca: Comunidades Tradicionais.
    * Gráficos de barras horizontais: Metas Internas e Frentes Responsáveis.

---

### FASE 6: Refinamento, Auditoria & Documentação
**Objetivo:** Garantir a robustez de ponta a ponta, carga da planilha real e entrega de documentação operacional.

* [x] **Passo 6.1: Teste de Carga Real (`sipac_participacoes.xlsx`)**
  * Criado comando de gerenciamento CLI (`python manage.py importar_planilha sipac_participacoes.xlsx`) com suporte a `--dry-run`, `--clear` e `--report-invalid`.
  * Carga completa executada sobre a base real de 8.135 registros em apenas ~6.2 segundos:
    * Total de Pessoas físicas cadastradas (CPFs únicos): 3.764.
    * Total de Atividades/Eventos únicos consolidados: 382.
    * Total de Instituições normalizadas no catálogo: 311.
    * Total de Participações ativas persistidas: 7.306.
    * Integridade referencial auditada: 100% íntegra (0 órfãos).
    * Linhas barradas com relatório explicativo de inconsistência: 829.
* [x] **Passo 6.2: Auditoria de Performance do Dashboard**
  * Medição de tempo de resposta com a base real populada (7.306 participações):
    * Dashboard Geral (sem filtros): 70.62 ms (13 queries, zero N+1).
    * Filtro por Estado (AM): 25.47 ms.
    * Filtros Combinados (Ano 2026 + AM + CAMPO): 13.88 ms.
    * Busca Textual Ampla: 46.16 ms.
    * Resposta HTTP completa (View + Queries + Template + json_script): ~167 ms.
  * Auditoria de índices via `EXPLAIN QUERY PLAN`: 100% de uso de covering indexes (`evento_estado_data_idx`, `evento_data_idx`, índices de FKs e unique constraints).
* [x] **Passo 6.3: Documentação e Guia de Uso**
  * `README.md` completo: instruções de instalação, ativação do ambiente, migrações, criação de superusuário, execução do servidor, comandos de importação e arquitetura do código.

---

## 4. Estrutura de Arquivos Resultante do Projeto

```
/home/pedrohsn/workspace/sipac/
│
├── config/
│   ├── __init__.py
│   ├── asgi.py
│   ├── wsgi.py
│   ├── urls.py
│   └── settings/
│       ├── __init__.py
│       ├── base.py
│       ├── local.py
│       └── production.py
│
├── apps/
│   ├── __init__.py
│   └── participantes/
│       ├── __init__.py
│       ├── admin.py
│       ├── apps.py
│       ├── urls.py
│       ├── models/
│       │   ├── __init__.py
│       │   ├── base.py
│       │   ├── choices.py
│       │   ├── pessoa.py
│       │   ├── evento.py
│       │   ├── instituicao.py
│       │   └── participacao.py
│       ├── forms/
│       │   ├── __init__.py
│       │   └── importacao.py
│       ├── services/
│       │   ├── __init__.py
│       │   ├── importacao/
│       │   │   ├── __init__.py
│       │   │   ├── constants.py
│       │   │   ├── reader.py
│       │   │   ├── normalizers.py
│       │   │   ├── validators.py
│       │   │   ├── processor.py
│       │   │   ├── importer.py
│       │   │   ├── result.py
│       │   │   └── service.py
│       │   └── dashboard/
│       │       ├── __init__.py
│       │       ├── filters.py
│       │       ├── queries.py
│       │       └── service.py
│       ├── views/
│       │   ├── __init__.py
│       │   ├── dashboard.py
│       │   └── importacao.py
│       ├── management/
│       │   ├── __init__.py
│       │   └── commands/
│       │       ├── __init__.py
│       │       └── importar_planilha.py
│       ├── tests/
│       │   ├── __init__.py
│       │   ├── test_models.py
│       │   ├── test_normalizers.py
│       │   ├── test_validators.py
│       │   └── test_importer.py
│       └── templates/
│           └── participantes/
│               ├── dashboard/
│               │   └── index.html
│               └── importacao/
│                   ├── upload.html
│                   ├── preview.html
│                   └── resultado.html
│
├── templates/
│   └── base.html
├── static/
│   ├── css/
│   │   └── style.css
│   └── js/
│       └── dashboard.js
├── media/
├── sipac_participacoes.xlsx
├── .env.example
├── .gitignore
├── manage.py
├── requirements.txt
└── README.md
```

---

## 5. Plano de Verificação

### Testes Automatizados
* Execução contínua da suíte de testes do Django:
  ```bash
  python manage.py test apps.participantes.tests
  ```
* Testes isolados de normalização e validação sem tocar no banco de dados para garantir performance imediata.

### Verificação Manual & Carga Real
* Execução do comando de importação contra `sipac_participacoes.xlsx`.
* Conferência dos totais:
  * Total de participações importadas vs. rejeitadas.
  * Validação das 4.398 pessoas e dos ~187 eventos consolidados.
* Acesso ao Django Admin (`/admin/`) para auditoria visual de integridade referencial.
* Acesso ao Dashboard (`/`) com teste de filtros combinados por UF, ano e meta interna.
