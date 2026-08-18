# ⚽ Brasileirão Data Lab

<p align="center">
  Plataforma de dados para coleta, processamento, análise e visualização do Campeonato Brasileiro Série A.
</p>

<p align="center">
  <strong>Python • FastAPI • React • TypeScript • SQLite • Pandas</strong>
</p>

<p align="center">
  <img src="https://img.shields.io/badge/version-v0.4.0-27d684" />
  <img src="https://img.shields.io/badge/Python-3.x-3776AB?logo=python&logoColor=white" />
  <img src="https://img.shields.io/badge/FastAPI-API-009688?logo=fastapi&logoColor=white" />
  <img src="https://img.shields.io/badge/React-TypeScript-61DAFB?logo=react&logoColor=black" />
  <img src="https://img.shields.io/badge/SQLite-Database-003B57?logo=sqlite&logoColor=white" />
</p>

---

## 📌 Sobre o projeto

O **Brasileirão Data Lab** é um projeto de Engenharia e Análise de Dados aplicado ao Campeonato Brasileiro Série A.

A aplicação coleta informações da competição, processa os dados, armazena os resultados em banco de dados e disponibiliza análises através de uma API REST e de um dashboard web interativo.

O objetivo do projeto é construir uma plataforma completa de dados esportivos, evoluindo desde a coleta das informações até modelos de previsão da classificação final do campeonato.

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
 ├───────────────┐
 ▼               ▼
Analytics      FastAPI
                 │
                 ▼
              React
                 │
                 ▼
             Dashboard
```

A aplicação é dividida em três grandes camadas:

**Data Layer**

Responsável pela coleta, tratamento, validação e persistência dos dados.

**Backend**

API REST construída com FastAPI, responsável por disponibilizar os dados processados para outras aplicações.

**Frontend**

Dashboard desenvolvido em React + TypeScript para visualização e exploração dos dados do campeonato.

---

## 📊 Dashboard

Atualmente o dashboard possui cinco áreas principais.

### 🏠 Visão Geral

Resumo do campeonato com informações como:

- líder atual;
- quantidade de partidas realizadas;
- gols marcados;
- média de gols;
- melhor ataque;
- melhor defesa;
- aproveitamento do líder;
- desempenho recente dos clubes;
- distribuição de vitórias e empates.

### 🏆 Classificação

Tabela completa da Série A contendo:

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

Visão individual dos 20 clubes participantes da competição, apresentando seus principais indicadores.

### 📈 Evolução

Visualização da trajetória dos clubes rodada a rodada.

É possível selecionar qualquer combinação entre os 20 clubes e analisar:

- evolução da posição;
- evolução da pontuação.

### 📅 Jogos

Consulta das partidas do campeonato com filtros por:

- rodada;
- clube;
- jogos realizados;
- próximos jogos.

As partidas exibem informações como placar, data, horário e local quando disponíveis.

---

## 🚀 API REST

O backend utiliza **FastAPI**.

Após iniciar a aplicação, a documentação interativa pode ser acessada em:

```text
http://127.0.0.1:8000/docs
```

Principais endpoints disponíveis:

```text
GET /api/health

GET /api/championship/summary

GET /api/standings

GET /api/recent-form

GET /api/evolution

GET /api/matches
```

Os endpoints permitem acessar informações consolidadas do campeonato, classificação, desempenho recente, evolução dos clubes e partidas.

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

### Qualidade

- Pytest
- Git
- GitHub

---

## 📁 Estrutura do projeto

```text
Brasileirao-Data-Lab/
│
├── data/
│   ├── processed/
│   └── raw/
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

## ⚙️ Executando o projeto

### 1. Clone o repositório

```bash
git clone https://github.com/cadupacheco/Brasileirao-Data-Lab.git
```

Entre na pasta:

```bash
cd Brasileirao-Data-Lab
```

---

### 2. Crie o ambiente virtual

No Windows:

```powershell
python -m venv .venv
```

Ative:

```powershell
.\.venv\Scripts\Activate.ps1
```

---

### 3. Instale as dependências Python

```powershell
pip install -r requirements.txt
```

---

### 4. Execute o pipeline de dados

```powershell
python main.py
```

O pipeline realiza a coleta e o processamento dos dados necessários para a aplicação.

---

### 5. Inicie a API

```powershell
uvicorn brasileirao_data_lab.api.app:app --reload --port 8000
```

Swagger:

```text
http://127.0.0.1:8000/docs
```

---

### 6. Instale as dependências do frontend

Em outro terminal:

```powershell
cd frontend
npm install
```

---

### 7. Inicie o frontend

```powershell
npm run dev
```

A aplicação ficará disponível em:

```text
http://localhost:5173
```

---

## 🧪 Testes

A aplicação possui testes automatizados para diferentes camadas do projeto.

Para executar:

```powershell
pytest -q
```

Estado atual da versão `v0.4.0`:

```text
123 passed
```

---

## 🗺️ Roadmap

| Versão | Objetivo | Status |
|---|---|---|
| `v0.1` | Coleta de dados | ✅ Concluído |
| `v0.2` | Analytics | ✅ Concluído |
| `v0.3` | Banco de dados | ✅ Concluído |
| `v0.4` | FastAPI + React Dashboard | ✅ Concluído |
| `v0.5` | Deploy + CI/CD | 🔜 Próxima versão |
| `v0.6` | Machine Learning e previsões | 📋 Planejado |
| `v0.7` | Atualização automática dos dados | 📋 Planejado |
| `v1.0` | Plataforma completa | 🎯 Objetivo |

---

## 🔮 Próximas evoluções

Entre as próximas funcionalidades planejadas estão:

- publicação do frontend e backend;
- integração contínua com GitHub Actions;
- atualização automática dos dados;
- modelos de Machine Learning;
- previsão da classificação final;
- probabilidade de título;
- probabilidade de classificação para competições continentais;
- probabilidade de rebaixamento;
- simulação das rodadas restantes.

---

## 💡 Objetivo

Além da análise esportiva, o projeto funciona como laboratório para aplicação prática de conceitos de:

- Engenharia de Software;
- Engenharia de Dados;
- APIs REST;
- bancos de dados;
- desenvolvimento frontend;
- testes automatizados;
- CI/CD;
- Machine Learning;
- visualização de dados.

A ideia é continuar evoluindo o projeto incrementalmente, mantendo cada grande etapa versionada no Git.

---

## 👨‍💻 Autor

**Carlos Eduardo Pacheco**

Desenvolvedor Python e estudante de Análise e Desenvolvimento de Sistemas.

GitHub: [@cadupacheco](https://github.com/cadupacheco)

---

<p align="center">
  ⚽ Dados, código e futebol no mesmo campo.
</p>
