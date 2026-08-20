# ⚽ Brasileirão Data Lab

<p align="center">
  Plataforma de dados para coleta, processamento, análise, Machine Learning e visualização do Campeonato Brasileiro Série A.
</p>

<p align="center">
  <strong>Python • FastAPI • React • TypeScript • SQLite • Pandas • Scikit-learn</strong>
</p>

<p align="center">
  <a href="https://brasileirao-data-lab.vercel.app">
    <img src="https://img.shields.io/badge/App-Online-27d684" alt="App Online" />
  </a>
  <a href="https://brasileirao-data-lab-api.onrender.com/docs">
    <img src="https://img.shields.io/badge/API-FastAPI-009688?logo=fastapi&logoColor=white" alt="FastAPI" />
  </a>
  <a href="https://github.com/cadupacheco/Brasileirao-Data-Lab/actions/workflows/ci.yml">
    <img src="https://github.com/cadupacheco/Brasileirao-Data-Lab/actions/workflows/ci.yml/badge.svg" alt="CI" />
  </a>
  <img src="https://img.shields.io/badge/version-v0.7.0-27d684" alt="Version v0.7.0" />
</p>

<p align="center">
  <a href="https://brasileirao-data-lab.vercel.app"><strong>🌐 Acessar aplicação</strong></a>
  •
  <a href="https://brasileirao-data-lab-api.onrender.com/docs"><strong>📚 Swagger da API</strong></a>
</p>

---

## 📌 Sobre o projeto

O **Brasileirão Data Lab** é uma plataforma de dados aplicada ao Campeonato Brasileiro Série A.

O projeto coleta informações da competição, processa e valida os dados, persiste os resultados em banco de dados, disponibiliza uma API REST, apresenta análises em um dashboard web e utiliza Machine Learning para gerar probabilidades de partidas e projeções do campeonato.

A partir da `v0.7.0`, o projeto também possui atualização automática dos dados. O sistema verifica periodicamente a CBF, detecta alterações reais no campeonato e, quando necessário, reconstrói toda a cadeia de dados, Machine Learning, simulações e publicação.

A evolução acontece em etapas versionadas, partindo da coleta de dados e avançando por analytics, banco de dados, API, frontend, deploy, Machine Learning e automação.

---

## 🌐 Aplicação em produção

### Dashboard

**https://brasileirao-data-lab.vercel.app**

Frontend desenvolvido com React + TypeScript e publicado na Vercel.

### API

**https://brasileirao-data-lab-api.onrender.com**

Documentação Swagger:

**https://brasileirao-data-lab-api.onrender.com/docs**

Backend desenvolvido com FastAPI e publicado no Render.

---

## 🏗️ Arquitetura

```text
                         CBF
                          │
                          ▼
                  Verificação periódica
                    GitHub Actions
                          │
                          ▼
                   Coleta dos dados
                          │
                          ▼
               Detecção de alterações
                          │
                  ┌───────┴───────┐
                  │               │
             Sem mudança      Com mudança
                  │               │
                  ▼               ▼
              Finaliza       Validação do
            sem rebuild       novo snapshot
                                  │
                                  ▼
                        Atualização dos dados
                                  │
                    ┌─────────────┴─────────────┐
                    ▼                           ▼
                 SQLite                  Dataset histórico
                    │                           │
                    ▼                           ▼
                Analytics               Feature Engineering
                    │                           │
                    │                           ▼
                    │                     Random Forest
                    │                           │
                    │                  ┌────────┴────────┐
                    │                  ▼                 ▼
                    │           Prob. por jogo      Monte Carlo
                    │                  │                 │
                    └──────────────────┴────────┬────────┘
                                               ▼
                                            FastAPI
                                               │
                                               ▼
                                             Render
                                               │
                                               ▼
                                        React + Vite
                                               │
                                               ▼
                                            Vercel
```

O projeto é dividido em cinco grandes camadas.

### Data Layer

Responsável pela coleta, tratamento, validação, analytics e persistência dos dados.

### Machine Learning

Responsável pelo dataset histórico, feature engineering, Elo, confrontos diretos, treinamento, avaliação, probabilidades de partidas e simulação do campeonato.

### Backend

API REST construída com FastAPI, responsável por disponibilizar dados processados, previsões e informações sobre o estado da atualização automática.

### Frontend

Dashboard desenvolvido em React + TypeScript para visualização e exploração dos dados, projeções do campeonato e estado de sincronização dos dados.

### Automação

GitHub Actions executa verificações periódicas na fonte oficial, detecta mudanças e inicia automaticamente a reconstrução dos artefatos quando necessário.

---

## 🤖 Machine Learning

A `v0.6.0` adicionou o primeiro motor preditivo do projeto.

A `v0.7.0` passou a integrar esse motor ao fluxo automático de atualização, permitindo recalcular previsões sempre que novos resultados forem detectados.

### Dataset histórico

Foram coletadas as temporadas de **2021 a 2026**, totalizando no snapshot de referência:

- 2.280 partidas no histórico;
- 2.125 partidas disputadas;
- 155 partidas futuras.

### Feature engineering

As features são reconstruídas de forma cronológica para evitar vazamento de informação.

Entre os sinais utilizados estão:

- pontos por jogo;
- saldo de gols por jogo;
- forma recente em 5 e 10 partidas;
- desempenho como mandante e visitante;
- médias recentes de gols;
- rating Elo;
- vantagem de mando no Elo;
- confrontos diretos históricos;
- forma recente do confronto direto.

### Modelos avaliados

Foram comparados:

- Regressão Logística multinomial;
- Random Forest;
- Gradient Boosting.

A seleção foi feita por backtest temporal com validações em 2023, 2024 e 2025, priorizando:

1. Log Loss;
2. Brier Score;
3. Accuracy como critério secundário.

O **Random Forest** apresentou o melhor resultado agregado e foi escolhido como modelo principal.

### Calibração

Foi testado Temperature Scaling.

Como a calibração não melhorou Log Loss e Brier na referência de 2026, a versão utiliza as probabilidades brutas do Random Forest.

### Previsões de partidas

Cada partida futura recebe probabilidades para:

```text
Mandante
Empate
Visitante
```

Exemplo:

```text
Fluminense 67.0% • X 19.2% • Remo 13.8%
```

### Monte Carlo

O restante do campeonato é simulado **10.000 vezes** com seed fixa para reprodutibilidade.

As simulações produzem:

- posição projetada;
- pontos esperados;
- posição média;
- probabilidade de título;
- probabilidade de G4;
- probabilidade de Top 6;
- probabilidade de rebaixamento.

Sempre que uma alteração real nos resultados é detectada, as previsões e simulações podem ser reconstruídas automaticamente pela pipeline da `v0.7.0`.

---

## 📊 Dashboard

O dashboard possui seis áreas principais.

### 🏠 Visão Geral

Resumo do campeonato com:

- líder atual;
- partidas realizadas;
- jogos restantes;
- gols marcados;
- média de gols;
- melhor ataque;
- melhor defesa;
- aproveitamento do líder;
- desempenho recente dos clubes.

### 🏆 Classificação

Tabela completa da Série A com:

- posição;
- jogos;
- vitórias;
- empates;
- derrotas;
- gols pró;
- gols contra;
- saldo de gols;
- aproveitamento;
- pontos.

### 🛡️ Clubes

Visão dos 20 clubes participantes da competição com seus principais indicadores.

### 📈 Evolução

Visualização rodada a rodada da trajetória dos clubes.

É possível selecionar clubes e alternar entre:

- evolução da posição;
- evolução da pontuação.

### 📅 Jogos

Consulta das partidas do campeonato com filtros por:

- rodada;
- clube;
- jogos realizados;
- próximos jogos.

Jogos futuros exibem também as probabilidades do modelo para vitória do mandante, empate e vitória do visitante.

### 🤖 Previsões

Painel preditivo com:

- classificação projetada;
- pontos esperados;
- posição média;
- corrida pelo título;
- chances de G4;
- chances de Top 6;
- risco de rebaixamento;
- visualização dos resultados das 10.000 simulações.

### 📡 Estado dos dados

A `v0.7.0` adiciona um indicador global na interface mostrando:

- data e horário de sincronização;
- fonte dos dados;
- estado da automação;
- quantidade de partidas disputadas;
- quantidade de partidas futuras.

O horário do snapshot é armazenado em UTC e exibido no dashboard convertido para o horário de Brasília.

---

## 🚀 API REST

Principais endpoints:

```text
GET /api/health
GET /api/status
GET /api/championship/summary
GET /api/standings
GET /api/recent-form
GET /api/evolution
GET /api/matches
GET /api/predictions/matches
GET /api/predictions/standings
```

Os endpoints de previsões permitem acessar:

```text
/api/predictions/matches?round_number=24
/api/predictions/matches?team_id=<id>
/api/predictions/standings
```

### Status da atualização

O endpoint:

```text
GET /api/status
```

retorna informações públicas sobre o snapshot atualmente publicado.

Exemplo:

```json
{
  "season": 2026,
  "source": "CBF",
  "status": "up_to_date",
  "last_sync_at_utc": "2026-08-20T12:45:41Z",
  "total_matches": 380,
  "played_matches": 225,
  "future_matches": 155,
  "automation_enabled": true,
  "checks_per_day": 4
}
```

Esse endpoint é utilizado pelo frontend para exibir o estado de atualização dos dados.

---

## 🔄 Atualização automática

A `v0.7.0` transforma o Brasileirão Data Lab em uma plataforma capaz de acompanhar automaticamente a evolução do campeonato.

A estratégia adotada é:

> **não agendar jogos, agendar verificações.**

Em vez de depender dos dias em que normalmente existem partidas, a aplicação realiza verificações periódicas na CBF.

Isso também permite detectar:

- jogos adiados;
- partidas remarcadas;
- resultados lançados posteriormente;
- alterações em rodadas anteriores;
- mudanças de data ou horário;
- novos resultados publicados pela fonte oficial.

### Frequência

A automação realiza **4 verificações por dia**.

Os horários configurados correspondem aproximadamente a:

```text
08:00
14:00
20:00
23:59
```

no horário de Brasília.

### Detecção semântica

O sistema não compara apenas o número da rodada atual.

As partidas são identificadas individualmente e campos relevantes são comparados para detectar mudanças reais.

Entre os dados observados estão:

- ID da partida;
- rodada;
- data;
- horário;
- mandante;
- visitante;
- gols;
- estádio;
- cidade;
- estado;
- status;
- resultado.

### Fluxo sem alteração

Quando a CBF não apresenta mudanças:

```text
CBF
 │
 ▼
Verificação
 │
 ▼
Nenhuma alteração
 │
 ├─ não reconstrói features
 ├─ não recalcula previsões
 ├─ não executa Monte Carlo
 ├─ não altera banco
 └─ não cria commit
```

Isso evita processamento e histórico Git desnecessários.

### Fluxo com alteração

Quando uma mudança real é identificada:

```text
CBF
 │
 ▼
Novo snapshot
 │
 ▼
Validação
 │
 ▼
Atualização das partidas
 │
 ├─ SQLite
 ├─ histórico
 ├─ features
 ├─ previsões
 ├─ Monte Carlo
 └─ metadata
 │
 ▼
Testes automatizados
 │
 ▼
Commit automático
 │
 ▼
Push para main
 │
 ▼
Deploy
```

### Proteção do último estado válido

O projeto adota validações antes de publicar novos dados.

Snapshots inválidos, incompletos ou inconsistentes interrompem a atualização.

O objetivo é preservar sempre o último estado conhecido como válido.

Entre as validações estão:

- quantidade esperada de partidas;
- existência das 20 equipes;
- status válidos;
- dados essenciais de partidas disputadas;
- consistência entre partidas realizadas e futuras;
- geração correta dos artefatos de Machine Learning.

---

## 📝 Metadata da atualização

A `v0.7.0` adiciona:

```text
data/update_metadata.json
```

Esse arquivo representa o estado público do snapshot atualmente publicado.

Exemplo:

```json
{
  "season": 2026,
  "source": "CBF",
  "status": "up_to_date",
  "last_sync_at_utc": "2026-08-20T12:45:41Z",
  "total_matches": 380,
  "played_matches": 225,
  "future_matches": 155,
  "automation_enabled": true,
  "checks_per_day": 4
}
```

O campo `last_sync_at_utc` representa o momento em que o snapshot publicado foi sincronizado.

Uma verificação sem alteração não modifica esse horário e não gera um novo commit apenas para atualizar metadata.

---

## 🔄 CI/CD

Desde a `v0.5.0`, o projeto utiliza **GitHub Actions** para validar automaticamente alterações enviadas ao repositório.

Na `v0.7.0`, o GitHub Actions também passa a participar diretamente da atualização dos dados.

Existem dois fluxos principais.

### CI de desenvolvimento

```text
Push / Pull Request
        │
        ├──────────────┐
        ▼              ▼
 Python Tests      React Build
     pytest        npm run build
        │              │
        └──────┬───────┘
               ▼
              CI
```

Validações atuais:

- testes automatizados Python com Pytest;
- instalação do projeto Python;
- instalação do frontend com `npm ci`;
- build de produção do React/Vite.

### Atualização automatizada

```text
Schedule / Manual
       │
       ▼
GitHub Actions
       │
       ▼
Consulta CBF
       │
       ▼
Detecta mudança?
   │         │
  não       sim
   │         │
   ▼         ▼
 encerra   rebuild
             │
             ▼
           testes
             │
             ▼
           commit
             │
             ▼
            main
```

O workflow de atualização utiliza runner Windows para compatibilidade com a cadeia de certificados SSL utilizada pela CBF.

A execução também força UTF-8 para manter os logs e scripts compatíveis com caracteres utilizados pelo projeto.

O backend é publicado no **Render** e o frontend na **Vercel**.

---

## 🧰 Tecnologias

### Backend e dados

- Python
- FastAPI
- Pandas
- NumPy
- SciPy
- Scikit-learn
- SQLAlchemy
- SQLite
- BeautifulSoup
- Requests
- lxml
- Truststore

### Machine Learning

- Logistic Regression
- Random Forest
- Gradient Boosting
- Elo Rating
- H2H Features
- Backtest temporal
- Log Loss
- Brier Score
- Monte Carlo

### Frontend

- React
- TypeScript
- Vite
- React Router
- Recharts
- Lucide React

### Qualidade e infraestrutura

- Pytest
- Git
- GitHub
- GitHub Actions
- Vercel
- Render

---

## 📁 Estrutura do projeto

```text
Brasileirao-Data-Lab/
│
├── .github/
│   └── workflows/
│       ├── automated-update.yml
│       └── ci.yml
│
├── data/
│   ├── ml/
│   │   ├── features.csv
│   │   ├── future_predictions.csv
│   │   ├── matches_history.csv
│   │   └── season_simulation.csv
│   ├── processed/
│   ├── raw/
│   ├── brasileirao.db
│   └── update_metadata.json
│
├── frontend/
│   ├── public/
│   └── src/
│       ├── components/
│       │   └── UpdateStatusIndicator.tsx
│       ├── pages/
│       │   └── PredictionsPage.tsx
│       ├── api.ts
│       └── App.tsx
│
├── scripts/
│   ├── build_update_metadata.py
│   ├── check_updates.py
│   └── dry_run_v07_update.py
│
├── src/
│   └── brasileirao_data_lab/
│       ├── analytics/
│       ├── api/
│       │   └── status_router.py
│       ├── database/
│       ├── ml/
│       ├── pipelines/
│       │   ├── automated_ml_update.py
│       │   ├── automated_project_update.py
│       │   └── update_detector.py
│       ├── scrapers/
│       ├── update_metadata.py
│       └── utils/
│
├── tests/
│   ├── analytics/
│   ├── api/
│   ├── database/
│   ├── ml/
│   ├── pipeline/
│   └── scraper/
│
├── main.py
├── pyproject.toml
├── requirements.txt
└── README.md
```

---

## ⚙️ Executando localmente

### 1. Clone o repositório

```bash
git clone https://github.com/cadupacheco/Brasileirao-Data-Lab.git
cd Brasileirao-Data-Lab
```

### 2. Crie e ative o ambiente virtual

Windows:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

### 3. Instale as dependências e o projeto

```powershell
pip install -r requirements.txt
pip install -e .
```

### 4. Atualize os dados

```powershell
python main.py
```

### 5. Verifique atualizações da CBF

```powershell
python scripts\check_updates.py
```

### 6. Execute a atualização automatizada localmente

```powershell
python -m brasileirao_data_lab.pipelines.automated_project_update
```

### 7. Inicie a API

```powershell
uvicorn brasileirao_data_lab.api.app:app --reload --port 8000
```

Swagger local:

```text
http://127.0.0.1:8000/docs
```

### 8. Inicie o frontend

Em outro terminal:

```powershell
cd frontend
npm install
npm run dev
```

Frontend local:

```text
http://localhost:5173
```

---

## 🧠 Fluxo de Machine Learning

Os scripts principais introduzidos na `v0.6.0` são:

```powershell
python scripts\collect_cbf_history.py
python scripts\audit_team_identity.py
python scripts\build_ml_features.py
python scripts\train_ml_baseline.py
python scripts\compare_ml_models.py
python scripts\backtest_ml_models.py
python scripts\calibrate_ml_model.py
python scripts\predict_future_matches.py
python scripts\simulate_season.py
```

Arquivos gerados:

```text
data/ml/matches_history.csv
data/ml/features.csv
data/ml/future_predictions.csv
data/ml/season_simulation.csv
```

Na `v0.7.0`, a reconstrução dos artefatos necessários passa a fazer parte da pipeline automática quando novos dados são detectados.

---

## 🧪 Testes

Execute:

```powershell
pytest -q
```

Build do frontend:

```powershell
cd frontend
npm run build
```

A versão somente é considerada pronta quando os testes Python e o build do frontend passam sem erros.

No fechamento da `v0.7.0`, a suíte possui mais de 200 testes automatizados cobrindo coleta, analytics, banco de dados, API, Machine Learning, pipelines e metadata.

---

## 🗺️ Roadmap

| Versão | Objetivo | Status |
|---|---|---|
| `v0.1` | Coleta de dados | ✅ Concluído |
| `v0.2` | Analytics | ✅ Concluído |
| `v0.3` | Banco de dados | ✅ Concluído |
| `v0.4` | FastAPI + React Dashboard | ✅ Concluído |
| `v0.5` | Deploy + CI/CD | ✅ Concluído |
| `v0.6` | Machine Learning e previsões | ✅ Concluído |
| `v0.7` | Atualização automática dos dados | ✅ Concluído |
| `v1.0` | Plataforma completa | 🎯 Próxima etapa |

---

## 🔮 Próximas evoluções

Com a `v0.7.0` concluída, a próxima grande etapa é a `v1.0`, consolidando o Brasileirão Data Lab como uma plataforma completa.

Possíveis evoluções:

- melhorias de observabilidade da automação;
- histórico de execuções e atualizações;
- refinamento dos modelos preditivos;
- novas métricas e análises;
- otimizações de desempenho do frontend;
- code splitting do bundle React;
- aprimoramento da experiência mobile;
- novas visualizações de probabilidades;
- comparação histórica entre temporadas;
- consolidação da documentação e experiência final do produto.

---

## 💡 Objetivo

Além da análise esportiva, o projeto funciona como laboratório para aplicação prática de:

- Engenharia de Software;
- Engenharia de Dados;
- APIs REST;
- bancos de dados;
- desenvolvimento frontend;
- testes automatizados;
- CI/CD;
- deploy em nuvem;
- automação;
- Machine Learning;
- avaliação probabilística;
- simulação Monte Carlo;
- visualização de dados.

---

## 👨‍💻 Autor

**Carlos Eduardo Pacheco**

Desenvolvedor Python e estudante de Análise e Desenvolvimento de Sistemas.

GitHub: [@cadupacheco](https://github.com/cadupacheco)

---

<p align="center">
  ⚽ Dados, código, probabilidade e futebol no mesmo campo.
</p>