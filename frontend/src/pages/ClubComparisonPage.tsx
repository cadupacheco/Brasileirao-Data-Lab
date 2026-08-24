import {
  Activity,
  ArrowLeftRight,
  Flame,
  Goal,
  House,
  Plane,
  Shield,
  Swords,
  Trophy,
} from "lucide-react";

import {
  useEffect,
  useMemo,
  useState,
} from "react";

import {
  getClubComparison,
  getStandings,
} from "../api";

import type {
  ClubComparison,
  ClubComparisonTeam,
  Standing,
} from "../api";

import "./ClubComparisonPage.css";


interface MetricRow {
  key: string;
  label: string;

  format: (
    value: number,
  ) => string;

  getValue: (
    team: ClubComparisonTeam,
  ) => number;
}


const METRIC_ROWS: MetricRow[] = [
  {
    key: "position",
    label: "Posição",
    format: (
      value,
    ) => `${value}º`,
    getValue: (
      team,
    ) => team.position,
  },
  {
    key: "points",
    label: "Pontos",
    format: String,
    getValue: (
      team,
    ) => team.points,
  },
  {
    key: "wins",
    label: "Vitórias",
    format: String,
    getValue: (
      team,
    ) => team.wins,
  },
  {
    key: "goals_for",
    label: "Gols marcados",
    format: String,
    getValue: (
      team,
    ) => team.goals_for,
  },
  {
    key: "goals_against",
    label: "Gols sofridos",
    format: String,
    getValue: (
      team,
    ) => team.goals_against,
  },
  {
    key: "goal_difference",
    label: "Saldo de gols",
    format: formatSignedNumber,
    getValue: (
      team,
    ) => team.goal_difference,
  },
  {
    key: "performance_pct",
    label: "Aproveitamento",
    format: formatPercentage,
    getValue: (
      team,
    ) => team.performance_pct,
  },
  {
    key: "home_performance_pct",
    label: "Aproveitamento em casa",
    format: formatPercentage,
    getValue: (
      team,
    ) => team.home_performance_pct,
  },
  {
    key: "away_performance_pct",
    label: "Aproveitamento fora",
    format: formatPercentage,
    getValue: (
      team,
    ) => team.away_performance_pct,
  },
  {
    key: "recent_points",
    label: "Pontos nos últimos 5",
    format: (
      value,
    ) => `${value}/15`,
    getValue: (
      team,
    ) => team.recent_points,
  },
  {
    key: "recent_goal_difference",
    label: "Saldo nos últimos 5",
    format: formatSignedNumber,
    getValue: (
      team,
    ) => team.recent_goal_difference,
  },
];


function formatPercentage(
  value: number,
) {
  return `${value.toFixed(1)}%`;
}


function formatSignedNumber(
  value: number,
) {
  if (
    value > 0
  ) {
    return `+${value}`;
  }

  return String(
    value,
  );
}


function getFormLetterClass(
  result: string,
) {
  if (
    result === "V"
  ) {
    return "comparison-form-win";
  }

  if (
    result === "E"
  ) {
    return "comparison-form-draw";
  }

  if (
    result === "D"
  ) {
    return "comparison-form-loss";
  }

  return "";
}


function ClubComparisonPage() {
  const [
    standings,
    setStandings,
  ] = useState<Standing[]>([]);

  const [
    teamAId,
    setTeamAId,
  ] = useState<number | null>(
    null,
  );

  const [
    teamBId,
    setTeamBId,
  ] = useState<number | null>(
    null,
  );

  const [
    comparison,
    setComparison,
  ] = useState<ClubComparison | null>(
    null,
  );

  const [
    loadingTeams,
    setLoadingTeams,
  ] = useState(
    true,
  );

  const [
    loadingComparison,
    setLoadingComparison,
  ] = useState(
    false,
  );

  const [
    error,
    setError,
  ] = useState<string | null>(
    null,
  );


  useEffect(
    () => {
      async function loadTeams() {
        try {
          setLoadingTeams(
            true,
          );

          setError(
            null,
          );

          const data =
            await getStandings();

          setStandings(
            data,
          );

          if (
            data.length >= 2
          ) {
            setTeamAId(
              data[0].team_id,
            );

            setTeamBId(
              data[1].team_id,
            );
          }
        } catch (
          requestError
        ) {
          console.error(
            requestError,
          );

          setError(
            "Não foi possível carregar os clubes.",
          );
        } finally {
          setLoadingTeams(
            false,
          );
        }
      }

      loadTeams();
    },
    [],
  );


  useEffect(
    () => {
      if (
        teamAId === null
        || teamBId === null
        || teamAId === teamBId
      ) {
        setComparison(
          null,
        );

        return;
      }

      async function loadComparison() {
        try {
          setLoadingComparison(
            true,
          );

          setError(
            null,
          );

          const data =
            await getClubComparison(
              teamAId as number,
              teamBId as number,
              5,
            );

          setComparison(
            data,
          );
        } catch (
          requestError
        ) {
          console.error(
            requestError,
          );

          setComparison(
            null,
          );

          setError(
            "Não foi possível comparar os clubes.",
          );
        } finally {
          setLoadingComparison(
            false,
          );
        }
      }

      loadComparison();
    },
    [
      teamAId,
      teamBId,
    ],
  );


  const selectedTeamA =
    useMemo(
      () => standings.find(
        (
          team,
        ) =>
          team.team_id
          === teamAId,
      ) ?? null,
      [
        standings,
        teamAId,
      ],
    );


  const selectedTeamB =
    useMemo(
      () => standings.find(
        (
          team,
        ) =>
          team.team_id
          === teamBId,
      ) ?? null,
      [
        standings,
        teamBId,
      ],
    );


  function swapTeams() {
    setTeamAId(
      teamBId,
    );

    setTeamBId(
      teamAId,
    );
  }


  if (
    loadingTeams
  ) {
    return (
      <div className="panel">
        <div className="panel-header">
          <div className="panel-icon">
            <Activity
              size={19}
            />
          </div>

          <div>
            <h2>
              Preparando comparação...
            </h2>

            <p>
              Carregando os clubes
              da Série A.
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
            Comparação de Clubes
          </h1>

          <p>
            Coloque dois clubes frente
            a frente e compare campanha,
            forma recente, desempenho
            como mandante e visitante e
            confronto direto.
          </p>
        </div>

        <div className="round-badge">
          <Swords
            size={17}
          />

          Frente a frente
        </div>
      </header>


      <section className="comparison-selector-card">
        <div className="comparison-selector">
          <label
            htmlFor="comparison-team-a"
          >
            Clube A
          </label>

          <select
            id="comparison-team-a"
            value={
              teamAId ?? ""
            }
            onChange={
              (
                event,
              ) => {
                setTeamAId(
                  Number(
                    event.target.value,
                  ),
                );
              }
            }
          >
            {
              standings.map(
                (
                  team,
                ) => (
                  <option
                    key={
                      team.team_id
                    }
                    value={
                      team.team_id
                    }
                    disabled={
                      team.team_id
                      === teamBId
                    }
                  >
                    {
                      team.position
                    }º · {
                      team.team
                    }
                  </option>
                ),
              )
            }
          </select>
        </div>


        <button
          type="button"
          className="comparison-swap-button"
          onClick={
            swapTeams
          }
          disabled={
            teamAId === null
            || teamBId === null
          }
          aria-label="Inverter clubes"
          title="Inverter clubes"
        >
          <ArrowLeftRight
            size={20}
          />
        </button>


        <div className="comparison-selector">
          <label
            htmlFor="comparison-team-b"
          >
            Clube B
          </label>

          <select
            id="comparison-team-b"
            value={
              teamBId ?? ""
            }
            onChange={
              (
                event,
              ) => {
                setTeamBId(
                  Number(
                    event.target.value,
                  ),
                );
              }
            }
          >
            {
              standings.map(
                (
                  team,
                ) => (
                  <option
                    key={
                      team.team_id
                    }
                    value={
                      team.team_id
                    }
                    disabled={
                      team.team_id
                      === teamAId
                    }
                  >
                    {
                      team.position
                    }º · {
                      team.team
                    }
                  </option>
                ),
              )
            }
          </select>
        </div>
      </section>


      {
        error
        && (
          <section className="comparison-message-card">
            <Activity
              size={19}
            />

            <span>
              {error}
            </span>
          </section>
        )
      }


      {
        teamAId
        === teamBId
        && (
          <section className="comparison-message-card">
            <Shield
              size={19}
            />

            <span>
              Selecione dois clubes diferentes.
            </span>
          </section>
        )
      }


      {
        loadingComparison
        && (
          <section className="comparison-message-card">
            <Activity
              size={19}
            />

            <span>
              Calculando o duelo...
            </span>
          </section>
        )
      }


      {
        comparison
        && !loadingComparison
        && (
          <>
            <section className="comparison-hero">
              <TeamHero
                team={
                  comparison.team_a
                }
                side="a"
                winner={
                  comparison.overall_advantage
                  === comparison.team_a.team_id
                }
              />

              <div className="comparison-versus">
                <span>
                  VS
                </span>

                <small>
                  {
                    comparison.team_a_advantages
                  }
                  {" "}
                  ×
                  {" "}
                  {
                    comparison.team_b_advantages
                  }
                  {" "}
                  métricas
                </small>
              </div>

              <TeamHero
                team={
                  comparison.team_b
                }
                side="b"
                winner={
                  comparison.overall_advantage
                  === comparison.team_b.team_id
                }
              />
            </section>


            <section className="comparison-layout">
              <div className="comparison-main-column">
                <article className="comparison-card">
                  <div className="comparison-card-header">
                    <div className="comparison-card-icon">
                      <Trophy
                        size={19}
                      />
                    </div>

                    <div>
                      <h2>
                        Comparação geral
                      </h2>

                      <p>
                        O destaque indica qual
                        clube leva vantagem
                        naquela métrica.
                      </p>
                    </div>
                  </div>


                  <div className="comparison-table">
                    <div className="comparison-table-header">
                      <strong>
                        {
                          comparison.team_a.team
                        }
                      </strong>

                      <span>
                        Métrica
                      </span>

                      <strong>
                        {
                          comparison.team_b.team
                        }
                      </strong>
                    </div>

                    {
                      METRIC_ROWS.map(
                        (
                          metric,
                        ) => {
                          const winner =
                            comparison
                              .metric_winners[
                                metric.key
                              ];

                          const teamAValue =
                            metric.getValue(
                              comparison.team_a,
                            );

                          const teamBValue =
                            metric.getValue(
                              comparison.team_b,
                            );

                          return (
                            <div
                              key={
                                metric.key
                              }
                              className="comparison-table-row"
                            >
                              <div
                                className={
                                  winner
                                  === comparison
                                    .team_a
                                    .team_id
                                    ? "comparison-value comparison-value-winner"
                                    : "comparison-value"
                                }
                              >
                                {
                                  metric.format(
                                    teamAValue,
                                  )
                                }
                              </div>

                              <span className="comparison-metric-label">
                                {
                                  metric.label
                                }
                              </span>

                              <div
                                className={
                                  winner
                                  === comparison
                                    .team_b
                                    .team_id
                                    ? "comparison-value comparison-value-winner"
                                    : "comparison-value"
                                }
                              >
                                {
                                  metric.format(
                                    teamBValue,
                                  )
                                }
                              </div>
                            </div>
                          );
                        },
                      )
                    }
                  </div>
                </article>


                <article className="comparison-card">
                  <div className="comparison-card-header">
                    <div className="comparison-card-icon">
                      <Flame
                        size={19}
                      />
                    </div>

                    <div>
                      <h2>
                        Forma recente
                      </h2>

                      <p>
                        Últimos {
                          comparison.recent_n
                        } jogos de cada clube.
                      </p>
                    </div>
                  </div>


                  <div className="comparison-form-grid">
                    <FormBlock
                      team={
                        comparison.team_a
                      }
                    />

                    <FormBlock
                      team={
                        comparison.team_b
                      }
                    />
                  </div>
                </article>


                <article className="comparison-card">
                  <div className="comparison-card-header">
                    <div className="comparison-card-icon">
                      <Swords
                        size={19}
                      />
                    </div>

                    <div>
                      <h2>
                        Confronto direto
                      </h2>

                      <p>
                        Partidas realizadas
                        entre os dois clubes
                        na temporada disponível.
                      </p>
                    </div>
                  </div>


                  <div className="comparison-h2h-summary">
                    <div>
                      <span>
                        {
                          comparison.team_a.team
                        }
                      </span>

                      <strong>
                        {
                          comparison
                            .head_to_head
                            .team_a_wins
                        }
                      </strong>

                      <small>
                        vitórias
                      </small>
                    </div>

                    <div>
                      <span>
                        Empates
                      </span>

                      <strong>
                        {
                          comparison
                            .head_to_head
                            .draws
                        }
                      </strong>

                      <small>
                        jogos
                      </small>
                    </div>

                    <div>
                      <span>
                        {
                          comparison.team_b.team
                        }
                      </span>

                      <strong>
                        {
                          comparison
                            .head_to_head
                            .team_b_wins
                        }
                      </strong>

                      <small>
                        vitórias
                      </small>
                    </div>
                  </div>


                  {
                    comparison
                      .head_to_head
                      .games
                      .length
                    > 0
                      ? (
                        <div className="comparison-match-list">
                          {
                            comparison
                              .head_to_head
                              .games
                              .map(
                                (
                                  game,
                                ) => (
                                  <div
                                    key={
                                      game.match_id
                                      ?? `${
                                        game.home_team
                                      }-${
                                        game.away_team
                                      }-${
                                        game.round
                                      }`
                                    }
                                    className="comparison-match"
                                  >
                                    <span>
                                      {
                                        game.round
                                        ? `${game.round}ª rodada`
                                        : "Rodada"
                                      }
                                    </span>

                                    <div>
                                      <strong>
                                        {
                                          game.home_team
                                        }
                                      </strong>

                                      <b>
                                        {
                                          game.home_goals
                                        }
                                        {" "}
                                        ×
                                        {" "}
                                        {
                                          game.away_goals
                                        }
                                      </b>

                                      <strong>
                                        {
                                          game.away_team
                                        }
                                      </strong>
                                    </div>
                                  </div>
                                ),
                              )
                          }
                        </div>
                      )
                      : (
                        <div className="comparison-empty">
                          Nenhum confronto
                          realizado encontrado.
                        </div>
                      )
                  }
                </article>
              </div>


              <aside className="comparison-side-column">
                <PerformanceCard
                  title="Mandante"
                  icon={
                    <House
                      size={18}
                    />
                  }
                  teamA={
                    comparison.team_a
                  }
                  teamB={
                    comparison.team_b
                  }
                  getPercentage={
                    (
                      team,
                    ) =>
                      team.home_performance_pct
                  }
                  getRecord={
                    (
                      team,
                    ) =>
                      `${team.home_wins}V · ${team.home_draws}E · ${team.home_losses}D`
                  }
                />

                <PerformanceCard
                  title="Visitante"
                  icon={
                    <Plane
                      size={18}
                    />
                  }
                  teamA={
                    comparison.team_a
                  }
                  teamB={
                    comparison.team_b
                  }
                  getPercentage={
                    (
                      team,
                    ) =>
                      team.away_performance_pct
                  }
                  getRecord={
                    (
                      team,
                    ) =>
                      `${team.away_wins}V · ${team.away_draws}E · ${team.away_losses}D`
                  }
                />

                <article className="comparison-card comparison-summary-card">
                  <div className="comparison-card-header">
                    <div className="comparison-card-icon">
                      <Goal
                        size={19}
                      />
                    </div>

                    <div>
                      <h2>
                        Resumo do duelo
                      </h2>
                    </div>
                  </div>

                  <SummaryRow
                    label="Jogos"
                    teamA={
                      comparison.team_a.matches
                    }
                    teamB={
                      comparison.team_b.matches
                    }
                  />

                  <SummaryRow
                    label="Vitórias"
                    teamA={
                      comparison.team_a.wins
                    }
                    teamB={
                      comparison.team_b.wins
                    }
                  />

                  <SummaryRow
                    label="Empates"
                    teamA={
                      comparison.team_a.draws
                    }
                    teamB={
                      comparison.team_b.draws
                    }
                  />

                  <SummaryRow
                    label="Derrotas"
                    teamA={
                      comparison.team_a.losses
                    }
                    teamB={
                      comparison.team_b.losses
                    }
                  />

                  <SummaryRow
                    label="GP"
                    teamA={
                      comparison.team_a.goals_for
                    }
                    teamB={
                      comparison.team_b.goals_for
                    }
                  />

                  <SummaryRow
                    label="GC"
                    teamA={
                      comparison.team_a.goals_against
                    }
                    teamB={
                      comparison.team_b.goals_against
                    }
                  />
                </article>
              </aside>
            </section>
          </>
        )
      }


      {
        !comparison
        && !loadingComparison
        && !error
        && selectedTeamA
        && selectedTeamB
        && (
          <section className="comparison-message-card">
            <Swords
              size={19}
            />

            <span>
              Selecione os clubes
              para iniciar a comparação.
            </span>
          </section>
        )
      }
    </>
  );
}


interface TeamHeroProps {
  team: ClubComparisonTeam;
  side: "a" | "b";
  winner: boolean;
}


function TeamHero({
  team,
  side,
  winner,
}: TeamHeroProps) {
  return (
    <article
      className={
        winner
          ? `comparison-team-hero comparison-team-${side} comparison-team-winner`
          : `comparison-team-hero comparison-team-${side}`
      }
    >
      <div className="comparison-team-badge">
        <Shield
          size={28}
        />
      </div>

      <div>
        <span>
          {team.position}º lugar
        </span>

        <h2>
          {team.team}
        </h2>

        <p>
          {team.points} pontos
          {" "}
          ·
          {" "}
          {
            team.performance_pct.toFixed(
              1,
            )
          }%
        </p>
      </div>

      {
        winner
        && (
          <div className="comparison-advantage-badge">
            <Trophy
              size={14}
            />

            vantagem
          </div>
        )
      }
    </article>
  );
}


interface FormBlockProps {
  team: ClubComparisonTeam;
}


function FormBlock({
  team,
}: FormBlockProps) {
  const results =
    team.recent_form
      .trim()
      .split(/\s+/)
      .filter(
        Boolean,
      );

  return (
    <div className="comparison-form-block">
      <div>
        <strong>
          {team.team}
        </strong>

        <span>
          {team.recent_points} pts
          {" "}
          ·
          {" "}
          {
            team.recent_performance_pct.toFixed(
              1,
            )
          }%
        </span>
      </div>

      <div className="comparison-form-sequence">
        {
          results.length
          > 0
            ? results.map(
              (
                result,
                index,
              ) => (
                <span
                  key={
                    `${result}-${index}`
                  }
                  className={
                    `comparison-form-letter ${
                      getFormLetterClass(
                        result,
                      )
                    }`
                  }
                >
                  {result}
                </span>
              ),
            )
            : (
              <small>
                Sem jogos recentes
              </small>
            )
        }
      </div>
    </div>
  );
}


interface PerformanceCardProps {
  title: string;
  icon: React.ReactNode;

  teamA: ClubComparisonTeam;
  teamB: ClubComparisonTeam;

  getPercentage: (
    team: ClubComparisonTeam,
  ) => number;

  getRecord: (
    team: ClubComparisonTeam,
  ) => string;
}


function PerformanceCard({
  title,
  icon,
  teamA,
  teamB,
  getPercentage,
  getRecord,
}: PerformanceCardProps) {
  return (
    <article className="comparison-card">
      <div className="comparison-card-header">
        <div className="comparison-card-icon">
          {icon}
        </div>

        <div>
          <h2>
            {title}
          </h2>

          <p>
            Aproveitamento
          </p>
        </div>
      </div>

      <div className="comparison-performance-team">
        <div>
          <strong>
            {teamA.team}
          </strong>

          <span>
            {getRecord(
              teamA,
            )}
          </span>
        </div>

        <b>
          {
            getPercentage(
              teamA,
            ).toFixed(
              1,
            )
          }%
        </b>
      </div>

      <div className="comparison-performance-team">
        <div>
          <strong>
            {teamB.team}
          </strong>

          <span>
            {getRecord(
              teamB,
            )}
          </span>
        </div>

        <b>
          {
            getPercentage(
              teamB,
            ).toFixed(
              1,
            )
          }%
        </b>
      </div>
    </article>
  );
}


interface SummaryRowProps {
  label: string;
  teamA: number;
  teamB: number;
}


function SummaryRow({
  label,
  teamA,
  teamB,
}: SummaryRowProps) {
  return (
    <div className="comparison-summary-row">
      <strong>
        {teamA}
      </strong>

      <span>
        {label}
      </span>

      <strong>
        {teamB}
      </strong>
    </div>
  );
}


export default ClubComparisonPage;