import {
  Activity,
  Bot,
  Medal,
  ShieldAlert,
  Sparkles,
  Target,
  Trophy,
} from "lucide-react";

import {
  useEffect,
  useMemo,
  useState,
} from "react";

import {
  getPredictionStandings,
} from "../api";

import type {
  StandingPrediction,
} from "../api";

import "./PredictionsPage.css";


function PredictionsPage() {
  const [
    predictions,
    setPredictions,
  ] = useState<StandingPrediction[]>([]);

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
      async function loadPredictions() {
        try {
          setLoading(true);
          setError(null);

          const data =
            await getPredictionStandings();

          setPredictions(
            data,
          );
        } catch (
          requestError
        ) {
          console.error(
            requestError,
          );

          setError(
            "Não foi possível carregar as previsões do campeonato.",
          );
        } finally {
          setLoading(false);
        }
      }

      loadPredictions();
    },
    [],
  );


  const titleContenders =
    useMemo(
      () =>
        [...predictions]
          .sort(
            (
              a,
              b,
            ) =>
              b.champion_probability_pct
              - a.champion_probability_pct,
          )
          .slice(
            0,
            4,
          ),
      [
        predictions,
      ],
    );


  const relegationRisks =
    useMemo(
      () =>
        [...predictions]
          .sort(
            (
              a,
              b,
            ) =>
              b.relegation_probability_pct
              - a.relegation_probability_pct,
          )
          .slice(
            0,
            6,
          ),
      [
        predictions,
      ],
    );


  if (loading) {
    return (
      <div className="panel">
        <div className="panel-header">
          <div className="panel-icon">
            <Activity size={19} />
          </div>

          <div>
            <h2>
              Carregando previsões...
            </h2>

            <p>
              Consultando as simulações do campeonato.
            </p>
          </div>
        </div>
      </div>
    );
  }


  if (
    error
    || predictions.length
    === 0
  ) {
    return (
      <div className="panel">
        <div className="panel-header">
          <div className="panel-icon">
            <ShieldAlert size={19} />
          </div>

          <div>
            <h2>
              Previsões indisponíveis
            </h2>

            <p>
              {
                error
                ?? "Nenhuma projeção encontrada."
              }
            </p>
          </div>
        </div>
      </div>
    );
  }


  const season =
    predictions[
      0
    ].season;

  const simulations =
    predictions[
      0
    ].simulations;


  return (
    <>
      <header className="page-header">
        <div>
          <span className="eyebrow">
            MACHINE LEARNING
          </span>

          <h1>
            Previsões
          </h1>

          <p>
            Projeção do Brasileirão{" "}
            {season} baseada nas
            probabilidades do modelo e em{" "}
            {formatNumber(
              simulations,
            )} simulações Monte Carlo.
          </p>
        </div>

        <div className="round-badge">
          <Bot size={17} />

          Random Forest
        </div>
      </header>


      <section className="predictions-title-grid">
        {
          titleContenders.map(
            (
              team,
              index,
            ) => (
              <TitleCard
                key={
                  team.team_key
                }
                team={
                  team
                }
                rank={
                  index + 1
                }
              />
            ),
          )
        }
      </section>


      <section className="predictions-layout">
        <div className="panel predictions-table-panel">
          <div className="panel-header">
            <div className="panel-icon">
              <Target size={19} />
            </div>

            <div>
              <h2>
                Classificação projetada
              </h2>

              <p>
                Posição média, pontos esperados
                e probabilidades por clube.
              </p>
            </div>
          </div>

          <div className="predictions-table-wrapper">
            <table className="predictions-table">
              <thead>
                <tr>
                  <TableHeader>
                    Pos.
                  </TableHeader>

                  <TableHeader align="left">
                    Clube
                  </TableHeader>

                  <TableHeader>
                    Pts esp.
                  </TableHeader>

                  <TableHeader>
                    Pos. média
                  </TableHeader>

                  <TableHeader>
                    Título
                  </TableHeader>

                  <TableHeader>
                    G4
                  </TableHeader>

                  <TableHeader>
                    Top 6
                  </TableHeader>

                  <TableHeader>
                    Rebaix.
                  </TableHeader>
                </tr>
              </thead>

              <tbody>
                {
                  predictions.map(
                    (
                      team,
                    ) => (
                      <tr
                        key={
                          team.team_key
                        }
                        className="predictions-table-row"
                      >
                        <TableCell>
                          <PositionBadge
                            position={
                              team.projected_position
                            }
                          />
                        </TableCell>

                        <TableCell align="left">
                          <strong>
                            {
                              cleanTeamName(
                                team.team_name,
                              )
                            }
                          </strong>
                        </TableCell>

                        <TableCell>
                          {
                            team.expected_points.toFixed(
                              1,
                            )
                          }
                        </TableCell>

                        <TableCell>
                          {
                            team.average_position.toFixed(
                              1,
                            )
                          }
                        </TableCell>

                        <TableCell>
                          <ProbabilityText
                            value={
                              team.champion_probability_pct
                            }
                            highlight={
                              team.champion_probability_pct
                              >= 10
                            }
                          />
                        </TableCell>

                        <TableCell>
                          <ProbabilityText
                            value={
                              team.top4_probability_pct
                            }
                            highlight={
                              team.top4_probability_pct
                              >= 50
                            }
                          />
                        </TableCell>

                        <TableCell>
                          <ProbabilityText
                            value={
                              team.top6_probability_pct
                            }
                          />
                        </TableCell>

                        <TableCell>
                          <ProbabilityText
                            value={
                              team.relegation_probability_pct
                            }
                            danger={
                              team.relegation_probability_pct
                              >= 50
                            }
                          />
                        </TableCell>
                      </tr>
                    ),
                  )
                }
              </tbody>
            </table>
          </div>
        </div>


        <div className="predictions-side-column">
          <div className="panel">
            <div className="panel-header">
              <div className="panel-icon">
                <Trophy size={19} />
              </div>

              <div>
                <h2>
                  Corrida pelo título
                </h2>

                <p>
                  Probabilidade de terminar
                  em 1º lugar.
                </p>
              </div>
            </div>

            <div className="predictions-probability-list">
              {
                titleContenders.map(
                  (
                    team,
                  ) => (
                    <ProbabilityBar
                      key={
                        team.team_key
                      }
                      label={
                        cleanTeamName(
                          team.team_name,
                        )
                      }
                      value={
                        team.champion_probability_pct
                      }
                    />
                  ),
                )
              }
            </div>
          </div>


          <div className="panel">
            <div className="panel-header">
              <div className="panel-icon">
                <ShieldAlert size={19} />
              </div>

              <div>
                <h2>
                  Risco de rebaixamento
                </h2>

                <p>
                  Clubes com maior chance
                  de terminar no Z4.
                </p>
              </div>
            </div>

            <div className="predictions-probability-list">
              {
                relegationRisks.map(
                  (
                    team,
                  ) => (
                    <ProbabilityBar
                      key={
                        team.team_key
                      }
                      label={
                        cleanTeamName(
                          team.team_name,
                        )
                      }
                      value={
                        team.relegation_probability_pct
                      }
                      danger
                    />
                  ),
                )
              }
            </div>
          </div>
        </div>
      </section>


      <section className="panel predictions-interpretation">
        <div className="panel-header">
          <div className="panel-icon">
            <Sparkles size={19} />
          </div>

          <div>
            <h2>
              Como interpretar
            </h2>

            <p>
              As porcentagens representam
              a frequência de cada evento nas{" "}
              {formatNumber(
                simulations,
              )} simulações.
              Elas são projeções probabilísticas,
              não garantias de resultado.
            </p>
          </div>
        </div>
      </section>
    </>
  );
}


function TitleCard({
  team,
  rank,
}: {
  team: StandingPrediction;
  rank: number;
}) {
  return (
    <article
      className="panel"
      style={{
        padding: "18px",
        margin: 0,
      }}
    >
      <div
        style={{
          display: "flex",
          justifyContent: "space-between",
          alignItems: "flex-start",
          gap: "12px",
        }}
      >
        <div>
          <span
            style={{
              fontSize: "11px",
              textTransform: "uppercase",
              letterSpacing: "0.08em",
              opacity: 0.55,
            }}
          >
            #{rank} em chance de título
          </span>

          <h3
            style={{
              margin:
                "8px 0 4px",
              fontSize: "18px",
            }}
          >
            {
              cleanTeamName(
                team.team_name,
              )
            }
          </h3>

          <span
            style={{
              fontSize: "12px",
              opacity: 0.58,
            }}
          >
            {
              team.expected_points.toFixed(
                1,
              )
            }{" "}
            pts esperados
          </span>
        </div>

        <Medal size={20} />
      </div>

      <div
        style={{
          marginTop: "18px",
          fontSize: "30px",
          fontWeight: 800,
          lineHeight: 1,
        }}
      >
        {
          team.champion_probability_pct.toFixed(
            2,
          )
        }%
      </div>

      <div
        style={{
          marginTop: "8px",
          fontSize: "12px",
          opacity: 0.58,
        }}
      >
        chance de título
      </div>
    </article>
  );
}


function ProbabilityBar({
  label,
  value,
  danger = false,
}: {
  label: string;
  value: number;
  danger?: boolean;
}) {
  const width = Math.max(
    0,
    Math.min(
      100,
      value,
    ),
  );

  return (
    <div>
      <div
        style={{
          display: "flex",
          justifyContent: "space-between",
          gap: "12px",
          marginBottom: "6px",
          fontSize: "12px",
        }}
      >
        <span>
          {label}
        </span>

        <strong>
          {value.toFixed(2)}%
        </strong>
      </div>

      <div
        style={{
          height: "7px",
          borderRadius: "999px",
          overflow: "hidden",
          background:
            "rgba(148, 163, 184, 0.12)",
        }}
      >
        <div
          style={{
            width: `${width}%`,
            height: "100%",
            borderRadius: "999px",
            background: danger
              ? "rgba(244, 63, 94, 0.75)"
              : "rgba(16, 185, 129, 0.78)",
          }}
        />
      </div>
    </div>
  );
}


function PositionBadge({
  position,
}: {
  position: number;
}) {
  return (
    <span
      style={{
        display: "inline-flex",
        width: "28px",
        height: "28px",
        alignItems: "center",
        justifyContent: "center",
        borderRadius: "8px",
        background:
          position <= 4
            ? "rgba(16, 185, 129, 0.12)"
            : position >= 17
              ? "rgba(244, 63, 94, 0.12)"
              : "rgba(148, 163, 184, 0.08)",
        fontWeight: 800,
      }}
    >
      {position}
    </span>
  );
}


function ProbabilityText({
  value,
  highlight = false,
  danger = false,
}: {
  value: number;
  highlight?: boolean;
  danger?: boolean;
}) {
  return (
    <strong
      style={{
        color: danger
          ? "#fb7185"
          : highlight
            ? "#34d399"
            : "inherit",
      }}
    >
      {value.toFixed(2)}%
    </strong>
  );
}


function TableHeader({
  children,
  align = "center",
}: {
  children: React.ReactNode;
  align?: "left" | "center";
}) {
  return (
    <th
      style={{
        padding: "12px 10px",
        textAlign: align,
        fontSize: "11px",
        textTransform: "uppercase",
        letterSpacing: "0.05em",
        opacity: 0.5,
        fontWeight: 700,
      }}
    >
      {children}
    </th>
  );
}


function TableCell({
  children,
  align = "center",
}: {
  children: React.ReactNode;
  align?: "left" | "center";
}) {
  return (
    <td
      style={{
        padding: "12px 10px",
        textAlign: align,
        fontSize: "13px",
      }}
    >
      {children}
    </td>
  );
}


function cleanTeamName(
  teamName: string,
) {
  const replacements:
    Record<string, string> = {
      "Vasco da Gama Saf":
        "Vasco da Gama",
      "Santos FC":
        "Santos",
    };

  return (
    replacements[
      teamName
    ]
    ?? teamName
  );
}


function formatNumber(
  value: number,
) {
  return new Intl.NumberFormat(
    "pt-BR",
  ).format(
    value,
  );
}


export default PredictionsPage;