import {
  Activity,
  Bot,
  CalendarDays,
  Clock3,
  MapPin,
} from "lucide-react";

import {
  useEffect,
  useMemo,
  useState,
} from "react";

import {
  getChampionshipSummary,
  getMatches,
  getMatchPredictions,
  getStandings,
} from "../api";

import type {
  ChampionshipMatch,
  ChampionshipSummary,
  MatchPrediction,
  MatchStatus,
  Standing,
} from "../api";


function GamesPage() {
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
    matches,
    setMatches,
  ] = useState<ChampionshipMatch[]>([]);

  const [
    predictions,
    setPredictions,
  ] = useState<MatchPrediction[]>([]);

  const [
    selectedRound,
    setSelectedRound,
  ] = useState<string>(
    "",
  );

  const [
    selectedTeam,
    setSelectedTeam,
  ] = useState<string>(
    "",
  );

  const [
    selectedStatus,
    setSelectedStatus,
  ] = useState<MatchStatus>(
    "all",
  );

  const [
    loading,
    setLoading,
  ] = useState(true);

  const [
    matchesLoading,
    setMatchesLoading,
  ] = useState(false);

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
          ] = await Promise.all([
            getChampionshipSummary(),
            getStandings(),
          ]);

          setSummary(
            summaryData,
          );

          setStandings(
            standingsData,
          );
        } catch (
          requestError
        ) {
          console.error(
            requestError,
          );

          setError(
            "Não foi possível carregar a página de jogos.",
          );
        } finally {
          setLoading(false);
        }
      }

      loadPage();
    },
    [],
  );


  useEffect(
    () => {
      async function loadMatchesAndPredictions() {
        try {
          setMatchesLoading(true);
          setError(null);

          const roundNumber =
            selectedRound
              ? Number(
                  selectedRound,
                )
              : undefined;

          const teamId =
            selectedTeam
              ? Number(
                  selectedTeam,
                )
              : undefined;

          const [
            matchData,
            predictionData,
          ] = await Promise.all([
            getMatches({
              roundNumber,
              teamId,
              status:
                selectedStatus,
            }),
            getMatchPredictions({
              roundNumber,
              teamId,
            }),
          ]);

          setMatches(
            matchData,
          );

          setPredictions(
            predictionData,
          );
        } catch (
          requestError
        ) {
          console.error(
            requestError,
          );

          setError(
            "Não foi possível carregar as partidas e previsões.",
          );
        } finally {
          setMatchesLoading(false);
        }
      }

      loadMatchesAndPredictions();
    },
    [
      selectedRound,
      selectedTeam,
      selectedStatus,
    ],
  );


  const predictionByMatchId =
    useMemo(
      () => {
        return new Map(
          predictions.map(
            (
              prediction,
            ) => [
              prediction.match_id,
              prediction,
            ],
          ),
        );
      },
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
              Carregando jogos...
            </h2>

            <p>
              Consultando o campeonato.
            </p>
          </div>
        </div>
      </div>
    );
  }


  if (
    error
    && !summary
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
            Jogos
          </h1>

          <p>
            Partidas realizadas e futuras
            da Série A {summary?.season},
            agora com probabilidades do
            modelo de Machine Learning.
          </p>
        </div>

        <div className="round-badge">
          <CalendarDays size={17} />

          {matches.length} partidas
        </div>
      </header>


      <section className="games-toolbar">
        <div className="games-status-filter">
          <button
            className={
              selectedStatus
              === "all"
                ? "games-filter-button active"
                : "games-filter-button"
            }
            onClick={
              () =>
                setSelectedStatus(
                  "all",
                )
            }
          >
            Todos
          </button>

          <button
            className={
              selectedStatus
              === "played"
                ? "games-filter-button active"
                : "games-filter-button"
            }
            onClick={
              () =>
                setSelectedStatus(
                  "played",
                )
            }
          >
            Realizados
          </button>

          <button
            className={
              selectedStatus
              === "upcoming"
                ? "games-filter-button active"
                : "games-filter-button"
            }
            onClick={
              () =>
                setSelectedStatus(
                  "upcoming",
                )
            }
          >
            Próximos
          </button>
        </div>


        <div className="games-selectors">
          <label>
            <span>
              Rodada
            </span>

            <select
              value={
                selectedRound
              }
              onChange={
                (
                  event,
                ) =>
                  setSelectedRound(
                    event.target.value,
                  )
              }
            >
              <option value="">
                Todas
              </option>

              {
                Array.from(
                  {
                    length: 38,
                  },
                  (
                    _,
                    index,
                  ) =>
                    index + 1,
                ).map(
                  (
                    round,
                  ) => (
                    <option
                      key={
                        round
                      }
                      value={
                        round
                      }
                    >
                      Rodada{" "}
                      {round}
                    </option>
                  ),
                )
              }
            </select>
          </label>


          <label>
            <span>
              Clube
            </span>

            <select
              value={
                selectedTeam
              }
              onChange={
                (
                  event,
                ) =>
                  setSelectedTeam(
                    event.target.value,
                  )
              }
            >
              <option value="">
                Todos
              </option>

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
                    >
                      {
                        team.team
                      }
                    </option>
                  ),
                )
              }
            </select>
          </label>
        </div>
      </section>


      {
        matchesLoading
          ? (
              <div className="games-loading">
                <div className="loader" />

                <span>
                  Atualizando partidas...
                </span>
              </div>
            )
          : null
      }


      {
        error
          ? (
              <div className="games-error">
                {error}
              </div>
            )
          : null
      }


      {
        !matchesLoading
        && matches.length
        === 0
          ? (
              <div className="games-empty">
                <CalendarDays
                  size={32}
                />

                <strong>
                  Nenhuma partida encontrada
                </strong>

                <span>
                  Altere os filtros para
                  visualizar outros jogos.
                </span>
              </div>
            )
          : null
      }


      <section className="games-grid">
        {
          matches.map(
            (
              match,
            ) => (
              <MatchCard
                key={
                  match.match_id
                }
                match={
                  match
                }
                prediction={
                  predictionByMatchId.get(
                    match.match_id,
                  )
                }
              />
            ),
          )
        }
      </section>
    </>
  );
}


function MatchCard({
  match,
  prediction,
}: {
  match: ChampionshipMatch;
  prediction?: MatchPrediction;
}) {
  const played =
    match.status
    === "played";

  const formattedDate =
    formatMatchDate(
      match.date,
    );

  const formattedTime =
    formatMatchTime(
      match.time,
    );

  return (
    <article className="match-card">
      <div className="match-card-header">
        <span>
          Rodada{" "}
          {match.round}
        </span>

        <span
          className={
            played
              ? "match-status played"
              : "match-status upcoming"
          }
        >
          {
            played
              ? "Finalizado"
              : "Próximo"
          }
        </span>
      </div>


      <div className="match-score">
        <div className="match-team">
          <strong>
            {match.home_team}
          </strong>

          <span>
            Mandante
          </span>
        </div>

        <div className="score">
          {
            played
              ? (
                  <>
                    <strong>
                      {
                        match.home_goals
                      }
                    </strong>

                    <span>
                      x
                    </span>

                    <strong>
                      {
                        match.away_goals
                      }
                    </strong>
                  </>
                )
              : (
                  <span className="versus">
                    x
                  </span>
                )
          }
        </div>

        <div className="match-team away">
          <strong>
            {match.away_team}
          </strong>

          <span>
            Visitante
          </span>
        </div>
      </div>


      {
        !played
        && prediction
          ? (
              <PredictionStrip
                prediction={
                  prediction
                }
              />
            )
          : null
      }


      <div className="match-meta">
        <div>
          <CalendarDays
            size={14}
          />

          <span>
            {formattedDate}
          </span>
        </div>

        <div>
          <Clock3
            size={14}
          />

          <span>
            {formattedTime}
          </span>
        </div>

        <div>
          <MapPin
            size={14}
          />

          <span>
            {
              buildLocation(
                match,
              )
            }
          </span>
        </div>
      </div>
    </article>
  );
}


function PredictionStrip({
  prediction,
}: {
  prediction: MatchPrediction;
}) {
  return (
    <div
      style={{
        margin: "0 18px 16px",
        padding: "12px 14px",
        borderRadius: "12px",
        border:
          "1px solid rgba(99, 102, 241, 0.24)",
        background:
          "rgba(99, 102, 241, 0.08)",
      }}
    >
      <div
        style={{
          display: "flex",
          alignItems: "center",
          gap: "7px",
          marginBottom: "9px",
          fontSize: "12px",
          fontWeight: 700,
          letterSpacing: "0.04em",
          textTransform: "uppercase",
          opacity: 0.82,
        }}
      >
        <Bot size={15} />

        Previsão do modelo
      </div>

      <div
        style={{
          display: "grid",
          gridTemplateColumns:
            "1fr auto 1fr auto 1fr",
          alignItems: "center",
          gap: "8px",
          fontSize: "13px",
        }}
      >
        <ProbabilityItem
          label={
            shortTeamName(
              prediction.home_team,
            )
          }
          value={
            prediction.home_probability_pct
          }
          highlighted={
            prediction.predicted_result
            === "HOME"
          }
        />

        <span
          style={{
            opacity: 0.45,
          }}
        >
          •
        </span>

        <ProbabilityItem
          label="X"
          value={
            prediction.draw_probability_pct
          }
          highlighted={
            prediction.predicted_result
            === "DRAW"
          }
        />

        <span
          style={{
            opacity: 0.45,
          }}
        >
          •
        </span>

        <ProbabilityItem
          label={
            shortTeamName(
              prediction.away_team,
            )
          }
          value={
            prediction.away_probability_pct
          }
          highlighted={
            prediction.predicted_result
            === "AWAY"
          }
        />
      </div>
    </div>
  );
}


function ProbabilityItem({
  label,
  value,
  highlighted,
}: {
  label: string;
  value: number;
  highlighted: boolean;
}) {
  return (
    <div
      style={{
        display: "flex",
        justifyContent: "center",
        alignItems: "center",
        gap: "5px",
        fontWeight:
          highlighted
            ? 800
            : 600,
        opacity:
          highlighted
            ? 1
            : 0.72,
        whiteSpace: "nowrap",
      }}
    >
      <span>
        {label}
      </span>

      <strong>
        {value.toFixed(1)}%
      </strong>
    </div>
  );
}


function shortTeamName(
  teamName: string,
) {
  const replacements:
    Record<string, string> = {
      "Athletico Paranaense":
        "Athletico-PR",
      "Atlético Mineiro":
        "Atlético-MG",
      "Red Bull Bragantino":
        "Bragantino",
      "Vasco da Gama Saf":
        "Vasco",
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


function formatMatchDate(
  value: string | null,
) {
  if (!value) {
    return "Data a definir";
  }

  const [
    year,
    month,
    day,
  ] = value.split(
    "-",
  );

  return `${day}/${month}/${year}`;
}


function formatMatchTime(
  value: string | null,
) {
  if (!value) {
    return "Horário a definir";
  }

  return value.slice(
    0,
    5,
  );
}


function buildLocation(
  match: ChampionshipMatch,
) {
  const location = [
    match.venue,
    match.city,
    match.state,
  ].filter(
    Boolean,
  );

  if (
    location.length
    === 0
  ) {
    return "Local a definir";
  }

  return location.join(
    " • ",
  );
}


export default GamesPage;