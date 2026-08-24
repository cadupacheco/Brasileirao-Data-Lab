# ⚽ Brasileirão Data Lab

<p align="center">
  Plataforma completa de dados, analytics, Machine Learning e visualização do Campeonato Brasileiro Série A.
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
  <img src="https://img.shields.io/badge/version-v1.0.0-27d684" alt="Version v1.0.0" />
</p>

<p align="center">
  <a href="https://brasileirao-data-lab.vercel.app"><strong>🌐 Acessar aplicação</strong></a>
  •
  <a href="https://brasileirao-data-lab-api.onrender.com/docs"><strong>📚 Swagger da API</strong></a>
</p>

---

## 📌 Sobre o projeto

O **Brasileirão Data Lab** é uma plataforma criada para transformar dados do Campeonato Brasileiro Série A em informações exploráveis, análises estatísticas e projeções probabilísticas.

O projeto percorre uma cadeia completa:

```text
Coleta
  ↓
Validação
  ↓
Processamento
  ↓
Banco de dados
  ↓
Analytics
  ↓
Machine Learning
  ↓
API REST
  ↓
Dashboard React
  ↓
Deploy
  ↓
Atualização automática
```

A aplicação acompanha a temporada atual utilizando dados da CBF e disponibiliza informações sobre classificação, partidas, clubes, jogadores, evolução rodada a rodada, comparação entre equipes e previsões geradas por Machine Learning.

A `v1.0.0` consolida todas as etapas anteriores em uma plataforma única e responsiva.

---

# 🌐 Aplicação em produção

## Dashboard

**https://brasileirao-data-lab.vercel.app**

Frontend desenvolvido com React, TypeScript, Vite, React Router, Recharts e Lucide React.

Deploy realizado na **Vercel**.

## API

**https://brasileirao-data-lab-api.onrender.com**

Swagger:

**https://brasileirao-data-lab-api.onrender.com/docs**

Backend desenvolvido com **FastAPI** e publicado no **Render**.

---

# 🏗️ Arquitetura

```text
                               CBF
                                │
                                ▼
                    Verificações automáticas
                       GitHub Actions
                                │
                                ▼
                         Coleta de dados
                                │
                                ▼
                      Detecção de mudanças
                                │
                   ┌────────────┴────────────┐
                   │                         │
                   ▼                         ▼
            Nenhuma mudança             Há mudança
                   │                         │
                   ▼                         ▼
                Finaliza              Validação do
              sem rebuild              novo estado
                                             │
                                             ▼
                                  Atualização dos dados
                                             │
                    ┌────────────────────────┼────────────────────────┐
                    │                        │                        │
                    ▼                        ▼                        ▼
                  SQLite                  Analytics              Histórico ML
                    │                        │                        │
                    │                        │                        ▼
                    │                        │               Feature Engineering
                    │                        │                        │
                    │                        │                        ▼
                    │                        │                Random Forest
                    │                        │                        │
                    │                        │              ┌─────────┴─────────┐
                    │                        │              ▼                   ▼
                    │                        │        Prob. por jogo        Monte Carlo
                    │                        │              │                   │
                    └────────────────────────┴──────────────┴──────────┬────────┘
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

---

# 🧱 Camadas do projeto

## Data Layer

Responsável por coleta, parsing, normalização, validação, armazenamento e atualização dos dados da competição.

## Analytics

Responsável por classificação calculada, forma recente, desempenho como mandante e visitante, evolução rodada a rodada, comparação entre clubes e confronto direto.

## Machine Learning

Responsável por construção do dataset histórico, feature engineering, Elo Rating, confrontos diretos, treinamento, backtests, probabilidades e simulação do campeonato.

## Backend

API REST em FastAPI que entrega dados processados para o frontend.

## Frontend

Dashboard React + TypeScript para exploração visual dos dados.

## Automação

GitHub Actions verifica periodicamente a CBF e reconstrói os artefatos quando alterações reais são detectadas.

---

# 📊 Dashboard

A `v1.0.0` possui as seguintes áreas.

## 🏠 Visão Geral

Resumo da temporada com líder, partidas realizadas e restantes, gols, média de gols, melhor ataque, melhor defesa, melhor momento, classificação, forma recente e distribuição dos resultados.

## 🏆 Classificação

Tabela completa da Série A com posição, jogos, vitórias, empates, derrotas, gols pró, gols contra, saldo de gols, aproveitamento e pontos.

## 🛡️ Clubes

Visão dos 20 participantes da Série A. Cada card apresenta indicadores principais da campanha e permite acessar a página individual da equipe.

## 🔎 Página individual do clube

Cada clube possui uma página própria com informações organizadas em abas, incluindo posição atual, pontos, campanha, gols, aproveitamento, desempenho recente, jogos, estatísticas e jogadores.

## 👥 Jogadores

A aplicação mantém jogadores associados aos clubes na competição. Para cada jogador disponível são exibidos nome, idade quando disponível, clube, partidas, gols, cartões amarelos e vermelhos.

As estatísticas são associadas ao jogador, clube, temporada e competição, permitindo manter corretamente casos de transferência durante a temporada.

## ⚔️ Comparação de Clubes

A página de comparação permite colocar duas equipes frente a frente.

São analisados posição, pontos, vitórias, gols marcados, gols sofridos, saldo, aproveitamento, aproveitamento em casa, aproveitamento fora, forma recente e confronto direto.

O backend determina automaticamente qual clube possui vantagem em cada indicador. Também é possível inverter rapidamente os dois clubes selecionados.

## 📈 Evolução

Visualização rodada a rodada da trajetória dos clubes, com alternância entre posição e pontos e seleção de diferentes equipes para comparação no gráfico.

## 📅 Jogos

Consulta das partidas da competição com filtros por rodada, clube, realizadas e próximas partidas.

São exibidos mandante, visitante, placar, data, horário, estádio e localização. Partidas futuras também podem utilizar as probabilidades produzidas pelo modelo.

## 🤖 Previsões

Painel de Machine Learning com classificação projetada, pontos esperados, posição média, chance de título, chance de G4, chance de Top 6, risco de rebaixamento, corrida pelo título e ranking de risco de rebaixamento.

As probabilidades são baseadas em simulações do restante da competição.

## 📡 Estado dos dados

O dashboard exibe última sincronização, fonte, quantidade de jogos realizados, jogos futuros e estado da atualização automática.

---

# 🤖 Machine Learning

O motor preditivo utiliza histórico recente do Campeonato Brasileiro para estimar probabilidades.

## Dataset histórico

O pipeline utiliza temporadas entre 2021 e 2026.

## Feature engineering

Entre os sinais utilizados estão pontos por jogo, saldo de gols por jogo, forma recente, desempenho como mandante e visitante, médias recentes de gols, Elo Rating, vantagem de mando, confrontos diretos e forma recente no confronto.

As features são reconstruídas cronologicamente para evitar vazamento de informação.

## Modelos avaliados

Foram comparados Logistic Regression multinomial, Random Forest e Gradient Boosting.

A avaliação utiliza backtests temporais com Log Loss, Brier Score e Accuracy.

O **Random Forest** foi selecionado como modelo principal.

## 🎲 Monte Carlo

Após gerar as probabilidades dos jogos restantes, o campeonato é simulado **10.000 vezes**.

As simulações produzem posição projetada, pontos esperados, posição média, probabilidade de título, G4, Top 6 e rebaixamento.

As simulações utilizam seed fixa para permitir reprodutibilidade.

---

# 🚀 API REST

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
GET /api/clubs/{team_id}/players
GET /api/clubs/compare
```

Exemplo de comparação:

```text
GET /api/clubs/compare?team_a=20002&team_b=20016
```

Exemplo de jogadores:

```text
GET /api/clubs/20002/players
```

Exemplo de previsões:

```text
GET /api/predictions/matches?round_number=24
```

---

# 🔄 Atualização automática

O Brasileirão Data Lab não depende de datas fixas de partidas.

A estratégia utilizada é:

> **não agendar jogos, agendar verificações.**

O GitHub Actions consulta periodicamente a CBF para detectar novos resultados, partidas adiadas ou remarcadas, alterações de horário ou estádio e correções em rodadas anteriores.

## Frequência

Atualmente são realizadas quatro verificações por dia, aproximadamente às 08:00, 14:00, 20:00 e 23:59 no horário de Brasília.

## Detecção semântica

O sistema compara partidas individualmente, observando ID, rodada, data, horário, mandante, visitante, gols, estádio, cidade, estado, status e resultado.

Se nenhuma alteração significativa for encontrada, nenhum rebuild é realizado.

## Fluxo sem mudança

```text
CBF
 │
 ▼
Verificação
 │
 ▼
Nenhuma alteração
 │
 ├─ não reconstrói banco
 ├─ não recalcula features
 ├─ não recalcula previsões
 ├─ não executa Monte Carlo
 └─ não cria commit
```

## Fluxo com mudança

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
Atualização
 │
 ├─ partidas
 ├─ SQLite
 ├─ histórico
 ├─ features
 ├─ previsões
 ├─ Monte Carlo
 └─ metadata
 │
 ▼
Testes
 │
 ▼
Commit automático
 │
 ▼
Push
 │
 ▼
Deploy
```

---

# 👥 Preservação dos jogadores

A atualização automática reconstrói atomicamente o banco de partidas.

Na `v1.0.0`, o pipeline também preserva:

```text
players
player_team_competition_stats
```

antes de substituir o SQLite publicado.

Isso impede que uma atualização automática das partidas apague os dados de jogadores já sincronizados.

---

# ✅ Proteção do último estado válido

Antes de publicar uma atualização, o sistema valida o novo snapshot.

Entre as verificações estão quantidade esperada de partidas, presença dos clubes, estados válidos, dados essenciais, consistência entre partidas realizadas e futuras, geração dos artefatos de ML e integridade do SQLite.

Em caso de falha, o último estado válido permanece publicado.

---

# 🔄 CI/CD

O projeto utiliza GitHub Actions em dois fluxos principais.

## CI

```text
Push / Pull Request
        │
        ├───────────────┐
        ▼               ▼
     Pytest         React Build
        │               │
        └───────┬───────┘
                ▼
               CI
```

## Atualização automática

```text
Schedule
   │
   ▼
Consulta CBF
   │
   ▼
Mudou?
 │    │
não  sim
 │    │
 ▼    ▼
fim  rebuild
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

O workflow de atualização utiliza runner Windows por compatibilidade com a cadeia SSL utilizada pela fonte.

---

# ⚡ Performance frontend

A `v1.0.0` introduz **route-based code splitting**.

As páginas são carregadas com `React.lazy()` e `Suspense`, evitando enviar todas as páginas do dashboard no bundle inicial.

```text
App
 │
 ├─ Sidebar
 │
 └─ rota atual
      │
      ├─ Overview
      ├─ Clubes
      ├─ Comparação
      ├─ Jogos
      └─ Previsões
```

Cada rota é carregada sob demanda.

---

# 📱 Responsividade

A interface foi preparada para diferentes tamanhos de tela.

No mobile, grids são reorganizados, cards são empilhados, comparação é adaptada para uma coluna, filtros são reorganizados, tabelas extensas utilizam scroll horizontal e o menu é reorganizado para telas menores.

---

# 🛡️ Tratamento de erros

O frontend possui tratamento para loading de rotas, erros de API, estados vazios, falhas inesperadas de renderização e falhas de carregamento de chunks.

Um Error Boundary global impede que uma falha isolada transforme a aplicação inteira em uma tela branca.

---

# 🧰 Tecnologias

## Dados e backend

- Python
- FastAPI
- Pandas
- NumPy
- SciPy
- SQLAlchemy
- SQLite
- Requests
- BeautifulSoup
- lxml

## Machine Learning

- Scikit-learn
- Logistic Regression
- Random Forest
- Gradient Boosting
- Elo Rating
- Backtest temporal
- Log Loss
- Brier Score
- Monte Carlo

## Frontend

- React
- TypeScript
- Vite
- React Router
- Recharts
- Lucide React

## Qualidade e infraestrutura

- Pytest
- Git
- GitHub
- GitHub Actions
- Render
- Vercel

---

# 📁 Estrutura

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
│   ├── processed/
│   ├── raw/
│   ├── brasileirao.db
│   └── update_metadata.json
│
├── frontend/
│   ├── public/
│   └── src/
│       ├── components/
│       ├── pages/
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

# ⚙️ Executando localmente

## 1. Clone

```powershell
git clone https://github.com/cadupacheco/Brasileirao-Data-Lab.git
cd Brasileirao-Data-Lab
```

## 2. Ambiente virtual

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

## 3. Dependências Python

```powershell
pip install -r requirements.txt
pip install -e .
```

## 4. API

```powershell
uvicorn brasileirao_data_lab.api.app:app --reload --port 8000
```

Swagger:

```text
http://127.0.0.1:8000/docs
```

## 5. Frontend

Em outro terminal:

```powershell
cd frontend
npm install
npm run dev
```

Aplicação:

```text
http://localhost:5173
```

---

# 🧪 Testes

Backend:

```powershell
python -m pytest
```

Frontend:

```powershell
npm --prefix frontend run build
```

A release somente é considerada pronta quando os testes e o build passam sem erros.

A suíte atualmente possui **mais de 200 testes automatizados** cobrindo coleta, analytics, banco, API, Machine Learning, pipelines, automação e metadata.

---

# 🗺️ Evolução do projeto

| Versão | Objetivo | Status |
|---|---|---|
| `v0.1` | Coleta de dados | ✅ |
| `v0.2` | Analytics | ✅ |
| `v0.3` | Banco de dados | ✅ |
| `v0.4` | FastAPI + React | ✅ |
| `v0.5` | Deploy + CI/CD | ✅ |
| `v0.6` | Machine Learning | ✅ |
| `v0.7` | Atualização automática | ✅ |
| `v1.0` | Plataforma completa | ✅ |

---

# ✨ Destaques da v1.0.0

A primeira versão estável adiciona e consolida:

- página individual dos clubes;
- jogadores e estatísticas por clube;
- comparação entre clubes;
- confronto direto;
- preservação dos jogadores na atualização automática;
- interface mobile;
- melhoria da página de previsões;
- lazy loading;
- code splitting;
- tratamento global de erros;
- refinamento geral da experiência.

---

# 🔮 Próximas evoluções

Possibilidades para versões futuras:

- suporte ao Brasileirão Série B;
- múltiplas competições;
- novas ligas;
- refinamento dos modelos;
- novas métricas de jogadores;
- novas fontes de dados;
- observabilidade da automação;
- melhorias adicionais de performance;
- novas visualizações analíticas.

A arquitetura já evolui pensando na separação entre:

```text
competição
temporada
clube
jogador
partida
fonte de dados
```

---

# 💡 Objetivo

Além do futebol, o projeto funciona como laboratório prático de Engenharia de Software, Engenharia de Dados, APIs REST, bancos de dados, automação, frontend, testes, CI/CD, cloud, Machine Learning, simulação e visualização de dados.

---

# 👨‍💻 Autor

**Carlos Eduardo Pacheco**

Desenvolvedor Python e estudante de Análise e Desenvolvimento de Sistemas.

GitHub: [@cadupacheco](https://github.com/cadupacheco)

---

<p align="center">
  ⚽ Dados, código, probabilidade e futebol no mesmo campo.
</p>
