# ⚽ Brasileirão Data Lab

<p align="center">
  Plataforma de dados para coleta, processamento, análise e visualização do Campeonato Brasileiro Série A.
</p>

<p align="center">
  <strong>Python • FastAPI • React • TypeScript • SQLite • Pandas</strong>
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
  <img src="https://img.shields.io/badge/version-v0.5.0-27d684" alt="Version v0.5.0" />
</p>

<p align="center">
  <a href="https://brasileirao-data-lab.vercel.app"><strong>🌐 Acessar aplicação</strong></a>
  •
  <a href="https://brasileirao-data-lab-api.onrender.com/docs"><strong>📚 Swagger da API</strong></a>
</p>

---

## 📌 Sobre o projeto

O **Brasileirão Data Lab** é uma plataforma de dados aplicada ao Campeonato Brasileiro Série A.

O projeto coleta informações da competição, processa e valida os dados, persiste os resultados em banco de dados, disponibiliza uma API REST e apresenta as análises em um dashboard web interativo.

A proposta é evoluir o projeto em etapas versionadas, partindo da coleta de dados até chegar a modelos de Machine Learning e previsões da classificação final do campeonato.

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
                 ▼
              SQLite
                 │
        ┌────────┴────────┐
        ▼                 ▼
    Analytics          FastAPI
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

O projeto é dividido em três grandes camadas:

**Data Layer**

Responsável pela coleta, tratamento, validação, analytics e persistência dos dados.

**Backend**

API REST construída com FastAPI, responsável por disponibilizar os dados processados.

**Frontend**

Dashboard desenvolvido em React + TypeScript para visualização e exploração dos dados do campeonato.

---

## 📊 Dashboard

O dashboard possui cinco áreas principais.

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

As partidas apresentam placar, data, horário e local quando disponíveis.

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
```

Exemplos em produção:

```text
https://brasileirao-data-lab-api.onrender.com/api/health
https://brasileirao-data-lab-api.onrender.com/api/standings
https://brasileirao-data-lab-api.onrender.com/api/championship/summary
```

---

## 🔄 CI/CD

A partir da `v0.5.0`, o projeto utiliza **GitHub Actions** para validar automaticamente alterações enviadas ao repositório.

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
- SQLAlchemy
- SQLite
- BeautifulSoup
- Requests
- lxml

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
│   ├── processed/
│   ├── raw/
│   └── brasileirao.db
│
├── frontend/
│   ├── public/
│   └── src/
│       ├── components/
│       ├── pages/
│       ├── api.ts
│       └── App.tsx
│
├── notebooks/
│
├── reports/
│   └── figures/
│
├── scripts/
│
├── src/
│   └── brasileirao_data_lab/
│       ├── analytics/
│       ├── api/
│       ├── database/
│       ├── pipelines/
│       ├── scrapers/
│       └── utils/
│
├── tests/
│   ├── analytics/
│   ├── api/
│   ├── database/
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

## 🧪 Testes

Execute:

```powershell
pytest -q
```

Estado validado da `v0.5.0`:

```text
123 passed
```

Build do frontend:

```powershell
cd frontend
npm run build
```

---

## 🗺️ Roadmap

| Versão | Objetivo | Status |
|---|---|---|
| `v0.1` | Coleta de dados | ✅ Concluído |
| `v0.2` | Analytics | ✅ Concluído |
| `v0.3` | Banco de dados | ✅ Concluído |
| `v0.4` | FastAPI + React Dashboard | ✅ Concluído |
| `v0.5` | Deploy + CI/CD | ✅ Concluído |
| `v0.6` | Machine Learning e previsões | 🔜 Próxima versão |
| `v0.7` | Atualização automática dos dados | 📋 Planejado |
| `v1.0` | Plataforma completa | 🎯 Objetivo |

---

## 🔮 Próximas evoluções

A próxima grande etapa será a `v0.6`, focada em Machine Learning e simulação do campeonato.

Funcionalidades planejadas:

- previsão da classificação final;
- probabilidade de título;
- probabilidade de classificação para competições continentais;
- probabilidade de rebaixamento;
- simulação das partidas restantes;
- comparação entre classificação atual e classificação prevista.

Depois, a `v0.7` será focada em automatizar a atualização dos dados.

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
- visualização de dados.

---

## 👨‍💻 Autor

**Carlos Eduardo Pacheco**

Desenvolvedor Python e estudante de Análise e Desenvolvimento de Sistemas.

GitHub: [@cadupacheco](https://github.com/cadupacheco)

---

<p align="center">
  ⚽ Dados, código e futebol no mesmo campo.
</p>
