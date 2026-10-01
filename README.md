# SIPAC — Sistema de Informações de Participação e Capacitação

[![Python](https://img.shields.io/badge/Python-3.12-blue.svg)](https://www.python.org/)
[![Django](https://img.shields.io/badge/Django-5.2-green.svg)](https://www.djangoproject.com/)
[![Tests](https://img.shields.io/badge/Tests-86%20Passing-brightgreen.svg)]()
[![License](https://img.shields.io/badge/License-Proprietary-red.svg)]()

> **Sistema Web Analítico e de Auditoria para Projetos de Capacitação, Formação e Extensão Rural (ATER).**

---

## 1. Visão Geral e Propósito do Sistema

O **SIPAC** foi desenvolvido para transformar o controle operacional de capacitações e eventos rurais — tradicionalmente gerido em planilhas dispersas — em um ambiente relacional auditável, de alta performance e com inteligência de dados.

O sistema opera sobre dois pilares fundamentais:
1. **Pipeline de Importação e Saneamento em 2 Fases:** Motor robusto de leitura streaming, normalização semântica, pré-validação diagnóstica e persistência transacional atômica sob bloco `transaction.atomic()`.
2. **Dashboard de Inteligência Analítica:** Painel executivo interativo com gráficos HTML5 Canvas (Chart.js 4.4), filtros dinâmicos multifacetados e relatórios consolidados em tempo real.

---

## 2. Stack Tecnológico

| Componente | Tecnologia | Versão Adotada | Justificativa / Papel |
|---|---|---|---|
| **Linguagem** | Python | `3.12.x` | Desempenho, tipagem moderna (`str \| None`), `match-case` e suporte de longo prazo. |
| **Framework Web** | Django | `>=5.1, <6.0` (LTS) | Estabilidade, ORM maduro, CBV expressivas e sistema de autenticação/admin nativo. |
| **Banco Local** | SQLite | `3.x` | Zero configuração para desenvolvimento local ágil e execução ultra-rápida de testes. |
| **Banco Produção** | PostgreSQL | `>=15.0` | Integridade referencial, concorrência, índices compostos e robustez analítica. |
| **Driver PostgreSQL** | `psycopg` (v3) | `[binary] >= 3.2.0` | Driver moderno oficial recomendado pelo Django 5+. |
| **Parser de Planilhas** | `openpyxl` | `>= 3.1.2` | Leitura streaming/read-only de arquivos `.xlsx` com acesso direto às células. |
| **Variáveis de Ambiente**| `python-dotenv` | `>= 1.0.1` | Gestão segura de segredos e alternância transparente de ambientes (`.env`). |
| **UI Framework** | Bootstrap | `5.3.x` (CDN) | Responsividade mobile-first, grid moderno sem necessidade de build tools (Node/npm). |
| **Visualização** | Chart.js | `4.4.x` (CDN) | Renderização de gráficos interativos via JSON desacoplado (`json_script`). |

---

## 3. Arquitetura de Camadas: CBV + Services + Models

O projeto segue rigorosamente o princípio arquitetural **Thin Views, Fat Services e Expressive Models**, garantindo isolamento total entre a camada web HTTP e as regras de negócio:

```
  [ REQUISIÇÃO HTTP ]
          │
          ▼
┌──────────────────┐
│   Django CBV     │  • Autenticação e permissões HTTP
│  (views/*.py)    │  • Validação do formulário (extensão/tamanho do arquivo)
└─────────┬────────┘  • Invoca o Service apropriado e retorna render/redirect
          │
          ▼
┌──────────────────┐
│  Service Layer   │  • Orquestra regras de negócio e fluxo operacional
│ (services/*.py)  │  • 100% isolado de HTTP (sem `request`, sem `session`)
└─────────┬────────┘  • Retorna Dataclasses/DTOs tipadas
          │
          ├──────────────────────────┐
          ▼                          ▼
┌───────────────────┐      ┌───────────────────┐
│ ImportacaoService │      │ DashboardService  │
│ • Reader (openpyxl)      │ • DashboardFilter │
│ • Normalizer (Puro)      │ • DashboardQueries│
│ • Validator (Regras)     │   (Agregações ORM)│
│ • Importer (Atomic)      │                   │
└─────────┬─────────┘      └─────────┬─────────┘
          │                          │
          └─────────────┬────────────┘
                        ▼
            ┌───────────────────────┐
            │    Django ORM / DB    │
            │ (Pessoa, Evento,      │
            │  Instituicao,         │
            │  Participacao)        │
            └───────────────────────┘
```

### Regras de Ouro da Arquitetura
1. **Normalizadores NUNCA rejeitam uma linha:** Apenas padronizam tipos (ex.: remover pontuação de CPF, converter números seriais do Excel como `46261` para `date`, converter nomes por extenso de Estados para siglas UF). Valores corrompidos ou ilegíveis retornam `UnparseableDate` ou `None`.
2. **Validadores NUNCA alteram dados:** Apenas emitem julgamentos lógicos sobre dados já normalizados (ex.: algoritmo de Dígitos Verificadores do CPF, limites cronológicos de datas, consistência anual).
3. **Persistência é 100% Atômica:** A gravação só ocorre na Fase 2 sob bloco `transaction.atomic()`. Se uma linha falhar no banco, ocorre rollback integral automático.
4. **Isolamento de Scripts:** Nenhuma tag `<script>` interpola variáveis de template diretamente. Os dados analíticos são serializados com o filtro seguro `json_script` e consumidos por `dashboard.js`.

---

## 4. Modelagem Relacional e Regras de Domínio

```
┌─────────────────────────────────┐
│             PESSOA              │
├─────────────────────────────────┤
│ id (PK)                         │
│ cpf: CharField(11) [UNIQUE]     │
│ nome: CharField(255)            │
│ data_nascimento: DateField NULL │
│ genero: CharField(2) [M, F, NI] │
│ comunidade_tradicional: Char(20)│
│ created_at / updated_at         │
└────────────────┬────────────────┘
                 │
                 │ 1:N (on_delete=PROTECT)
                 ▼
┌─────────────────────────────────┐           ┌─────────────────────────────────┐
│          PARTICIPAÇÃO           │           │             EVENTO              │
├─────────────────────────────────┤           ├─────────────────────────────────┤
│ id (PK)                         │           │ id (PK)                         │
│ codigo: CharField(50) [UNIQUE]  │           │ nome: CharField(255)            │
│ pessoa_id: FK(Pessoa)           │◄────N:1───│ data: DateField                 │
│ evento_id: FK(Evento)           │           │ frente_responsavel: Char(30)    │
│ tipo_participante: Char(30)     │           │ estado: Char(2) [UF]            │
│ instituicao_id: FK(Instituicao) │           │ meta_interna: Char(80)          │
│ created_at / updated_at         │           │ created_at / updated_at         │
└────────────────┬────────────────┘           ├─────────────────────────────────┤
                 │                            │ UNIQUE(nome, data, frente, meta)│
                 │ N:1 (SET_NULL)             │ INDEX(data), INDEX(estado, data)│
                 ▼                            └─────────────────────────────────┘
┌─────────────────────────────────┐
│           INSTITUIÇÃO           │
├─────────────────────────────────┤
│ id (PK)                         │
│ nome: CharField(255) [UNIQUE]   │
│ created_at / updated_at         │
└─────────────────────────────────┘
```

- **Pessoa:** O CPF (11 dígitos numéricos) é a chave natural única. Atualizações cadastrais em importações sucessivas executam `update_or_create`. Protegida contra exclusão acidental via `PROTECT`.
- **Evento:** A unicidade lógica é garantida pela combinação `(nome, data, frente_responsavel, meta_interna)`. Possui índices em `data` e composto em `(estado, data)` para otimização de consultas analíticas.
- **Instituição:** Catálogo canônico sanitizado em maiúsculas (ex.: `"Iabs"`, `" iabs "` convergem para `"IABS"`). Ausências semânticas tornam-se `NULL`.
- **Participação:** Registra o fato relacional (`codigo` único de rastreio da planilha, ex.: `PART-00001`). `tipo_participante` pertence ao vínculo da participação, permitindo que uma mesma pessoa participe como produtor em um evento e como palestrante em outro.

---

## 5. Instalação e Configuração do Ambiente

### 5.1 Pré-requisitos
- Python 3.12+ instalado (`python3 --version`).
- Git instalado.

### 5.2 Passo a Passo de Instalação

1. **Clonar o Repositório:**
   ```bash
   git clone https://github.com/seu-usuario/sipac.git
   cd sipac
   ```

2. **Criar e Ativar o Ambiente Virtual:**
   ```bash
   python3 -m venv .venv
   source .venv/bin/activate
   ```

3. **Instalar Dependências:**
   ```bash
   pip install --upgrade pip
   pip install -r requirements.txt
   ```

4. **Configurar as Variáveis de Ambiente:**
   Crie o arquivo `.env` a partir do modelo fornecido:
   ```bash
   cp .env.example .env
   ```

   Conteúdo padrão do `.env`:
   ```env
   # Configurações do Django
   SECRET_KEY="sua-chave-secreta-segura-de-desenvolvimento"
   DEBUG=True
   ALLOWED_HOSTS="localhost,127.0.0.1,testserver"

   # Banco de Dados (SQLite por padrão para desenvolvimento local ágil)
   # DATABASE_URL="sqlite:///db.sqlite3"

   # Para usar PostgreSQL em homologação/produção:
   # DATABASE_URL="postgres://sipac_user:sipac_password@localhost:5432/sipac_db"
   ```

5. **Aplicar as Migrações Iniciais:**
   ```bash
   python manage.py migrate
   ```

6. **Criar Superusuário Administrativo:**
   ```bash
   python manage.py createsuperuser
   ```

7. **Executar o Servidor de Desenvolvimento:**
   ```bash
   python manage.py runserver
   ```
   Acesse a aplicação no navegador em: [http://localhost:8000/](http://localhost:8000/).

---

## 6. Pipeline de Importação: Guia de Uso

O SIPAC oferece duas formas complementares para importação de planilhas:

### 6.1 Modo Linha de Comando (CLI Management Command)

O comando de gerenciamento oficial permite cargas automatizadas, auditorias em batch e testes de conformidade:

```bash
# Execução padrão (importa a planilha na raiz sipac_participacoes.xlsx)
python manage.py importar_planilha sipac_participacoes.xlsx

# Modo Dry-Run (apenas diagnostica a planilha sem gravar nada no banco)
python manage.py importar_planilha sipac_participacoes.xlsx --dry-run

# Modo Limpeza Prévia (limpa registros anteriores antes da nova carga)
python manage.py importar_planilha sipac_participacoes.xlsx --clear

# Exibição do relatório linha a linha de inconsistências barradas
python manage.py importar_planilha sipac_participacoes.xlsx --report-invalid
```

#### Métricas Auditadas na Planilha Real (`sipac_participacoes.xlsx`):
```text
======================================================================
SIPAC — Pipeline de Importação e Saneamento de Participações
======================================================================
Arquivo de origem: sipac_participacoes.xlsx (1.20 MB)
Linhas lidas: 8.135 | Linhas válidas: 7.306 | Inconsistências: 829
Tempo Fase 1 (Diagnóstico): 1.41 segundos
Tempo Fase 2 (Gravação Atômica): 4.79 segundos

AUDITORIA FINAL DO BANCO DE DADOS:
• Pessoas físicas cadastradas (CPFs únicos): 3.764
• Atividades/Eventos únicos consolidados:   382
• Instituições normalizadas no catálogo:    311
• Participações ativas vinculadas:          7.306
• Integridade referencial: 100% íntegra (0 órfãos).
======================================================================
```

### 6.2 Modo Interface Web

1. **Upload (`/importacao/`):**
   - Suporte a formulário intuitivo com área de arraste (*drag-and-drop*).
   - Validações de segurança: tamanho máximo de 25 MB, extensão estrita `.xlsx` e checagem de integridade binária ZIP/OOXML.
2. **Diagnóstico Pré-Importação (`/importacao/preview/`):**
   - Cards com KPIs de qualidade: Total de Registros Lidos, Aptos para Gravação e Inconsistências.
   - Sumário ranqueado das principais causas de erro (ex.: Dígito verificador de CPF inválido, data da atividade não informada, conflitos de UF em eventos homônimos).
   - Tabela paginada (50 linhas por página) com filtro por abas (*Todos*, *Apenas Válidos*, *Apenas Inconsistentes*) e badges com a descrição exata de cada falha.
   - Botões de decisão: **Confirmar Gravação** dos registros válidos ou **Cancelar/Novo Arquivo**.
3. **Persistência e Sucesso (`/importacao/resultado/`):**
   - Execução sob transação atômica completa (Fase 2).
   - Feedback quantitativo com botões de navegação para o Dashboard ou Admin.

---

## 7. Dashboard Analítico e Indicadores

O Dashboard é renderizado na rota raiz `/` e disponibiliza visão consolidada das participações:

### 7.1 Indicadores Macro (KPIs)
- **Total de Participações:** Volume global de presenças registradas.
- **Pessoas Únicas (CPFs):** Total de cidadãos distintos beneficiados pelas ações.
- **Eventos Realizados:** Quantidade de atividades catalogadas.
- **Média por Pessoa:** Métrica de engajamento contínuo (participações / pessoas únicas).

### 7.2 Gráficos Interativos (Chart.js 4.4)
- **Evolução Cronológica:** Gráfico de linha e área sombreada com evolução mês a mês das atividades.
- **Distribuição por Gênero:** Gráfico de rosca (*doughnut*) com proporções e percentuais de Masculino, Feminino e Não Informado.
- **Participações por Estado (UF):** Gráfico de barras verticais com a distribuição geográfica das participações.
- **Comunidades Tradicionais:** Gráfico de rosca polar com a representação de Ribeirinhos, Indígenas, Quilombolas, Assentados e Outros.
- **Metas Internas:** Gráfico de barras horizontais detalhando a adesão a cada meta temática do projeto.
- **Frentes de Atuação:** Gráfico de barras horizontais por frente responsável (CAMPO, ATER, CAPACITAÇÃO, CME).

### 7.3 Filtros Dinâmicos Multifacetados
Permite refinar todos os KPIs, gráficos e tabelas simultaneamente através de:
- Ano da atividade;
- Estado (UF);
- Frente responsável;
- Meta interna;
- Público / Tipo de participante;
- Busca textual geral (pesquisa instantânea por Nome, CPF com ou sem pontuação e nome do Evento).

---

## 8. Auditoria de Desempenho

Resultados medidos diretamente sobre a base de dados real com **7.306 registros** persistidos:

| Cenário Analítico | Registros Analisados | Queries SQL | Tempo DB | Tempo Total (Python+DB) |
|---|---|---|---|---|
| **Dashboard Geral (Sem Filtros)** | 7.306 participações | **13 queries** | 52.00 ms | **70.62 ms** |
| **Filtro por Estado (AM)** | 3.066 participações | **13 queries** | 15.00 ms | **25.47 ms** |
| **Filtros Combinados (2026 + AM + CAMPO)** | 123 participações | **13 queries** | 2.00 ms | **13.88 ms** |
| **Busca Textual ("Silva")** | 1.436 participações | **13 queries** | 38.00 ms | **46.16 ms** |
| **Ciclo HTTP Completo (`GET /`)** | Renderização HTML (32 KB) | **13 queries** | 52.00 ms | **167.19 ms** |

> **Otimização ORM:** O volume de queries SQL permanece estritamente fixo em **13 queries por carregamento** (zero problemas de $N+1$). Todas as consultas utilizam *covering indexes* (`evento_estado_data_idx`, `evento_data_idx` e índices B-Tree de chaves estrangeiras).

---

## 9. Suíte de Testes Automatizados

O sistema conta com **86 testes automatizados** cobrindo todas as camadas da aplicação:

```bash
# Executar a suíte completa de testes
python manage.py test apps.participantes.tests

# Executar com detalhamento de testes (-v 2)
python manage.py test apps.participantes.tests -v 2
```

### Distribuição dos Testes
- [`test_models.py`](apps/participantes/tests/test_models.py) (12 testes): Unicidade simples e composta, representação textual e integridade referencial `PROTECT` e `SET_NULL`.
- [`test_normalizers.py`](apps/participantes/tests/test_normalizers.py) (16 testes): Sanitização pura, datas seriais do Excel (`46261`), formatos ISO/BR, remoção de acentos e marcador `UnparseableDate`.
- [`test_validators.py`](apps/participantes/tests/test_validators.py) (20 testes): Algoritmo de Dígitos Verificadores do CPF, bloqueio de 11 dígitos repetidos, datas limite e consistência anual.
- [`test_importer.py`](apps/participantes/tests/test_importer.py) (5 testes): Persistência atômica sob `transaction.atomic()`, upsert de Pessoa por CPF, deduplicação de Evento e garantia de rollback.
- [`test_forms.py`](apps/participantes/tests/test_forms.py) (8 testes): Validação de extensão `.xlsx`, detecção de arquivos vazios, limite de tamanho (25 MB) e assinatura mágica de cabeçalho ZIP.
- [`test_views.py`](apps/participantes/tests/test_views.py) (10 testes): Ciclo web completo (upload, preview, filtros, paginação, confirmação atômica, cancelamento e dashboard).
- [`test_dashboard.py`](apps/participantes/tests/test_dashboard.py) (12 testes): Filtros HTTP sanitizados, cálculo matemático de KPIs, agrupamentos categóricos e séries temporais.
- [`test_commands.py`](apps/participantes/tests/test_commands.py) (3 testes): Execução do comando CLI `importar_planilha` com `--dry-run`, `--clear` e auditoria de métricas.

---

## 10. Estrutura Física do Projeto

```text
sipac/
│
├── config/                          # Configurações do Projeto Django
│   ├── __init__.py
│   ├── asgi.py                      # Ponto de entrada ASGI
│   ├── wsgi.py                      # Ponto de entrada WSGI
│   ├── urls.py                      # Roteamento raiz do projeto
│   └── settings/                    # Settings modularizados por ambiente
│       ├── __init__.py
│       ├── base.py                  # Definições comuns (apps, i18n, middleware, tz)
│       ├── local.py                 # Ambiente local de desenvolvimento (SQLite)
│       └── production.py            # Ambiente de produção (PostgreSQL)
│
├── apps/                            # Diretório raiz para aplicações Django
│   ├── __init__.py
│   └── participantes/               # App central de participantes e eventos
│       ├── __init__.py
│       ├── apps.py                  # ParticipantesConfig
│       ├── admin.py                 # Customização do Django Admin
│       ├── urls.py                  # Rotas do app (/ e /importacao/...)
│       │
│       ├── models/                  # Modelagem relacional particionada
│       │   ├── __init__.py          # Exporta: Pessoa, Evento, Instituicao, Participacao
│       │   ├── base.py              # TimeStampedModel abstrato
│       │   ├── choices.py           # TextChoices oficiais (Genero, Estado, Frente, etc.)
│       │   ├── pessoa.py            # Cadastro único da Pessoa física
│       │   ├── evento.py            # Cadastro único da Atividade/Evento
│       │   ├── instituicao.py       # Catálogo sanitizado de instituições
│       │   └── participacao.py      # Fato: Relação Pessoa <-> Evento
│       │
│       ├── forms/                   # Formulários de entrada HTTP
│       │   ├── __init__.py
│       │   └── importacao.py        # ImportacaoUploadForm (.xlsx e validação)
│       │
│       ├── services/                # Camada Core de Regras de Negócio e Serviços
│       │   ├── __init__.py
│       │   ├── importacao/          # Pipeline de Importação
│       │   │   ├── __init__.py
│       │   │   ├── constants.py     # Colunas oficiais, mappings de enums, listas de nulos
│       │   │   ├── result.py        # Dataclasses de resultado (ValidationError, ProcessedRow)
│       │   │   ├── reader.py        # Leitura bruta do Excel (openpyxl streaming read-only)
│       │   │   ├── normalizers.py   # Funções puras de normalização semântica
│       │   │   ├── validators.py    # Regras matemáticas de CPF e consistência cronológica
│       │   │   ├── processor.py     # Orquestrador de validação em lote e conflitos
│       │   │   ├── importer.py      # Persistência atômica no ORM com rollback
│       │   │   └── service.py       # Facade de alto nível (ImportacaoService)
│       │   │
│       │   └── dashboard/           # Serviços Analíticos do Dashboard
│       │       ├── __init__.py
│       │       ├── filters.py       # DTO e sanitização dos filtros GET
│       │       ├── queries.py       # Agregações analíticas e otimização ORM
│       │       └── service.py       # Facade do Dashboard (DashboardService)
│       │
│       ├── views/                   # Controladores Web (Django CBV finas)
│       │   ├── __init__.py
│       │   ├── dashboard.py         # DashboardView (TemplateView)
│       │   └── importacao.py        # UploadView, PreviewView, ConfirmarView, etc.
│       │
│       ├── management/              # Comandos de linha de comando (CLI)
│       │   ├── __init__.py
│       │   └── commands/
│       │       ├── __init__.py
│       │       └── importar_planilha.py # CLI de importação com dry-run e auditoria
│       │
│       ├── tests/                   # Suíte com 86 testes automatizados
│       │   ├── __init__.py
│       │   ├── test_models.py
│       │   ├── test_normalizers.py
│       │   ├── test_validators.py
│       │   ├── test_importer.py
│       │   ├── test_forms.py
│       │   ├── test_views.py
│       │   ├── test_dashboard.py
│       │   └── test_commands.py
│       │
│       └── templates/participantes/ # Templates específicos do app
│           ├── dashboard/
│           │   └── index.html       # Painel analítico com filtros e Chart.js
│           └── importacao/
│               ├── upload.html      # Formulário de upload com drag-and-drop
│               ├── preview.html     # Diagnóstico pré-importação e inconsistências
│               └── resultado.html   # Resumo da importação concluída
│
├── templates/                       # Templates compartilhados
│   └── base.html                    # Layout mestre (Navbar, Bootstrap CDN, Footer)
│
├── static/                          # Arquivos estáticos
│   ├── css/
│   │   └── style.css                # Estilização complementar e temas
│   └── js/
│       └── dashboard.js             # Módulo Vanilla JS para renderização do Chart.js
│
├── media/                           # Diretório transitório de uploads
├── sipac_participacoes.xlsx         # Planilha de matriz original
├── .env.example                     # Template de variáveis de ambiente
├── .gitignore                       # Filtro de versionamento Git
├── manage.py                        # Utilitário CLI do Django
├── requirements.txt                 # Dependências travadas do projeto
└── README.md                        # Documentação executiva e guia operacional
```

---

## 11. Licença

Este software é de propriedade privada e confidencial, desenvolvido sob medida para projetos de gestão de dados de participação e capacitação rural (ATER).
