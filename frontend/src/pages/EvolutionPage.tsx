import {
  Activity,
  BarChart3,
  CircleDot,
  Trophy,
} from "lucide-react";

import {
  useEffect,
  useMemo,
  useState,
} from "react";

import {
  CartesianGrid,
  Legend,
  Line,
  LineChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";

import {
  getChampionshipSummary,
  getEvolution,
  getStandings,
} from "../api";

import type {
  ChampionshipSummary,
  EvolutionPoint,
  Standing,
} from "../api";


type EvolutionMetric =
  | "position"
  | "points";


const CHART_COLORS = [
  "#27d684",
  "#5aa9ff",
  "#f5c451",
  "#ff7078",
  "#b08cff",
  "#ff9f5a",
  "#4dd0e1",
  "#ec70ff",
  "#8bc34a",
  "#ffca28",
  "#26c6da",
  "#ef5350",
  "#7e57c2",
  "#66bb6a",
  "#ffa726",
  "#42a5f5",
  "#ab47bc",
  "#d4e157",
  "#26a69a",
  "#ff7043",
];


function EvolutionPage() {
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
    evolution,
    setEvolution,
  ] = useState<EvolutionPoint[]>([]);

  const [
    selectedTeamIds,
    setSelectedTeamIds,
  ] = useState<number[]>([]);

  const [
    metric,
    setMetric,
  ] = useState<EvolutionMetric>(
    "position",
  );

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
      async function loadPage() {
        try {
          setLoading(true);
          setError(null);

          const [
            summaryData,
            standingsData,
            evolutionData,
          ] = await Promise.all([
            getChampionshipSummary(),
            getStandings(),
            getEvolution(),
          ]);

          setSummary(
            summaryData,
          );

          setStandings(
            standingsData,
          );

          setEvolution(
            evolutionData,
          );

          setSelectedTeamIds(
            standingsData
              .slice(
                0,
                5,
              )
              .map(
                (
                  team,
                ) =>
                  team.team_id,
              ),
          );
        } catch (
          requestError
        ) {
          console.error(
            requestError,
          );

          setError(
            "Não foi possível carregar a evolução do campeonato.",
          );
        } finally {
          setLoading(false);
        }
      }

      loadPage();
    },
    [],
  );


  const selectedTeams =
    useMemo(
      () =>
        standings.filter(
          (
            team,
          ) =>
            selectedTeamIds.includes(
              team.team_id,
            ),
        ),
      [
        standings,
        selectedTeamIds,
      ],
    );


  const chartData =
    useMemo(
      () => {
        const rounds =
          new Map<
            number,
            Record<
              string,
              string | number
            >
          >();

        evolution
          .filter(
            (
              point,
            ) =>
              selectedTeamIds.includes(
                point.team_id,
              ),
          )
          .forEach(
            (
              point,
            ) => {
              const current =
                rounds.get(
                  point.round,
                )
                ?? {
                  round:
                    point.round,
                };

              current[
                String(
                  point.team_id,
                )
              ] =
                metric
                === "position"
                  ? point.position
                  : point.points;

              rounds.set(
                point.round,
                current,
              );
            },
          );

        return Array.from(
          rounds.values(),
        ).sort(
          (
            first,
            second,
          ) =>
            Number(
              first.round,
            )
            - Number(
              second.round,
            ),
        );
      },
      [
        evolution,
        selectedTeamIds,
        metric,
      ],
    );


  function toggleTeam(
    teamId: number,
  ) {
    const isSelected =
      selectedTeamIds.includes(
        teamId,
      );

    if (isSelected) {
      if (
        selectedTeamIds.length
        === 1
      ) {
        return;
      }

      setSelectedTeamIds(
        selectedTeamIds.filter(
          (
            selectedId,
          ) =>
            selectedId
            !== teamId,
        ),
      );

      return;
    }

    setSelectedTeamIds([
      ...selectedTeamIds,
      teamId,
    ]);
  }


  function selectAllTeams() {
    setSelectedTeamIds(
      standings.map(
        (
          team,
        ) =>
          team.team_id,
      ),
    );
  }


  function selectTopFive() {
    setSelectedTeamIds(
      standings
        .slice(
          0,
          5,
        )
        .map(
          (
            team,
          ) =>
            team.team_id,
        ),
    );
  }


  if (loading) {
    return (
      <div className="panel">
        <div className="panel-header">
          <div className="panel-icon">
            <Activity size={19} />
          </div>

          <div>
            <h2>
              Carregando evolução...
            </h2>

            <p>
              Consultando o histórico
              rodada a rodada.
            </p>
          </div>
        </div>
      </div>
    );
  }


  if (
    error
    || !summary
  ) {
    return (
      <div className="panel">
        <div className="panel-header">
          <div className="panel-icon">
            <Activity size={19} />
          </div>

          <div>
            <h2>
              Erro ao carregar
            </h2>

            <p>
              {error}
            </p>
          </div>
        </div>
      </div>
    );
  }


  return (
    <>
      <header className="page-header">
        <div>
          <span className="eyebrow">
            CAMPEONATO BRASILEIRO
          </span>

          <h1>
            Evolução
          </h1>

          <p>
            Acompanhe a trajetória
            dos clubes rodada a rodada
            na Série A {summary.season}.
          </p>
        </div>

        <div className="round-badge">
          <BarChart3 size={17} />

          Até a rodada{" "}
          {
            summary.latest_played_round
            ?? "-"
          }
        </div>
      </header>


      <section className="evolution-toolbar">
        <div>
          <span className="toolbar-label">
            Métrica
          </span>

          <div className="metric-switch">
            <button
              className={
                metric
                === "position"
                  ? "metric-button active"
                  : "metric-button"
              }
              onClick={
                () =>
                  setMetric(
                    "position",
                  )
              }
            >
              <Trophy size={15} />
              Posição
            </button>

            <button
              className={
                metric
                === "points"
                  ? "metric-button active"
                  : "metric-button"
              }
              onClick={
                () =>
                  setMetric(
                    "points",
                  )
              }
            >
              <CircleDot size={15} />
              Pontos
            </button>

            <button
              className="metric-button"
              onClick={
                selectTopFive
              }
            >
              Top 5
            </button>

            <button
              className="metric-button"
              onClick={
                selectAllTeams
              }
            >
              Todos
            </button>
          </div>
        </div>


        <div className="evolution-selection-info">
          <strong>
            {
              selectedTeamIds.length
            }/
            {
              standings.length
            }
          </strong>

          <span>
            clubes selecionados
          </span>
        </div>
      </section>


      <section className="club-selector">
        {
          standings.map(
            (
              team,
            ) => {
              const isSelected =
                selectedTeamIds.includes(
                  team.team_id,
                );

              return (
                <button
                  key={
                    team.team_id
                  }
                  className={
                    isSelected
                      ? "club-chip active"
                      : "club-chip"
                  }
                  onClick={
                    () =>
                      toggleTeam(
                        team.team_id,
                      )
                  }
                >
                  <span>
                    {
                      team.position
                    }º
                  </span>

                  {
                    team.team
                  }
                </button>
              );
            },
          )
        }
      </section>


      <section className="panel evolution-panel">
        <div className="panel-header">
          <div className="panel-icon">
            <BarChart3 size={19} />
          </div>

          <div>
            <h2>
              {
                metric
                === "position"
                  ? "Evolução da posição"
                  : "Evolução dos pontos"
              }
            </h2>

            <p>
              {
                metric
                === "position"
                  ? "Quanto menor o número, melhor a colocação."
                  : "Pontuação acumulada ao longo das rodadas."
              }
            </p>
          </div>
        </div>


        <div className="evolution-chart">
          <ResponsiveContainer
            width="100%"
            height={460}
          >
            <LineChart
              data={
                chartData
              }
              margin={{
                top: 24,
                right: 28,
                left: 0,
                bottom: 10,
              }}
            >
              <CartesianGrid
                strokeDasharray="3 3"
                stroke="#1f2a2f"
                vertical={false}
              />

              <XAxis
                dataKey="round"
                stroke="#65736c"
                tickLine={false}
                axisLine={false}
              />

              <YAxis
                stroke="#65736c"
                tickLine={false}
                axisLine={false}
                allowDecimals={false}
                reversed={
                  metric
                  === "position"
                }
                domain={
                  metric
                  === "position"
                    ? [1, 20]
                    : [
                        0,
                        "auto",
                      ]
                }
              />

              <Tooltip
                contentStyle={{
                  background:
                    "#11181d",
                  border:
                    "1px solid #263038",
                  borderRadius:
                    "10px",
                }}
                labelStyle={{
                  color:
                    "#dfe7e3",
                }}
              />

              <Legend />

              {
                selectedTeams.map(
                  (
                    team,
                    index,
                  ) => (
                    <Line
                      key={
                        team.team_id
                      }
                      type="monotone"
                      dataKey={
                        String(
                          team.team_id,
                        )
                      }
                      name={
                        team.team
                      }
                      stroke={
                        CHART_COLORS[
                          index
                          % CHART_COLORS.length
                        ]
                      }
                      strokeWidth={2.5}
                      dot={{
                        r: 2.5,
                      }}
                      activeDot={{
                        r: 5,
                      }}
                      connectNulls
                    />
                  ),
                )
              }
            </LineChart>
          </ResponsiveContainer>
        </div>
      </section>


      <section className="evolution-summary">
        {
          selectedTeams.map(
            (
              team,
              index,
            ) => (
              <article
                className="evolution-stat-card"
                key={
                  team.team_id
                }
              >
                <div
                  className="evolution-color-dot"
                  style={{
                    background:
                      CHART_COLORS[
                        index
                        % CHART_COLORS.length
                      ],
                  }}
                />

                <div>
                  <span>
                    {
                      team.position
                    }º lugar
                  </span>

                  <strong>
                    {
                      team.team
                    }
                  </strong>

                  <small>
                    {
                      team.points
                    } pontos
                  </small>
                </div>
              </article>
            ),
          )
        }
      </section>
    </>
  );
}


export default EvolutionPage;