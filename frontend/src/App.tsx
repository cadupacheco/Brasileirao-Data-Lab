import {
  Activity,
  BarChart3,
  CalendarDays,
  Database,
  Flame,
  Goal,
  Home,
  Medal,
  Shield,
  Trophy,
} from "lucide-react";

import {
  useEffect,
  useState,
} from "react";

import type {
  ReactNode,
} from "react";

import {
  getChampionshipSummary,
  getRecentForm,
  getStandings,
} from "./api";

import type {
  ChampionshipSummary,
  RecentForm,
  Standing,
} from "./api";

import "./App.css";


function App() {
  const [
    summary,
    setSummary,
  ] = useState<ChampionshipSummary | null>(
    null,
  );

  const [
    standings,
    setStandings,
  ] = useState<Standing[]>([]);

  const [
    recentForm,
    setRecentForm,
  ] = useState<RecentForm[]>([]);

  const [
    loading,
    setLoading,
  ] = useState(true);

  const [
    error,
    setError,
  ] = useState<string | null>(
    null,
  );


  useEffect(
    () => {
      async function loadDashboard() {
        try {
          setLoading(true);
          setError(null);

          const [
            summaryData,
            standingsData,
            recentFormData,
          ] = await Promise.all([
            getChampionshipSummary(),
            getStandings(),
            getRecentForm(),
          ]);

          setSummary(
            summaryData,
          );

          setStandings(
            standingsData,
          );

          setRecentForm(
            recentFormData,
          );
        } catch (
          requestError
        ) {
          console.error(
            requestError,
          );

          setError(
            "Não foi possível carregar os dados da API.",
          );
        } finally {
          setLoading(false);
        }
      }

      loadDashboard();
    },
    [],
  );


  if (loading) {
    return (
      <div className="state-screen">
        <div className="loader" />

        <h2>
          Carregando Brasileirão...
        </h2>

        <p>
          Consultando FastAPI e SQLite.
        </p>
      </div>
    );
  }


  if (
    error
    || !summary
  ) {
    return (
      <div className="state-screen">
        <Activity size={40} />

        <h2>
          API indisponível
        </h2>

        <p>
          {error}
        </p>

        <small>
          Verifique se o FastAPI está
          rodando na porta 8000.
        </small>
      </div>
    );
  }


  const leader =
    summary.leader;

  const bestAttack =
    [...standings]
      .sort(
        (
          first,
          second,
        ) =>
          second.goals_for
          - first.goals_for,
      )[0];

  const bestDefense =
    [...standings]
      .sort(
        (
          first,
          second,
        ) =>
          first.goals_against
          - second.goals_against,
      )[0];

  const hottestTeam =
    recentForm[0];


  return (
    <div className="app-shell">
      <aside className="sidebar">
        <div className="brand">
          <div className="brand-icon">
            <Goal size={24} />
          </div>

          <div>
            <strong>
              Brasileirão
            </strong>

            <span>
              Data Lab
            </span>
          </div>
        </div>


        <nav className="nav">
          <button
            className="nav-item active"
          >
            <Home size={18} />
            Visão Geral
          </button>

          <button
            className="nav-item"
          >
            <Trophy size={18} />
            Classificação
          </button>

          <button
            className="nav-item"
          >
            <Shield size={18} />
            Clubes
          </button>

          <button
            className="nav-item"
          >
            <BarChart3 size={18} />
            Evolução
          </button>

          <button
            className="nav-item"
          >
            <CalendarDays size={18} />
            Jogos
          </button>
        </nav>


        <div className="sidebar-footer">
          <Database size={17} />

          <div>
            <strong>
              SQLite
            </strong>

            <span>
              Fonte principal
            </span>
          </div>
        </div>
      </aside>


      <main className="content">
        <header className="page-header">
          <div>
            <span className="eyebrow">
              CAMPEONATO BRASILEIRO
            </span>

            <h1>
              Série A {summary.season}
            </h1>

            <p>
              Dados processados pelo
              Brasileirão Data Lab.
            </p>
          </div>

          <div className="round-badge">
            <Activity size={17} />

            Rodada{" "}
            {
              summary.latest_played_round
              ?? "-"
            }
          </div>
        </header>


        <section className="metric-grid">
          <MetricCard
            label="Líder"
            value={
              leader?.team
              ?? "-"
            }
            detail={
              leader
                ? `${leader.points} pontos`
                : "Sem dados"
            }
            icon={
              <Trophy size={21} />
            }
          />

          <MetricCard
            label="Jogos realizados"
            value={
              String(
                summary.played_matches,
              )
            }
            detail={
              `${summary.future_matches} restantes`
            }
            icon={
              <CalendarDays size={21} />
            }
          />

          <MetricCard
            label="Gols marcados"
            value={
              String(
                summary.total_goals,
              )
            }
            detail={
              `${summary.average_goals_per_match.toFixed(
                2,
              )} por jogo`
            }
            icon={
              <Goal size={21} />
            }
          />

          <MetricCard
            label="Melhor momento"
            value={
              hottestTeam?.team
              ?? "-"
            }
            detail={
              hottestTeam
                ? `${hottestTeam.points}/15 pontos`
                : "Sem dados"
            }
            icon={
              <Flame size={21} />
            }
          />
        </section>


        <section className="highlight-grid">
          <HighlightCard
            title="Melhor ataque"
            value={
              bestAttack?.team
              ?? "-"
            }
            detail={
              bestAttack
                ? `${bestAttack.goals_for} gols marcados`
                : "Sem dados"
            }
            icon={
              <Goal size={20} />
            }
          />

          <HighlightCard
            title="Melhor defesa"
            value={
              bestDefense?.team
              ?? "-"
            }
            detail={
              bestDefense
                ? `${bestDefense.goals_against} gols sofridos`
                : "Sem dados"
            }
            icon={
              <Shield size={20} />
            }
          />

          <HighlightCard
            title="Aproveitamento do líder"
            value={
              standings[0]
                ? `${standings[0].performance_pct.toFixed(
                    2,
                  )}%`
                : "-"
            }
            detail={
              standings[0]
                ? `${standings[0].matches} partidas`
                : "Sem dados"
            }
            icon={
              <Medal size={20} />
            }
          />
        </section>


        <section className="dashboard-grid">
          <div className="panel">
            <PanelHeader
              title="Classificação"
              subtitle="Tabela atual do campeonato"
              icon={
                <Trophy size={19} />
              }
            />

            <div className="table-wrapper">
              <table>
                <thead>
                  <tr>
                    <th>Pos</th>
                    <th>Clube</th>
                    <th>J</th>
                    <th>V</th>
                    <th>E</th>
                    <th>D</th>
                    <th>SG</th>
                    <th>PTS</th>
                  </tr>
                </thead>

                <tbody>
                  {
                    standings.map(
                      (
                        team,
                      ) => (
                        <tr
                          key={
                            team.team_id
                          }
                        >
                          <td>
                            <PositionBadge
                              position={
                                team.position
                              }
                            />
                          </td>

                          <td className="team-name">
                            {
                              team.team
                            }
                          </td>

                          <td>
                            {
                              team.matches
                            }
                          </td>

                          <td>
                            {
                              team.wins
                            }
                          </td>

                          <td>
                            {
                              team.draws
                            }
                          </td>

                          <td>
                            {
                              team.losses
                            }
                          </td>

                          <td>
                            {
                              team.goal_difference
                              > 0
                                ? `+${team.goal_difference}`
                                : team.goal_difference
                            }
                          </td>

                          <td className="points">
                            {
                              team.points
                            }
                          </td>
                        </tr>
                      ),
                    )
                  }
                </tbody>
              </table>
            </div>
          </div>


          <div className="side-column">
            <div className="panel">
              <PanelHeader
                title="Melhor momento"
                subtitle="Últimos 5 jogos"
                icon={
                  <Flame size={19} />
                }
              />

              <div className="form-list">
                {
                  recentForm
                    .slice(
                      0,
                      6,
                    )
                    .map(
                      (
                        team,
                      ) => (
                        <div
                          className="form-row"
                          key={
                            team.team_id
                          }
                        >
                          <div className="form-team">
                            <span>
                              {
                                team.position
                              }º
                            </span>

                            <strong>
                              {
                                team.team
                              }
                            </strong>
                          </div>

                          <FormSequence
                            form={
                              team.form
                            }
                          />

                          <b>
                            {
                              team.points
                            }
                          </b>
                        </div>
                      ),
                    )
                }
              </div>
            </div>


            <div className="panel results-panel">
              <PanelHeader
                title="Resultados gerais"
                subtitle="Distribuição das partidas"
                icon={
                  <Activity size={19} />
                }
              />

              <ResultBar
                label="Mandantes"
                value={
                  summary.home_wins
                }
                total={
                  summary.played_matches
                }
              />

              <ResultBar
                label="Empates"
                value={
                  summary.draws
                }
                total={
                  summary.played_matches
                }
              />

              <ResultBar
                label="Visitantes"
                value={
                  summary.away_wins
                }
                total={
                  summary.played_matches
                }
              />
            </div>
          </div>
        </section>
      </main>
    </div>
  );
}


interface MetricCardProps {
  label: string;
  value: string;
  detail: string;
  icon: ReactNode;
}


function MetricCard({
  label,
  value,
  detail,
  icon,
}: MetricCardProps) {
  return (
    <article className="metric-card">
      <div className="metric-card-header">
        <span>
          {label}
        </span>

        <div className="card-icon">
          {icon}
        </div>
      </div>

      <strong>
        {value}
      </strong>

      <small>
        {detail}
      </small>
    </article>
  );
}


interface HighlightCardProps {
  title: string;
  value: string;
  detail: string;
  icon: ReactNode;
}


function HighlightCard({
  title,
  value,
  detail,
  icon,
}: HighlightCardProps) {
  return (
    <article className="highlight-card">
      <div className="highlight-icon">
        {icon}
      </div>

      <div>
        <span>
          {title}
        </span>

        <strong>
          {value}
        </strong>

        <small>
          {detail}
        </small>
      </div>
    </article>
  );
}


interface PanelHeaderProps {
  title: string;
  subtitle: string;
  icon: ReactNode;
}


function PanelHeader({
  title,
  subtitle,
  icon,
}: PanelHeaderProps) {
  return (
    <div className="panel-header">
      <div className="panel-icon">
        {icon}
      </div>

      <div>
        <h2>
          {title}
        </h2>

        <p>
          {subtitle}
        </p>
      </div>
    </div>
  );
}


function PositionBadge({
  position,
}: {
  position: number;
}) {
  let className =
    "position";

  if (position <= 4) {
    className += " champions";
  } else if (
    position <= 6
  ) {
    className += " continental";
  } else if (
    position >= 17
  ) {
    className += " relegation";
  }

  return (
    <span className={className}>
      {position}
    </span>
  );
}


function FormSequence({
  form,
}: {
  form: string;
}) {
  const results =
    form
      .split(" ")
      .filter(Boolean);

  return (
    <div className="form-sequence">
      {
        results.map(
          (
            result,
            index,
          ) => (
            <span
              key={
                `${result}-${index}`
              }
              className={
                `form-result ${result.toLowerCase()}`
              }
            >
              {result}
            </span>
          ),
        )
      }
    </div>
  );
}


interface ResultBarProps {
  label: string;
  value: number;
  total: number;
}


function ResultBar({
  label,
  value,
  total,
}: ResultBarProps) {
  const percentage =
    total > 0
      ? (
          value
          / total
        ) * 100
      : 0;

  return (
    <div className="result-item">
      <div className="result-label">
        <span>
          {label}
        </span>

        <strong>
          {value}
        </strong>
      </div>

      <div className="progress-track">
        <div
          className="progress-fill"
          style={{
            width: `${percentage}%`,
          }}
        />
      </div>

      <small>
        {percentage.toFixed(
          1,
        )}%
      </small>
    </div>
  );
}


export default App;