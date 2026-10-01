# SIPAC — Sistema de Informações de Participação e Capacitação
# Memória Técnica e Arquitetural (Blueprint do Projeto)

> **Documento de Referência Permanente**  
> Este documento estabelece formalmente todas as convenções, regras de negócio, padrões de código, arquitetura de camadas (CBV + Services), modelagem relacional e diretrizes de interface do SIPAC.

---

## 1. Visão Geral e Propósito do Sistema

O **SIPAC** é um sistema web desenvolvido em Django com foco analítico e de auditoria para projetos de capacitação, formação e extensão rural (ATER). 

O sistema possui dois pilares operacionais fundamentais:
1. **Pipeline de Importação e Saneamento:** Leitura de planilhas operacionais (`.xlsx`), normalização semântica, pré-validação diagnóstica e persistência transacional de dados cadastrais.
2. **Dashboard de Inteligência:** Consolidação e exibição gráfica de indicadores gerenciais (participações por estado, gênero, comunidade tradicional, frente de atuação e metas internas).

---

## 2. Stack Tecnológico e Versões

| Componente | Tecnologia | Versão Adotada | Justificativa / Papel |
|---|---|---|---|
| **Linguagem** | Python | `3.12.x` | Desempenho, type hinting moderno (`str \| None`), match-case e suporte a longo prazo. |
| **Framework Web** | Django | `>=5.1, <6.0` (LTS) | Estabilidade, ORM maduro, CBV expressivas e sistema de autenticação/admin nativo. |
| **Banco de Dados Local** | SQLite | `3.x` | Zero configuração para desenvolvimento ágil e execução rápida da suíte de testes. |
| **Banco de Dados Produção** | PostgreSQL | `>=15.0` | Integridade referencial, concorrência, índices compostos e robustez analítica. |
| **Driver PostgreSQL** | `psycopg` (v3) | `[binary] >= 3.2.0` | Driver moderno oficial recomendado pelo Django 5+. |
| **Parser de Planilhas** | `openpyxl` | `>= 3.1.2` | Leitura streaming/read-only de arquivos `.xlsx` com acesso direto às células. |
| **Configurações de Ambiente** | `python-dotenv` | `>= 1.0.1` | Gestão de segredos e alternância transparente de ambientes (`.env`). |
| **UI Framework** | Bootstrap | `5.3.x` (via CDN) | Responsividade mobile-first, grid moderno e sem dependência de build tools (Node/npm). |
| **Visualização de Dados** | Chart.js | `4.4.x` (via CDN) | Renderização de gráficos interativos HTML5 Canvas via JSON desacoplado. |

---

## 3. Topologia e Estrutura Física do Projeto

O projeto adota a separação entre configurações globais (`config/`), o núcleo de domínio modular (`apps/participantes/`), camadas estáticas e de templates:

```
sipac/  (Raiz do Projeto)
│
├── config/                          # Configurações do Projeto Django
│   ├── __init__.py
│   ├── asgi.py                      # Ponto de entrada ASGI
│   ├── wsgi.py                      # Ponto de entrada WSGI
│   ├── urls.py                      # Roteamento raiz do projeto
│   └── settings/                    # Settings modularizados por ambiente
│       ├── __init__.py
│       ├── base.py                  # Definições comuns (apps, i18n, middleware, tz)
│       ├── local.py                 # Ambiente local de desenvolvimento (SQLite, DEBUG=True)
│       └── production.py            # Ambiente de produção (PostgreSQL, WhiteNoise, segurança)
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
│       │   └── importacao.py        # ImportacaoUploadForm (.xlsx e validação de arquivo)
│       │
│       ├── services/                # Regras de Negócio e Serviços (Camada Core)
│       │   ├── __init__.py
│       │   ├── importacao/          # Pipeline de Importação
│       │   │   ├── __init__.py
│       │   │   ├── constants.py     # Colunas oficiais, mappings de enums, listas de nulos
│       │   │   ├── result.py        # Dataclasses de resultado (ValidationError, ProcessedRow, etc.)
│       │   │   ├── reader.py        # Leitura bruta do Excel (openpyxl read-only)
│       │   │   ├── normalizers.py   # Funções puras de transformação de dados
│       │   │   ├── validators.py    # Regras matemáticas e validações de consistência
│       │   │   ├── processor.py     # Orquestrador de linha a linha
│       │   │   ├── importer.py      # Persistência transacional atômica no ORM
│       │   │   └── service.py       # Facade de alto nível (ImportacaoService)
│       │   │
│       │   └── dashboard/           # Serviços Analíticos do Dashboard
│       │       ├── __init__.py
│       │       ├── filters.py       # DTO e sanitização dos filtros GET
│       │       ├── queries.py       # Agregações analíticas e otimização ORM
│       │       └── service.py       # DashboardService
│       │
│       ├── views/                   # Controladores Web (Django CBV finas)
│       │   ├── __init__.py
│       │   ├── dashboard.py         # DashboardView (TemplateView)
│       │   └── importacao.py        # UploadView, PreviewView, ConfirmarView
│       │
│       ├── management/              # Comandos de linha de comando (CLI)
│       │   ├── __init__.py
│       │   └── commands/
│       │       ├── __init__.py
│       │       └── importar_planilha.py # CLI para importação de planilhas locais
│       │
│       ├── tests/                   # Suíte de testes automatizados
│       │   ├── __init__.py
│       │   ├── test_models.py       # Integridade, constraints e str dos models
│       │   ├── test_normalizers.py  # Teste unitário de funções puras
│       │   ├── test_validators.py   # Teste das regras de CPF, datas e escolhas
│       │   ├── test_importer.py     # Teste integrado de transação e banco
│       │   └── test_dashboard.py    # Teste de métricas e filtros
│       │
│       └── templates/participantes/ # Templates específicos do app
│           ├── dashboard/
│           │   └── index.html       # Painel analítico com filtros e gráficos Chart.js
│           └── importacao/
│               ├── upload.html      # Formulário de upload da planilha
│               ├── preview.html     # Diagnóstico pré-importação e relatório de inconsistências
│               └── resultado.html   # Resumo da importação concluída com sucesso
│
├── templates/                       # Templates compartilhados
│   └── base.html                    # Layout mestre (Navbar, CDN Bootstrap, Footer)
│
├── static/                          # Arquivos estáticos
│   ├── css/
│   │   └── style.css                # Estilização complementar e temas
│   └── js/
│       └── dashboard.js             # Módulo Vanilla JS para renderização do Chart.js
│
├── media/                           # Uploads transitórios de arquivos
├── sipac_participacoes.xlsx         # Planilha de matriz original
├── .env                             # Variáveis de ambiente locais (não versionar)
├── .env.example                     # Template de variáveis de ambiente
├── .gitignore                       # Filtro de versionamento Git
├── manage.py                        # Utilitário CLI do Django
├── requirements.txt                 # Dependências travadas do projeto
└── README.md                        # Instruções executivas do projeto
```

---

## 4. Regras de Negócio e Modelagem de Dados

### 4.1 Entidades e Relacionamentos

```
┌─────────────────────────────────┐
│             PESSOA              │
├─────────────────────────────────┤
│ id (PK)                         │
│ cpf: CharField(11) [UNIQUE]     │
│ nome: CharField(255)            │
│ data_nascimento: DateField NULL │
│ genero: CharField(2)            │
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
│ tipo_participante: Char(30)     │           │ estado: Char(2)                 │
│ instituicao_id: FK(Instituicao) │           │ meta_interna: Char(80)          │
│ created_at / updated_at         │           │ created_at / updated_at         │
└────────────────┬────────────────┘           ├─────────────────────────────────┤
                 │                            │ UNIQUE(nome, data, frente, meta)│
                 │ N:1 (SET_NULL)             └─────────────────────────────────┘
                 ▼
┌─────────────────────────────────┐
│           INSTITUIÇÃO           │
├─────────────────────────────────┤
│ id (PK)                         │
│ nome: CharField(255) [UNIQUE]   │
│ created_at / updated_at         │
└─────────────────────────────────┘
```

### 4.2 Regras de Domínio por Entidade

#### Pessoa
1. **Chave Natural:** O `cpf` (11 dígitos, sem pontuação) é o identificador único e universal do cidadão. Não se deve criar restrição composta com `nome`. Se uma pessoa mudar o nome ou grafia, o CPF permanece o elo canônico.
2. **Atualização Cadastral:** Em importações sucessivas, se o CPF já existir, o sistema executa um `update_or_create`, atualizando dados complementares com a versão mais recente.
3. **Data de Nascimento:** É um dado opcional (`null=True, blank=True`). Valores indicando ausência (`"NÃO INFORMADA"`, `"NÃO INFORMADO"`, `"-"`, `"(ilegível)"`) tornam-se obrigatoriamente `None`. Datas de nascimento anteriores a `01/01/1900` ou posteriores ao dia corrente são barradas como inválidas.
4. **Proteção de Exclusão:** `Pessoa` possui `on_delete=models.PROTECT` em `Participacao`. Nenhuma pessoa com histórico de participação pode ser apagada acidentalmente do sistema.

#### Evento
1. **Identidade Composta:** A unicidade do evento é definida pela combinação lógica:  
   `nome` + `data` + `frente_responsavel` + `meta_interna`.
2. **Obrigatoriedade da Data:** `Evento.data` é estritamente obrigatória (`null=False`). Registros na planilha com `DATA DA ATIVIDADE = 'NÃO INFORMADO'` (como as 141 linhas existentes) **não entram no banco** e são apontadas como erro impeditivo no relatório.
3. **Integridade de Localidade (Estado):** Se duas linhas compartilharem a mesma tupla `(nome, data, frente, meta)` com estados divergentes (ex.: Amazonas e Rondônia), o sistema sinaliza **erro de consistência cadastral**, impedindo sobrescritas silenciosas.

#### Instituição
1. **Catálogo Canônico:** As instituições são cadastradas de forma sanitizada (espaços únicos, trim, uppercase padronizado). Exemplos como `"IABS"`, `"Iabs"`, `" iabs "` convergem para um único registro `IABS`.
2. **Ausência Semântica:** A ausência de instituição é gravada como `instituicao = NULL`. É vedado criar registros fictícios no banco com nome `"Não informado"` ou `"-"`.

#### Participação
1. **Identificador de Origem:** O `codigo` (ex.: `PART-00001`) é único e rastreia o registro de origem da planilha. O `id` do banco permanece como chave primária interna (PK auto-increment).
2. **Papel Relacional:** O `tipo_participante` (ex.: Produtor Rural, Técnico de ATER) pertence à `Participacao` e não à `Pessoa`, permitindo que um mesmo indivíduo participe como produtor em um evento e como técnico ou palestrante em outro.

---

## 5. Arquitetura de Camadas: Django CBV + Services

O projeto adota uma separação rigorosa de responsabilidades baseada no princípio de **Thin Views, Fat Services e Expressive Models**.

```
  [ REQUISIÇÃO HTTP ]
          │
          ▼
┌──────────────────┐
│   Django CBV     │  Responsabilidade exclusiva:
│  (views/*.py)    │  • Autenticação e permissões HTTP
└─────────┬────────┘  • Validação do formulário (extensão/tamanho do arquivo)
          │           • Invocar o Service apropriado
          │           • Converter exceções/retornos em contexto para o template ou redirecionamento
          ▼
┌──────────────────┐
│  Service Layer   │  Responsabilidade exclusiva:
│ (services/*.py)  │  • Orquestrar regras de negócio e fluxo operacional
└─────────┬────────┘  • Isolar a lógica de qualquer contexto HTTP (sem `request`, sem `session`)
          │           • Retornar DTOs / Dataclasses tipadas
          ▼
┌──────────────────┐
│   Sub-serviços   │  Componentes especializados:
│  Especializados  │  • Reader: I/O de arquivo para estruturas brutas
└─────────┬────────┘  • Normalizer: funções puras de saneamento
          │           • Validator: checagem de conformidade matemática e lógica
          ▼           • Importer: persistência sob `transaction.atomic()`
┌──────────────────┐
│  Django ORM / DB │  Models expressivos, constraints de unicidade e integridade
└──────────────────┘
```

### 5.1 O que a View PODE e NÃO PODE fazer

* **A View PODE:**
  * Validar formulários Django (`form.is_valid()`).
  * Chamar métodos públicos do Service (`service.gerar_preview()`, `service.executar_importacao()`).
  * Definir mensagens de feedback ao usuário (`django.contrib.messages`).
  * Retornar `render()` com template e contexto ou `HttpResponseRedirect`.
* **A View NÃO PODE:**
  * Instanciar `openpyxl` ou ler planilhas diretamente.
  * Executar lógica de limpeza de strings ou regex de CPF.
  * Executar queries com múltiplos `.filter()`, `.annotate()` ou regras de agregação analítica.
  * Executar transações de banco de dados diretamente (`transaction.atomic`).

### 5.2 Exemplo Concreto do Padrão CBV + Service

#### Na Camada de View (`apps/participantes/views/importacao.py`):
```python
from django.contrib import messages
from django.shortcuts import redirect, render
from django.views.generic import FormView, TemplateView
from apps.participantes.forms.importacao import ImportacaoUploadForm
from apps.participantes.services.importacao.service import ImportacaoService


class ImportacaoUploadView(FormView):
    template_name = "participantes/importacao/upload.html"
    form_class = ImportacaoUploadForm

    def form_valid(self, form):
        arquivo = form.cleaned_data["arquivo"]
        service = ImportacaoService()
        
        # O Service executa a Fase 1 (sem gravar nada no banco)
        preview = service.processar_preview(arquivo)
        
        # Armazena referência ou dados transitórios
        self.request.session["import_preview_data"] = preview.to_dict()
        return redirect("participantes:importacao_preview")
```

#### Na Camada de Service (`apps/participantes/services/importacao/service.py`):
```python
class ImportacaoService:
    def __init__(self, reader=None, processor=None, importer=None):
        self.reader = reader or ExcelReader()
        self.processor = processor or ImportacaoProcessor()
        self.importer = importer or DatabaseImporter()

    def processar_preview(self, arquivo) -> ImportPreview:
        """Fase 1: Lê, normaliza e valida sem tocar no banco de dados."""
        linhas_brutas = self.reader.read(arquivo)
        linhas_processadas = []

        for idx, linha in enumerate(linhas_brutas, start=2):
            resultado_linha = self.processor.process_row(linha, row_number=idx)
            linhas_processadas.append(resultado_linha)

        return ImportPreview.from_processed_rows(linhas_processadas)

    def executar_importacao(self, linhas_validas: list[dict]) -> ImportResult:
        """Fase 2: Grava sob transação atômica completa."""
        return self.importer.persist_atomic(linhas_validas)
```

---

## 6. O Pipeline de Importação: Contrato de 2 Fases

Para garantir que o banco nunca fique com estado intermediário corrompido, a importação opera estritamente em **duas fases desacopladas**:

```
                       [ UPLOAD DO EXCEL ]
                                │
                                ▼
                       ┌─────────────────┐
                       │   ExcelReader   │
                       └────────┬────────┘
                                │ (Linhas Brutas)
                                ▼
                       ┌─────────────────┐
                       │   Normalizer    │  (Funções Puras)
                       └────────┬────────┘
                                │ (Linhas Sanitizadas)
                                ▼
                       ┌─────────────────┐
                       │    Validator    │  (Regras de Domínio)
                       └────────┬────────┘
                                │
              ┌─────────────────┴─────────────────┐
              ▼                                   ▼
    [ LINHAS INVÁLIDAS ]                [ LINHAS VÁLIDAS ]
              │                                   │
              ▼                                   ▼
      Relatório de Erros                  Tabela de Prévia
      (Linha, Código, Causa)              (Total apto para carga)
              │                                   │
              └─────────────────┬─────────────────┘
                                ▼
                    [ CONFIRMAÇÃO DO USUÁRIO ]
                                │
                                ▼
                       ┌─────────────────┐
                       │    Importer     │
                       │                 │
                       │with transaction:│
                       │  1. Pessoa      │
                       │  2. Instituicao │
                       │  3. Evento      │
                       │  4. Participacao│
                       └────────┬────────┘
                                │
                                ▼
                       [ POSTGRESQL / SQLITE ]
```

### 6.1 Regra de Ouro: Normalização vs. Validação
1. **O Normalizador NUNCA rejeita uma linha:** Sua função é exclusivamente padronizar tipos (ex.: remover máscara de CPF `"002.089.351-50"` -> `"00208935150"`, converter número serial do Excel `46261` para `date(2026, 8, 16)`, converter `"  Amazonas "` para `"AM"`). Se o valor for ilegível ou ausente, converte para `None`.
2. **O Validador NUNCA transforma dados:** Sua função é apenas emitir julgamento com base nos dados já normalizados (ex.: verificar se o CPF possui exatamente 11 dígitos e passa pelo algoritmo de DV, se a data do evento está preenchida, se a data de nascimento é verossímil).

### 6.2 Estrutura Padronizada de Erros (`ValidationError`)
Erros são estruturados via dataclass para consumo simplificado pelo template e relatórios:
```python
@dataclass(frozen=True)
class ValidationError:
    field: str      # Nome do campo ('cpf', 'data_evento', etc.)
    code: str       # Código de máquina ('invalid_cpf_dv', 'missing_event_date')
    message: str    # Mensagem amigável ('Dígito verificador do CPF inválido.')
```

---

## 7. Padrão de Templates, Frontend e Visualização

### 7.1 Filosofia do Frontend
* **Sem Frameworks JS Pesados:** Nada de React, Vue ou Angular compilados. O projeto usa a capacidade nativa de renderização do Django Templates (`DTL`) com Bootstrap 5.3 e Vanilla JS moderno.
* **Componentes Acessíveis e Responsivos:** Grids `container-fluid`, `row`, `col-*`, tabelas com `table-responsive`, badges informativos e tooltips do Bootstrap.
* **Isolamento de Scripts:** Nenhuma tag `<script>` espalhada no meio do HTML com interpolações inseguras de Django (`var x = {{ data }}`). Os dados são serializados com o filtro `json_script` seguro e consumidos por funções no arquivo estático `dashboard.js`.

### 7.2 Arquitetura do Layout Mestre (`templates/base.html`)
O template base define a casca visual da aplicação:
```html
<!DOCTYPE html>
<html lang="pt-BR">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{% block title %}SIPAC — Gestão de Participações{% endblock %}</title>

    <!-- Bootstrap 5.3 CDN -->
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.3/dist/css/bootstrap.min.css" rel="stylesheet">
    <link href="https://cdn.jsdelivr.net/npm/bootstrap-icons@1.11.3/font/bootstrap-icons.min.css" rel="stylesheet">
    
    <!-- CSS Customizado -->
    <link href="{% static 'css/style.css' %}" rel="stylesheet">
    {% block extra_css %}{% endblock %}
</head>
<body class="bg-light d-flex flex-column min-vh-100">
    <!-- Navbar Superior -->
    <nav class="navbar navbar-expand-lg navbar-dark bg-success shadow-sm">
        <div class="container-fluid px-4">
            <a class="navbar-brand fw-bold" href="{% url 'participantes:dashboard' %}">
                <i class="bi bi-tree me-2"></i>SIPAC
            </a>
            <div class="navbar-nav ms-auto">
                <a class="nav-link" href="{% url 'participantes:dashboard' %}"><i class="bi bi-speedometer2 me-1"></i> Dashboard</a>
                <a class="nav-link" href="{% url 'participantes:importacao_upload' %}"><i class="bi bi-file-earmark-arrow-up me-1"></i> Importar</a>
                <a class="nav-link" href="/admin/"><i class="bi bi-shield-lock me-1"></i> Admin</a>
            </div>
        </div>
    </nav>

    <!-- Mensagens Globais (Flash Messages) -->
    <main class="container-fluid px-4 py-4 flex-grow-1">
        {% if messages %}
            {% for message in messages %}
                <div class="alert alert-{{ message.tags }} alert-dismissible fade show" role="alert">
                    {{ message }}
                    <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
                </div>
            {% endfor %}
        {% endif %}

        {% block content %}{% endblock %}
    </main>

    <!-- Footer -->
    <footer class="bg-white border-top py-3 text-center text-muted small mt-auto">
        <div class="container">
            SIPAC — Sistema de Informações de Participação e Capacitação &copy; 2026
        </div>
    </footer>

    <!-- Bootstrap Bundle JS -->
    <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.3.3/dist/js/bootstrap.bundle.min.js"></script>
    {% block extra_js %}{% endblock %}
</body>
</html>
```

### 7.3 Integração Segura do Chart.js
Para passar métricas do Django para o Chart.js com segurança e sem quebrar strings com aspas:

1. **No template (`dashboard/index.html`):**
   ```html
   {{ charts_data|json_script:"charts-data-json" }}
   ```
2. **No arquivo JS (`static/js/dashboard.js`):**
   ```javascript
   document.addEventListener("DOMContentLoaded", function () {
       const dataElem = document.getElementById("charts-data-json");
       if (!dataElem) return;
       
       const chartsData = JSON.parse(dataElem.textContent);
       
       // Renderizar gráfico de participações por Estado
       const ctxEstado = document.getElementById("chartEstado");
       if (ctxEstado && chartsData.por_estado) {
           new Chart(ctxEstado, {
               type: 'bar',
               data: {
                   labels: chartsData.por_estado.labels,
                   datasets: [{
                       label: 'Participações',
                       data: chartsData.por_estado.values,
                       backgroundColor: '#198754'
                   }]
               },
               options: { responsive: true, maintainAspectRatio: false }
           });
       }
   });
   ```

---

## 8. Regras de Escrita e Boas Práticas de Código

1. **PEP 8 Estrito:** Indentação de 4 espaços, linhas de no máximo 100 caracteres para clareza, imports agrupados na ordem padrão (Standard library -> Third-party -> Local Django apps).
2. **Type Annotations Mandatórias:** Todos os métodos de services, normalizadores e validadores devem conter assinaturas completas de tipo:
   ```python
   def normalize_cpf(value: Any) -> str | None: ...
   def validate_cpf(cpf: str | None) -> list[ValidationError]: ...
   ```
3. **Imutabilidade e Dataclasses:** Estruturas de trânsito de dados (DTOs) devem usar `@dataclass(frozen=True)` para evitar efeitos colaterais.
4. **Isolamento de Testes:** Os testes de normalizadores e validadores devem ser **testes unitários puros**, que não herdam de `TestCase` do Django (não instanciam banco nem executam migrações), rodando centenas de validações em milissegundos.
5. **Preservação de Documentação:** Código claro, nomes de variáveis legíveis em português ou padrão Django estabelecido, e docstrings pontuais descrevendo a regra de negócio do bloco.

---

## 9. Próximos Passos de Execução

Com esta Memória Técnica registrada e servindo de alicerce normativo, a implementação do projeto seguirá rigorosamente as 6 Fases estabelecidas no [implementation_plan.md](file:///home/pedrohsn/.gemini/antigravity/brain/f809e779-e88b-40b5-bee0-c1805e45c9f0/implementation_plan.md).
