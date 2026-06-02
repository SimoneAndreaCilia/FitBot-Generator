<p align="center">
  <img src="https://img.icons8.com/color/96/dumbbell.png" alt="FitBot Logo" width="80"/>
</p>

<h1 align="center">🏋️ FitBot — Workout of the Day Telegram Bot</h1>

<p align="center">
  <em>Generatore di schede di allenamento personalizzate, accessibile tramite Telegram Bot.</em>
</p>

<p align="center">
  <img src="https://img.shields.io/badge/python-3.11+-3776AB?style=for-the-badge&logo=python&logoColor=white" alt="Python 3.11+"/>
  <img src="https://img.shields.io/badge/Telegram-Bot_API-26A5E4?style=for-the-badge&logo=telegram&logoColor=white" alt="Telegram Bot API"/>
  <img src="https://img.shields.io/badge/SQLAlchemy-2.0-D71F00?style=for-the-badge&logo=sqlalchemy&logoColor=white" alt="SQLAlchemy 2.0"/>
  <img src="https://img.shields.io/badge/License-MIT-green?style=for-the-badge" alt="MIT License"/>
</p>

<p align="center">
  <img src="https://img.shields.io/badge/pytest-cov_≥75%25-009688?style=flat-square&logo=pytest" alt="Coverage"/>
  <img src="https://img.shields.io/badge/code%20style-black-000000?style=flat-square" alt="Black"/>
  <img src="https://img.shields.io/badge/type_checked-mypy_strict-blue?style=flat-square" alt="Mypy"/>
  <img src="https://img.shields.io/badge/linting-pylint_%7C_flake8-orange?style=flat-square" alt="Linting"/>
</p>

---

## 📖 Indice

- [Panoramica](#-panoramica)
- [Funzionalità e Comandi del Bot](#-funzionalità-e-comandi-del-bot)
- [Screenshots UX](#-screenshots-ux)
- [Architettura del Progetto](#-architettura-del-progetto)
- [Struttura del Repository](#-struttura-del-repository)
- [Guida all'Installazione](#-guida-allinstallazione)
- [Sviluppo e Qualità del Codice](#-sviluppo-e-qualità-del-codice)
- [Testing](#-testing)
- [CI/CD Pipeline](#-cicd-pipeline)
- [Tech Stack](#-tech-stack)

---

## 🎯 Panoramica

**FitBot** è un Telegram Bot progettato per generare schede di allenamento personalizzate (WOD — *Workout of the Day*) basate sul profilo fisico dell'utente, il suo livello di esperienza e l'attrezzatura disponibile.

Il progetto è stato sviluppato seguendo i principi della **Quality Development** con un focus su:

- ✅ **Core logic disaccoppiata** — la business logic è completamente separata dall'interfaccia Telegram
- ✅ **Architettura testabile** — ogni layer può essere testato in isolamento
- ✅ **Copertura dei test ≥ 75%** — enforced automaticamente nella CI pipeline
- ✅ **Static analysis completa** — Black, isort, Flake8, Pylint, Mypy (strict mode)
- ✅ **Pre-commit hooks** — qualità garantita ad ogni commit
- ✅ **CI/CD con GitHub Actions** — lint + test automatici su ogni push/PR

---

## 🤖 Funzionalità e Comandi del Bot

| Comando / Pulsante | Emoji | Descrizione |
|---|---|---|
| `/start` | 👋 | Avvia il bot e mostra il menu principale con tutti i comandi disponibili |
| **Nuova scheda** | 🏆 | Crea una nuova scheda di allenamento personalizzata tramite un processo di onboarding guidato. L'utente inserisce i propri dati (livello, frequenza, split, attrezzatura) o usa il profilo esistente |
| **Profilo** | 👤 | Visualizza il profilo completo dell'utente con tutte le informazioni personali (nome, altezza, peso, BMI, corporatura, livello, frequenza, split, attrezzatura). Include opzione per modificare il profilo |
| **🔥 WOD del giorno** | 🔥 | Mostra il Workout of the Day — l'allenamento giornaliero basato sulla scheda attiva, con navigazione tra i giorni della settimana (Indietro/Avanti) |
| **📜 Storico** | 📜 | Rivedi le schede di allenamento generate in passato, con possibilità di scaricarle in formato PDF o TXT |
| **⭐ Preferiti** | ⭐ | Accedi alle schede salvate nei preferiti per un rapido accesso alle routine più apprezzate |

### Flusso Utente

```
/start → Menu Principale
           ├── 🏆 Nuova scheda → Onboarding (livello, frequenza, split, attrezzatura) → Scheda generata
           ├── 👤 Profilo → Visualizza/Modifica dati personali
           ├── 🔥 WOD del giorno → Navigazione giornaliera della scheda attiva
           ├── 📜 Storico → Lista schede passate → Download PDF/TXT
           └── ⭐ Preferiti → Schede salvate
```

---

## 📱 Screenshots UX

Di seguito sono mostrate le schermate principali dell'interfaccia del bot Telegram:

<table>
  <tr>
    <td align="center" width="33%">
      <img src="docs/screenshots/start_command.jpg" width="260" alt="Comando /start"/>
      <br/>
      <b>Comando /start</b>
      <br/>
      <sub>Il bot accoglie l'utente con un messaggio di benvenuto e mostra l'elenco completo dei comandi disponibili. In basso sono presenti i pulsanti rapidi del menu.</sub>
    </td>
    <td align="center" width="33%">
      <img src="docs/screenshots/wod_profile.jpg" width="260" alt="WOD e Profilo"/>
      <br/>
      <b>WOD del giorno & Profilo</b>
      <br/>
      <sub>In alto: il WOD mostra l'allenamento del giorno con navigazione tra i giorni. In basso: il profilo utente con tutti i dati personali e il calcolo del BMI.</sub>
    </td>
    <td align="center" width="33%">
      <img src="docs/screenshots/preferiti.jpg" width="260" alt="Preferiti"/>
      <br/>
      <b>Preferiti</b>
      <br/>
      <sub>Lista delle schede salvate come preferite, con data/ora e tipo di programma. Tocca una scheda per visualizzarla.</sub>
    </td>
  </tr>
</table>

---

## 🏗️ Architettura del Progetto

Il progetto segue un'architettura **a tre layer** con separazione netta delle responsabilità, pensata per massimizzare la testabilità e il disaccoppiamento:

```
┌─────────────────────────────────────────────────┐
│                  Telegram Bot                    │
│           (Handlers & Keyboards)                 │
│          src/wod/bot/                            │
├─────────────────────────────────────────────────┤
│                  Core Logic                      │
│    (Engine, Split Generator, BMI, Intensity)     │
│          src/wod/core/                           │
├─────────────────────────────────────────────────┤
│                  Data Layer                      │
│     (SQLAlchemy Models & Repositories)           │
│          src/wod/db/                             │
└─────────────────────────────────────────────────┘
```

### Layer Details

| Layer | Path | Responsabilità | Principio di Qualità |
|---|---|---|---|
| **Bot** | `src/wod/bot/` | Interfaccia Telegram — gestione comandi, tastiere, formattazione messaggi | Thin controller — nessuna business logic |
| **Core** | `src/wod/core/` | Logica di dominio — filtraggio esercizi, generazione split, calcolo BMI e intensità | Pura business logic senza dipendenze esterne |
| **DB** | `src/wod/db/` | Persistenza — modelli SQLAlchemy, repository pattern, seeding dati | Repository pattern per isolare l'accesso ai dati |
| **Config** | `src/wod/config.py` | Configurazione centralizzata tramite Pydantic Settings | Validazione automatica, type-safe |

### Principi Architetturali

- **Dependency Inversion** — I layer superiori non dipendono dall'implementazione concreta dei layer inferiori
- **Repository Pattern** — L'accesso ai dati è incapsulato in repository dedicati, semplificando mocking e testing
- **Pure Functions** — La core logic è implementata come funzioni pure, facilmente testabili senza setup complesso
- **Configuration as Code** — Tutte le impostazioni sono gestite tramite `pydantic-settings` con validazione automatica

---

## 📂 Struttura del Repository

```
FitBot-Generator/
├── .github/
│   └── workflows/
│       └── ci.yml                  # GitHub Actions — lint + test pipeline
├── data/
│   └── seed_exercises.json         # Catalogo esercizi per il seeding del DB
├── docs/
│   └── screenshots/                # Screenshot UX del bot
├── scripts/
│   └── seed_db.py                  # Script per il seeding manuale del database
├── src/
│   └── wod/
│       ├── __init__.py
│       ├── config.py               # Configurazione app (Pydantic Settings)
│       ├── bot/                    # 🤖 Layer Telegram
│       │   ├── main.py             # Entry point — assembla handlers e avvia polling
│       │   ├── keyboards.py        # Tastiere inline e reply del bot
│       │   ├── formatters.py       # Formattazione messaggi per l'utente
│       │   ├── utils.py            # Utility condivise del bot
│       │   └── handlers/           # Gestori dei comandi
│       │       ├── onboarding.py   # Flusso di registrazione e creazione scheda
│       │       ├── menu.py         # Menu principale e navigazione
│       │       ├── profile.py      # Visualizzazione e modifica profilo
│       │       ├── wod.py          # WOD del giorno e navigazione
│       │       ├── history.py      # Storico schede + export PDF/TXT
│       │       └── favorites.py    # Gestione schede preferite
│       ├── core/                   # 🧠 Layer Business Logic
│       │   ├── types.py            # Enums e value objects del dominio
│       │   ├── engine.py           # Filtraggio esercizi per attrezzatura e muscoli
│       │   ├── split_generator.py  # Generazione split settimanale
│       │   ├── intensity.py        # Calcolo serie, ripetizioni e intensità
│       │   └── bmi.py              # Calcolo BMI (classificazione WHO)
│       └── db/                     # 💾 Layer Persistenza
│           ├── models.py           # Modelli SQLAlchemy (User, Exercise, Routine, ecc.)
│           ├── repositories.py     # Repository pattern per accesso ai dati
│           ├── session.py          # Gestione sessioni async del database
│           └── seeding.py          # Auto-seeding del catalogo esercizi
├── tests/                          # 🧪 Suite di Test
│   ├── conftest.py                 # Fixture condivise (DB in-memory, mock)
│   ├── test_config.py              # Test configurazione
│   ├── bot/                        # Test layer Bot
│   │   ├── test_main.py            # Test entry point e handler registration
│   │   ├── test_keyboards.py       # Test tastiere e layout
│   │   ├── test_formatters.py      # Test formattazione messaggi
│   │   ├── test_utils.py           # Test utility
│   │   ├── test_onboarding.py      # Test flusso onboarding
│   │   ├── test_profile.py         # Test gestione profilo
│   │   └── test_wod_helpers.py     # Test helper WOD
│   ├── core/                       # Test layer Core
│   │   ├── test_bmi.py             # Test calcolo BMI
│   │   ├── test_engine.py          # Test filtraggio esercizi
│   │   ├── test_intensity.py       # Test calcolo intensità
│   │   ├── test_split_generator.py # Test generazione split
│   │   └── test_types.py           # Test domain types
│   └── db/                         # Test layer DB
│       ├── test_models.py          # Test modelli
│       ├── test_repositories.py    # Test repository pattern
│       ├── test_seeding.py         # Test seeding dati
│       └── test_session.py         # Test sessioni DB
├── .coveragerc                     # Configurazione code coverage
├── .flake8                         # Configurazione Flake8
├── .pre-commit-config.yaml         # Hook pre-commit
├── .pylintrc                       # Configurazione Pylint
├── mypy.ini                        # Configurazione MyPy
├── pyproject.toml                  # Configurazione progetto e dipendenze
└── README.md
```

---

## 🚀 Guida all'Installazione

### Prerequisiti

- **Python 3.11+** — [Download](https://www.python.org/downloads/)
- **Git** — [Download](https://git-scm.com/)
- **Token Telegram Bot** — Ottenibile tramite [@BotFather](https://t.me/BotFather) su Telegram

### Step 1 — Clona il repository

```bash
git clone https://github.com/SimoneAndreaCilia/FitBot-Generator.git
cd FitBot-Generator
```

### Step 2 — Crea e attiva l'ambiente virtuale

```bash
# Crea il virtual environment
python -m venv .venv

# Attiva l'ambiente virtuale
.venv\Scripts\activate          # Windows (PowerShell / CMD)
# source .venv/bin/activate     # macOS / Linux
```

### Step 3 — Installa le dipendenze

```bash
# Installa il progetto in modalità editable con le dipendenze di sviluppo
pip install -e ".[dev]"
```

### Step 4 — Configura le variabili d'ambiente

```bash
# Crea il file .env dalla template
cp .env.example .env
```

Modifica il file `.env` e inserisci il tuo token Telegram:

```ini
TELEGRAM_BOT_TOKEN=il-tuo-token-qui
```

> [!TIP]
> Per ottenere un token, apri Telegram, cerca **@BotFather**, invia `/newbot` e segui le istruzioni.

### Step 5 — Avvia il bot

```bash
# Avvia il bot in modalità long-polling
wod-bot
```

Il bot si connetterà a Telegram e inizierà a ricevere messaggi. Cerca il tuo bot su Telegram e invia `/start` per iniziare! 🎉

---

## 🔧 Sviluppo e Qualità del Codice

Questo progetto implementa una **toolchain di qualità completa**, in linea con le best practice della materia **Quality Development**.

### Pre-commit Hooks

Il progetto utilizza `pre-commit` per garantire che il codice rispetti gli standard di formattazione e qualità **prima di ogni commit**.

```bash
# Installa pre-commit
pip install pre-commit

# Installa i ganci di pre-commit nel repository locale
pre-commit install
```

I seguenti controlli vengono eseguiti automaticamente ad ogni `git commit`:

| Hook | Strumento | Funzione |
|---|---|---|
| Trailing whitespace | pre-commit | Rimuove spazi bianchi a fine riga |
| End-of-file fixer | pre-commit | Assicura newline finale nei file |
| YAML check | pre-commit | Valida la sintassi dei file YAML |
| Code formatting | **Black** | Formattazione automatica del codice |
| Import sorting | **isort** | Ordinamento automatico degli import |
| Style checking | **Flake8** | Controllo stile PEP 8 |
| Static analysis | **Pylint** | Analisi statica approfondita |
| Type checking | **MyPy** | Controllo dei tipi in modalità strict |

### Esecuzione Manuale

È possibile eseguire manualmente i controlli senza effettuare un commit:

```bash
# Esegui tutti i controlli pre-commit
pre-commit run --all-files

# Oppure esegui i singoli strumenti:
black src/ tests/                # Formattazione
isort src/ tests/                # Import sorting
flake8 src/ tests/               # Style checking
pylint src/wod/                  # Static analysis
mypy src/wod/                    # Type checking
```

---

## 🧪 Testing

La suite di test è strutturata in modo da rispecchiare i tre layer dell'architettura:

```
tests/
├── core/    → Test unitari della business logic (puri, senza I/O)
├── bot/     → Test dei gestori Telegram (con mock dell'API)
└── db/      → Test del layer di persistenza (DB in-memory)
```

### Esecuzione dei test

```bash
# Esegui tutti i test con report di copertura
pytest

# Esegui solo i test di un layer specifico
pytest tests/core/               # Solo core logic
pytest tests/bot/                # Solo bot handlers
pytest tests/db/                 # Solo database

# Esegui un singolo file di test
pytest tests/core/test_bmi.py

# Esegui con output dettagliato
pytest -v --tb=short
```

### Configurazione Coverage

La copertura minima è impostata al **75%** e viene verificata automaticamente:

```ini
# pyproject.toml
[tool.pytest.ini_options]
addopts = [
    "--strict-markers",
    "--cov=src/wod",
    "--cov-report=term-missing",
    "--cov-fail-under=75",
]
```

> [!IMPORTANT]
> Se la copertura scende sotto il 75%, i test falliranno sia in locale che nella CI pipeline.

---

## ⚙️ CI/CD Pipeline

Il progetto utilizza **GitHub Actions** per l'integrazione continua. La pipeline viene eseguita automaticamente su ogni `push` e `pull_request` verso il branch `main`.

```
CI Pipeline
│
├── 🔍 Job: Lint & Type-check
│   ├── black --check          (formattazione)
│   ├── isort --check-only     (ordinamento import)
│   ├── flake8                 (stile PEP 8)
│   ├── pylint                 (analisi statica)
│   └── mypy                   (type checking strict)
│
└── 🧪 Job: Tests (dipende da Lint)
    └── pytest --cov --cov-fail-under=75
```

> [!NOTE]
> Il job dei test viene eseguito **solo se** il job di lint supera tutti i controlli, garantendo che il codice rispetti gli standard di qualità prima di verificare la correttezza funzionale.

---

## 🛠️ Tech Stack

| Tecnologia | Versione | Ruolo |
|---|---|---|
| [Python](https://www.python.org/) | 3.11+ | Linguaggio principale |
| [python-telegram-bot](https://python-telegram-bot.org/) | 21.x | Framework Telegram Bot API |
| [SQLAlchemy](https://www.sqlalchemy.org/) | 2.0 | ORM e gestione database |
| [aiosqlite](https://github.com/omnilib/aiosqlite) | 0.20+ | Driver SQLite asincrono |
| [Pydantic](https://docs.pydantic.dev/) | 2.0 | Validazione dati e configurazione |
| [ReportLab](https://www.reportlab.com/) | 4.0 | Generazione file PDF |
| [pytest](https://docs.pytest.org/) | 8.0 | Framework di testing |
| [Black](https://black.readthedocs.io/) | 24.x | Formattazione automatica del codice |
| [MyPy](https://mypy.readthedocs.io/) | 1.8+ | Type checking statico (strict) |
| [Pylint](https://pylint.readthedocs.io/) | 3.x | Analisi statica del codice |
| [Flake8](https://flake8.pycqa.org/) | 7.0 | Controllo stile PEP 8 |
| [GitHub Actions](https://github.com/features/actions) | — | CI/CD pipeline |

---

<p align="center">
  Sviluppato come progetto per il corso di <strong>Quality Development</strong> 💪
</p>
