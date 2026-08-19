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
  <img src="https://img.shields.io/badge/version-v0.6.0-27d684" alt="Version v0.6.0" />
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

A evolução acontece em etapas versionadas, partindo da coleta de dados e avançando por analytics, banco de dados, API, frontend, deploy e modelos preditivos.

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
            Web Scraping
                  │
                  ▼
       Processamento e Validação
                  │
          ┌───────┴────────┐
          ▼                ▼
       SQLite         Dataset histórico
          │                │
          ▼                ▼
      Analytics       Feature Engineering
          │                │
          │                ▼
          │          Random Forest
          │                │
          │        ┌───────┴────────┐
          │        ▼                ▼
          │   Prob. por jogo    Monte Carlo
          │        │                │
          └────────┴───────┬────────┘
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

O projeto é dividido em quatro grandes camadas:

**Data Layer**

Responsável pela coleta, tratamento, validação, analytics e persistência dos dados.

**Machine Learning**

Responsável pelo dataset histórico, feature engineering, Elo, confrontos diretos, treinamento, avaliação, probabilidades de partidas e simulação do campeonato.

**Backend**

API REST construída com FastAPI, responsável por disponibilizar os dados processados e previsões.

**Frontend**

Dashboard desenvolvido em React + TypeScript para visualização e exploração dos dados e projeções do campeonato.

---

## 🤖 Machine Learning

A `v0.6.0` adiciona o primeiro motor preditivo do projeto.

### Dataset histórico

Foram coletadas as temporadas de **2021 a 2026**, totalizando:

- 2.280 partidas no histórico;
- 2.125 partidas disputadas;
- 155 partidas futuras no snapshot utilizado pela versão.

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

O **Random Forest** apresentou o melhor resultado agregado e foi escolhido como modelo principal da versão.

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

---

## 🚀 API REST

Principais endpoints:

```text
GET /api/health
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

---

## 🔄 CI/CD

Desde a `v0.5.0`, o projeto utiliza **GitHub Actions** para validar automaticamente alterações enviadas ao repositório.

A pipeline executa dois jobs independentes:

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
│       └── ci.yml
│
├── data/
│   ├── ml/
│   │   ├── features.csv
│   │   ├── future_predictions.csv
│   │   ├── matches_history.csv
│   │   └── season_simulation.csv
│   ├── processed/
│   └── raw/
│
├── frontend/
│   ├── public/
│   └── src/
│       ├── components/
│       ├── pages/
│       │   └── PredictionsPage.tsx
│       ├── api.ts
│       └── App.tsx
│
├── scripts/
│
├── src/
│   └── brasileirao_data_lab/
│       ├── analytics/
│       ├── api/
│       ├── database/
│       ├── ml/
│       ├── pipelines/
│       ├── scrapers/
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

### 5. Inicie a API

```powershell
uvicorn brasileirao_data_lab.api.app:app --reload --port 8000
```

Swagger local:

```text
http://127.0.0.1:8000/docs
```

### 6. Inicie o frontend

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

Os scripts principais da `v0.6.0` são:

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
| `v0.7` | Atualização automática dos dados | 🔜 Próxima versão |
| `v1.0` | Plataforma completa | 🎯 Objetivo |

---

## 🔮 Próximas evoluções

A próxima grande etapa será a `v0.7`, focada em automatizar a atualização dos dados e manter as previsões sincronizadas com o andamento do campeonato.

Entre os próximos objetivos estão:

- atualização automática dos resultados;
- reconstrução automática das features;
- regeneração automática das probabilidades;
- nova execução das simulações após atualização dos dados;
- atualização automática dos dados servidos pela API e pelo frontend.

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
