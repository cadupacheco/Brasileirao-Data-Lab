# ⚽ Brasileirão Data Lab

Projeto em Python para coleta, análise e visualização de dados do Campeonato Brasileiro.

A ideia é construir o projeto em etapas, começando com um Web Scraper para coleta de dados, evoluindo para análises estatísticas, dashboard interativo e, futuramente, modelos de Machine Learning para previsão de partidas e simulação da classificação final do campeonato.

## 🎯 Objetivo

Criar uma plataforma de análise do Brasileirão capaz de

 Coletar dados automaticamente através de Web Scraping e APIs;
 Armazenar e tratar os dados das partidas;
 Gerar estatísticas dos clubes e do campeonato;
 Criar visualizações e dashboards interativos;
 Calcular rankings de força dos times;
 Prever probabilidades de resultados;
 Simular possíveis classificações finais do campeonato.

## 🛠️ Tecnologias planejadas

 Python
 Pandas
 BeautifulSoup
 Selenium  Playwright
 SQLite  PostgreSQL
 Streamlit
 Matplotlib  Plotly
 Scikit-learn
 FastAPI

## 🚧 Fase atual

### V0.1 - Coleta de Dados

Primeira etapa do projeto

 [ ] Estruturar o projeto
 [ ] Desenvolver Web Scraper
 [ ] Coletar classificação do Brasileirão
 [ ] Coletar partidas e resultados
 [ ] Normalizar os dados
 [ ] Exportar dados para CSV
 [ ] Criar pipeline de atualização

Dados iniciais planejados

```text
data
├── raw
├── processed
│   ├── matches.csv
│   └── standings.csv
```

## 🗺️ Roadmap

```text
V0.1  Web Scraper
 ↓
V0.2  Análise com Pandas
 ↓
V0.3  Banco de Dados
 ↓
V0.4  Dashboard Streamlit
 ↓
V0.5  Integração com APIs
 ↓
V0.6  Elo Rating
 ↓
V0.7  Previsão de Partidas
 ↓
V0.8  Simulação Monte Carlo
 ↓
V1.0  Plataforma completa
 ↓
V2.0  API com FastAPI
 ↓
V3.0  Aplicativo
```

## 📂 Estrutura inicial

```text
brasileirao-data-lab
│
├── src
│   ├── scrapers
│   ├── database
│   ├── analytics
│   ├── ml
│   └── pipelines
│
├── data
│   ├── raw
│   └── processed
│
├── notebooks
├── tests
│
├── .gitignore
├── requirements.txt
└── README.md
```

---

Projeto em desenvolvimento. ⚽🐍
