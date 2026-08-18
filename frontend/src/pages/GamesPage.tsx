import {
  Activity,
  CalendarDays,
  Clock3,
  MapPin,
} from "lucide-react";

import {
  useEffect,
  useState,
} from "react";

import {
  getChampionshipSummary,
  getMatches,
  getStandings,
} from "../api";

import type {
  ChampionshipMatch,
  ChampionshipSummary,
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
      async function loadMatches() {
        try {
          setMatchesLoading(true);
          setError(null);

          const matchData =
            await getMatches({
              roundNumber:
                selectedRound
                  ? Number(
                      selectedRound,
                    )
                  : undefined,

              teamId:
                selectedTeam
                  ? Number(
                      selectedTeam,
                    )
                  : undefined,

              status:
                selectedStatus,
            });

          setMatches(
            matchData,
          );
        } catch (
          requestError
        ) {
          console.error(
            requestError,
          );

          setError(
            "Não foi possível carregar as partidas.",
          );
        } finally {
          setMatchesLoading(false);
        }
      }

      loadMatches();
    },
    [
      selectedRound,
      selectedTeam,
      selectedStatus,
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
            da Série A {summary?.season}.
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
}: {
  match: ChampionshipMatch;
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