import {
  Activity,
  ArrowLeft,
  BarChart3,
  CalendarDays,
  Clock3,
  ExternalLink,
  Goal,
  MapPin,
  Shield,
  Trophy,
  UserRound,
  Users,
} from "lucide-react";

import {
  useEffect,
  useMemo,
  useState,
} from "react";

import {
  Link,
  useParams,
} from "react-router-dom";

import {
  getClubPlayers,
  getMatches,
  getMatchPredictions,
  getRecentForm,
  getStandings,
} from "../api";

import type {
  ChampionshipMatch,
  ClubPlayer,
  MatchPrediction,
  RecentForm,
  Standing,
} from "../api";


type ClubTab =
  | "overview"
  | "matches"
  | "players"
  | "stats";


function ClubDetailsPage() {
  const {
    teamId,
  } = useParams();

  const parsedTeamId =
    Number(
      teamId,
    );

  const [
    team,
    setTeam,
  ] = useState<Standing | null>(
    null,
  );

  const [
    recentForm,
    setRecentForm,
  ] = useState<RecentForm | null>(
    null,
  );

  const [
    matches,
    setMatches,
  ] = useState<ChampionshipMatch[]>(
    [],
  );

  const [
    predictions,
    setPredictions,
  ] = useState<MatchPrediction[]>(
    [],
  );

  const [
    players,
    setPlayers,
  ] = useState<ClubPlayer[]>(
    [],
  );

  const [
    activeTab,
    setActiveTab,
  ] = useState<ClubTab>(
    "overview",
  );

  const [
    loading,
    setLoading,
  ] = useState(
    true,
  );

  const [
    error,
    setError,
  ] = useState<string | null>(
    null,
  );

  const [
    playersLoading,
    setPlayersLoading,
  ] = useState(
    true,
  );

  const [
    playersError,
    setPlayersError,
  ] = useState<string | null>(
    null,
  );


  useEffect(
    () => {
      let cancelled =
        false;

      async function loadClub() {
        if (
          !Number.isInteger(
            parsedTeamId,
          )
          || parsedTeamId <= 0
        ) {
          if (
            !cancelled
          ) {
            setError(
              "Clube inválido.",
            );

            setLoading(
              false,
            );
          }

          return;
        }

        try {
          setLoading(
            true,
          );

          setError(
            null,
          );

          const [
            standingsData,
            recentFormData,
            matchesData,
            predictionsData,
          ] = await Promise.all([
            getStandings(),
            getRecentForm(),
            getMatches({
              teamId:
                parsedTeamId,
            }),
            getMatchPredictions({
              teamId:
                parsedTeamId,
            }),
          ]);

          if (
            cancelled
          ) {
            return;
          }

          const selectedTeam =
            standingsData.find(
              (
                standing,
              ) =>
                standing.team_id
                === parsedTeamId,
            );

          if (
            !selectedTeam
          ) {
            setError(
              "Clube não encontrado.",
            );

            return;
          }

          const selectedRecentForm =
            recentFormData.find(
              (
                form,
              ) =>
                form.team_id
                === parsedTeamId,
            );

          setTeam(
            selectedTeam,
          );

          setRecentForm(
            selectedRecentForm
            ?? null,
          );

          setMatches(
            matchesData,
          );

          setPredictions(
            predictionsData,
          );
        } catch (
          requestError
        ) {
          console.error(
            requestError,
          );

          if (
            !cancelled
          ) {
            setError(
              "Não foi possível carregar os dados do clube.",
            );
          }
        } finally {
          if (
            !cancelled
          ) {
            setLoading(
              false,
            );
          }
        }
      }


      async function loadPlayers() {
        if (
          !Number.isInteger(
            parsedTeamId,
          )
          || parsedTeamId <= 0
        ) {
          if (
            !cancelled
          ) {
            setPlayers(
              [],
            );

            setPlayersLoading(
              false,
            );
          }

          return;
        }

        try {
          setPlayersLoading(
            true,
          );

          setPlayersError(
            null,
          );

          const playersData =
            await getClubPlayers(
              parsedTeamId,
            );

          if (
            cancelled
          ) {
            return;
          }

          setPlayers(
            playersData,
          );
        } catch (
          requestError
        ) {
          console.error(
            requestError,
          );

          if (
            !cancelled
          ) {
            setPlayers(
              [],
            );

            setPlayersError(
              "Não foi possível carregar os jogadores deste clube.",
            );
          }
        } finally {
          if (
            !cancelled
          ) {
            setPlayersLoading(
              false,
            );
          }
        }
      }


      void loadClub();

      void loadPlayers();


      return () => {
        cancelled = true;
      };
    },
    [
      parsedTeamId,
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


  const playedMatches =
    useMemo(
      () => {
        return [
          ...matches,
        ]
          .filter(
            (
              match,
            ) =>
              match.status
              === "played",
          )
          .sort(
            (
              first,
              second,
            ) =>
              second.round
              - first.round,
          );
      },
      [
        matches,
      ],
    );


  const upcomingMatches =
    useMemo(
      () => {
        return [
          ...matches,
        ]
          .filter(
            (
              match,
            ) =>
              match.status
              === "upcoming",
          )
          .sort(
            (
              first,
              second,
            ) =>
              first.round
              - second.round,
          );
      },
      [
        matches,
      ],
    );


  if (
    loading
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
              Carregando clube...
            </h2>

            <p>
              Consultando dados da temporada.
            </p>
          </div>
        </div>
      </div>
    );
  }


  if (
    error
    || !team
  ) {
    return (
      <>
        <Link
          to="/clubes"
          style={{
            display: "inline-flex",
            alignItems: "center",
            gap: "7px",
            marginBottom: "20px",
            color: "#27d684",
            textDecoration: "none",
            fontSize: "12px",
          }}
        >
          <ArrowLeft
            size={16}
          />

          Voltar para clubes
        </Link>

        <div className="panel">
          <div className="panel-header">
            <div className="panel-icon">
              <Activity
                size={19}
              />
            </div>

            <div>
              <h2>
                Clube indisponível
              </h2>

              <p>
                {
                  error
                  ?? "Não foi possível localizar o clube."
                }
              </p>
            </div>
          </div>
        </div>
      </>
    );
  }


  return (
    <>
      <Link
        to="/clubes"
        style={{
          display: "inline-flex",
          alignItems: "center",
          gap: "7px",
          marginBottom: "20px",
          color: "#27d684",
          textDecoration: "none",
          fontSize: "12px",
        }}
      >
        <ArrowLeft
          size={16}
        />

        Voltar para clubes
      </Link>


      <header className="page-header">
        <div>
          <span className="eyebrow">
            CAMPEONATO BRASILEIRO
          </span>

          <h1>
            {team.team}
          </h1>

          <p>
            Visão completa da temporada,
            partidas, elenco e estatísticas
            do clube.
          </p>
        </div>

        <div className="round-badge">
          <Shield
            size={17}
          />

          {team.position}º lugar
        </div>
      </header>


      <ClubTabs
        activeTab={
          activeTab
        }
        onChange={
          setActiveTab
        }
      />


      {
        activeTab
        === "overview"
          ? (
              <OverviewTab
                team={
                  team
                }
                recentForm={
                  recentForm
                }
                playedMatches={
                  playedMatches
                }
                upcomingMatches={
                  upcomingMatches
                }
                predictionByMatchId={
                  predictionByMatchId
                }
              />
            )
          : null
      }


      {
        activeTab
        === "matches"
          ? (
              <MatchesTab
                matches={
                  matches
                }
                predictionByMatchId={
                  predictionByMatchId
                }
              />
            )
          : null
      }


      {
        activeTab
        === "players"
          ? (
              <PlayersTab
                teamName={
                  team.team
                }
                players={
                  players
                }
                loading={
                  playersLoading
                }
                error={
                  playersError
                }
              />
            )
          : null
      }


      {
        activeTab
        === "stats"
          ? (
              <StatsTab
                team={
                  team
                }
                recentForm={
                  recentForm
                }
              />
            )
          : null
      }
    </>
  );
}


function ClubTabs({
  activeTab,
  onChange,
}: {
  activeTab: ClubTab;
  onChange:
    (
      tab: ClubTab,
    ) => void;
}) {
  const tabs: Array<{
    id: ClubTab;
    label: string;
  }> = [
    {
      id: "overview",
      label: "Visão Geral",
    },
    {
      id: "matches",
      label: "Jogos",
    },
    {
      id: "players",
      label: "Jogadores",
    },
    {
      id: "stats",
      label: "Estatísticas",
    },
  ];

  return (
    <div
      style={{
        display: "flex",
        gap: "8px",
        marginBottom: "24px",
        paddingBottom: "12px",
        overflowX: "auto",
        borderBottom:
          "1px solid #20282e",
      }}
    >
      {
        tabs.map(
          (
            tab,
          ) => {
            const selected =
              tab.id
              === activeTab;

            return (
              <button
                key={
                  tab.id
                }
                type="button"
                onClick={
                  () =>
                    onChange(
                      tab.id,
                    )
                }
                style={{
                  padding:
                    "10px 14px",
                  border:
                    selected
                      ? "1px solid #2a5b45"
                      : "1px solid #20282e",
                  borderRadius:
                    "9px",
                  color:
                    selected
                      ? "#eafff3"
                      : "#829089",
                  background:
                    selected
                      ? "rgba(39, 214, 134, 0.11)"
                      : "#11181d",
                  cursor:
                    "pointer",
                  whiteSpace:
                    "nowrap",
                }}
              >
                {tab.label}
              </button>
            );
          },
        )
      }
    </div>
  );
}


function OverviewTab({
  team,
  recentForm,
  playedMatches,
  upcomingMatches,
  predictionByMatchId,
}: {
  team: Standing;
  recentForm:
    RecentForm | null;
  playedMatches:
    ChampionshipMatch[];
  upcomingMatches:
    ChampionshipMatch[];
  predictionByMatchId:
    Map<number, MatchPrediction>;
}) {
  const nextMatch =
    upcomingMatches[0];

  const lastMatches =
    playedMatches.slice(
      0,
      5,
    );

  const recentSequence =
    recentForm?.form.match(
      /[VED]/gi,
    )
    ?? [];

  return (
    <>
      <section className="metric-grid">
        <MetricCard
          label="Posição"
          value={`${team.position}º`}
          detail="Classificação atual"
          icon={
            <Trophy
              size={18}
            />
          }
        />

        <MetricCard
          label="Pontos"
          value={
            String(
              team.points,
            )
          }
          detail={`${team.matches} partidas`}
          icon={
            <BarChart3
              size={18}
            />
          }
        />

        <MetricCard
          label="Aproveitamento"
          value={`${team.performance_pct.toFixed(1)}%`}
          detail={`${team.wins} vitórias`}
          icon={
            <Activity
              size={18}
            />
          }
        />

        <MetricCard
          label="Saldo de gols"
          value={
            team.goal_difference
            > 0
              ? `+${team.goal_difference}`
              : String(
                  team.goal_difference,
                )
          }
          detail={`${team.goals_for} GP • ${team.goals_against} GC`}
          icon={
            <Goal
              size={18}
            />
          }
        />
      </section>


      <section
        className="dashboard-grid"
        style={{
          marginTop: "18px",
        }}
      >
        <div className="panel">
          <div className="panel-header">
            <div className="panel-icon">
              <Activity
                size={18}
              />
            </div>

            <div>
              <h2>
                Forma recente
              </h2>

              <p>
                Últimas partidas disputadas
              </p>
            </div>
          </div>

          <div
            style={{
              padding:
                "18px",
            }}
          >
            {
              recentForm
                ? (
                    <>
                      <div
                        style={{
                          display:
                            "flex",
                          gap:
                            "6px",
                          flexWrap:
                            "wrap",
                          marginBottom:
                            "16px",
                        }}
                      >
                        {
                          recentSequence.map(
                            (
                              result,
                              index,
                            ) => (
                              <ResultBadge
                                key={
                                  `${result}-${index}`
                                }
                                result={
                                  result
                                }
                              />
                            ),
                          )
                        }
                      </div>

                      <div
                        style={{
                          color:
                            "#829089",
                          fontSize:
                            "12px",
                        }}
                      >
                        {
                          recentForm.wins
                        } vitórias •{" "}
                        {
                          recentForm.draws
                        } empates •{" "}
                        {
                          recentForm.losses
                        } derrotas
                      </div>
                    </>
                  )
                : (
                    <span
                      style={{
                        color:
                          "#65736c",
                        fontSize:
                          "12px",
                      }}
                    >
                      Forma recente indisponível.
                    </span>
                  )
            }
          </div>
        </div>


        <div className="panel">
          <div className="panel-header">
            <div className="panel-icon">
              <CalendarDays
                size={18}
              />
            </div>

            <div>
              <h2>
                Próximo jogo
              </h2>

              <p>
                Próxima partida programada
              </p>
            </div>
          </div>

          {
            nextMatch
              ? (
                  <div
                    style={{
                      padding:
                        "18px",
                    }}
                  >
                    <SimpleMatch
                      match={
                        nextMatch
                      }
                      prediction={
                        predictionByMatchId.get(
                          nextMatch.match_id,
                        )
                      }
                    />
                  </div>
                )
              : (
                  <div
                    style={{
                      padding:
                        "18px",
                      color:
                        "#65736c",
                      fontSize:
                        "12px",
                    }}
                  >
                    Nenhuma partida futura encontrada.
                  </div>
                )
          }
        </div>
      </section>


      <div
        className="panel"
        style={{
          marginTop: "18px",
        }}
      >
        <div className="panel-header">
          <div className="panel-icon">
            <CalendarDays
              size={18}
            />
          </div>

          <div>
            <h2>
              Últimos jogos
            </h2>

            <p>
              Cinco partidas mais recentes
            </p>
          </div>
        </div>

        <div
          style={{
            padding:
              "18px",
            display:
              "grid",
            gap:
              "10px",
          }}
        >
          {
            lastMatches.length
            > 0
              ? (
                  lastMatches.map(
                    (
                      match,
                    ) => (
                      <SimpleMatch
                        key={
                          match.match_id
                        }
                        match={
                          match
                        }
                      />
                    ),
                  )
                )
              : (
                  <span
                    style={{
                      color:
                        "#65736c",
                      fontSize:
                        "12px",
                    }}
                  >
                    Nenhuma partida disputada encontrada.
                  </span>
                )
          }
        </div>
      </div>
    </>
  );
}


function MatchesTab({
  matches,
  predictionByMatchId,
}: {
  matches:
    ChampionshipMatch[];
  predictionByMatchId:
    Map<number, MatchPrediction>;
}) {
  const orderedMatches =
    [
      ...matches,
    ].sort(
      (
        first,
        second,
      ) =>
        first.round
        - second.round,
    );

  return (
    <div className="panel">
      <div className="panel-header">
        <div className="panel-icon">
          <CalendarDays
            size={18}
          />
        </div>

        <div>
          <h2>
            Jogos do clube
          </h2>

          <p>
            Temporada completa
          </p>
        </div>
      </div>

      <div
        style={{
          padding:
            "18px",
          display:
            "grid",
          gap:
            "10px",
        }}
      >
        {
          orderedMatches.map(
            (
              match,
            ) => (
              <SimpleMatch
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
      </div>
    </div>
  );
}


function PlayersTab({
  teamName,
  players,
  loading,
  error,
}: {
  teamName: string;
  players: ClubPlayer[];
  loading: boolean;
  error: string | null;
}) {
  const topScorer =
    useMemo(
      () => {
        if (
          players.length
          === 0
        ) {
          return null;
        }

        return [
          ...players,
        ].sort(
          (
            first,
            second,
          ) => {
            if (
              second.goals
              !== first.goals
            ) {
              return (
                second.goals
                - first.goals
              );
            }

            return (
              second.matches
              - first.matches
            );
          },
        )[0];
      },
      [
        players,
      ],
    );

  const transferredPlayers =
    useMemo(
      () =>
        players.filter(
          (
            player,
          ) =>
            !player.is_current_club,
        ),
      [
        players,
      ],
    );

  const playersWithAppearances =
    useMemo(
      () =>
        players.filter(
          (
            player,
          ) =>
            player.matches > 0,
        ).length,
      [
        players,
      ],
    );


  if (
    loading
  ) {
    return (
      <div className="panel">
        <div className="panel-header">
          <div className="panel-icon">
            <Users
              size={18}
            />
          </div>

          <div>
            <h2>
              Jogadores
            </h2>

            <p>
              Carregando elenco de {teamName}
            </p>
          </div>
        </div>

        <div
          style={{
            minHeight:
              "220px",
            display:
              "grid",
            placeItems:
              "center",
            color:
              "#65736c",
            fontSize:
              "12px",
          }}
        >
          Consultando jogadores e
          estatísticas...
        </div>
      </div>
    );
  }


  if (
    error
  ) {
    return (
      <div className="panel">
        <div className="panel-header">
          <div className="panel-icon">
            <Users
              size={18}
            />
          </div>

          <div>
            <h2>
              Jogadores
            </h2>

            <p>
              Elenco de {teamName}
            </p>
          </div>
        </div>

        <div
          style={{
            padding:
              "28px",
            color:
              "#ff787d",
            fontSize:
              "12px",
          }}
        >
          {error}
        </div>
      </div>
    );
  }


  if (
    players.length
    === 0
  ) {
    return (
      <div className="panel">
        <div className="panel-header">
          <div className="panel-icon">
            <Users
              size={18}
            />
          </div>

          <div>
            <h2>
              Jogadores
            </h2>

            <p>
              Elenco de {teamName}
            </p>
          </div>
        </div>

        <div
          style={{
            minHeight:
              "220px",
            padding:
              "34px",
            display:
              "grid",
            placeItems:
              "center",
            textAlign:
              "center",
          }}
        >
          <div>
            <Users
              size={38}
              style={{
                color:
                  "#27d684",
                marginBottom:
                  "12px",
              }}
            />

            <h3
              style={{
                margin:
                  "0 0 8px",
              }}
            >
              Elenco ainda não sincronizado
            </h3>

            <p
              style={{
                maxWidth:
                  "480px",
                margin:
                  "0 auto",
                color:
                  "#75827c",
                fontSize:
                  "12px",
                lineHeight:
                  1.7,
              }}
            >
              Ainda não existem jogadores
              armazenados para este clube
              nesta competição.
            </p>
          </div>
        </div>
      </div>
    );
  }


  return (
    <>
      <section className="metric-grid">
        <MetricCard
          label="Elenco"
          value={
            String(
              players.length,
            )
          }
          detail="Atletas registrados"
          icon={
            <Users
              size={18}
            />
          }
        />

        <MetricCard
          label="Utilizados"
          value={
            String(
              playersWithAppearances,
            )
          }
          detail="Jogadores com partidas"
          icon={
            <UserRound
              size={18}
            />
          }
        />

        <MetricCard
          label="Artilheiro"
          value={
            topScorer
              ? (
                  topScorer.nickname
                  ?? topScorer.full_name
                )
              : "-"
          }
          detail={
            topScorer
              ? `${topScorer.goals} gols`
              : "Sem dados"
          }
          icon={
            <Goal
              size={18}
            />
          }
        />

        <MetricCard
          label="Transferidos"
          value={
            String(
              transferredPlayers.length,
            )
          }
          detail="Hoje em outro clube"
          icon={
            <Activity
              size={18}
            />
          }
        />
      </section>


      <div
        className="panel"
        style={{
          marginTop:
            "18px",
        }}
      >
        <div className="panel-header">
          <div className="panel-icon">
            <Users
              size={18}
            />
          </div>

          <div>
            <h2>
              Jogadores
            </h2>

            <p>
              Estatísticas de {teamName}
              {" "}
              na Série A
            </p>
          </div>
        </div>


        <div className="table-wrapper">
          <table>
            <thead>
              <tr>
                <th>
                  Jogador
                </th>

                <th>
                  Idade
                </th>

                <th>
                  J
                </th>

                <th>
                  G
                </th>

                <th>
                  CA
                </th>

                <th>
                  CV
                </th>

                <th>
                  Situação
                </th>

                <th>
                  CBF
                </th>
              </tr>
            </thead>

            <tbody>
              {
                players.map(
                  (
                    player,
                  ) => (
                    <PlayerRow
                      key={
                        player.player_id
                      }
                      player={
                        player
                      }
                    />
                  ),
                )
              }
            </tbody>
          </table>
        </div>
      </div>
    </>
  );
}


function PlayerRow({
  player,
}: {
  player: ClubPlayer;
}) {
  const displayName =
    player.nickname
    ?? player.full_name;

  return (
    <tr>
      <td>
        <div
          style={{
            display:
              "flex",
            flexDirection:
              "column",
            gap:
              "4px",
          }}
        >
          <strong
            style={{
              color:
                "#e5ece8",
              fontSize:
                "12px",
            }}
          >
            {displayName}
          </strong>

          {
            player.nickname
            && player.nickname
            !== player.full_name
              ? (
                  <span
                    style={{
                      color:
                        "#65736c",
                      fontSize:
                        "10px",
                    }}
                  >
                    {player.full_name}
                  </span>
                )
              : null
          }
        </div>
      </td>

      <td>
        {
          player.age
          ?? "-"
        }
      </td>

      <td>
        {player.matches}
      </td>

      <td
        className={
          player.goals > 0
            ? "points"
            : undefined
        }
      >
        {player.goals}
      </td>

      <td>
        <span
          style={{
            display:
              "inline-grid",
            placeItems:
              "center",
            minWidth:
              "24px",
            height:
              "22px",
            padding:
              "0 5px",
            borderRadius:
              "5px",
            background:
              player.yellow_cards
              > 0
                ? "rgba(246, 201, 102, 0.13)"
                : "transparent",
            color:
              player.yellow_cards
              > 0
                ? "#f6c966"
                : "#75827c",
          }}
        >
          {
            player.yellow_cards
          }
        </span>
      </td>

      <td>
        <span
          style={{
            display:
              "inline-grid",
            placeItems:
              "center",
            minWidth:
              "24px",
            height:
              "22px",
            padding:
              "0 5px",
            borderRadius:
              "5px",
            background:
              player.red_cards
              > 0
                ? "rgba(255, 120, 125, 0.13)"
                : "transparent",
            color:
              player.red_cards
              > 0
                ? "#ff787d"
                : "#75827c",
          }}
        >
          {
            player.red_cards
          }
        </span>
      </td>

      <td>
        {
          player.is_current_club
            ? (
                <span
                  style={{
                    display:
                      "inline-flex",
                    alignItems:
                      "center",
                    gap:
                      "5px",
                    padding:
                      "5px 8px",
                    borderRadius:
                      "999px",
                    background:
                      "rgba(39, 214, 134, 0.10)",
                    color:
                      "#5cefa7",
                    fontSize:
                      "9px",
                    fontWeight:
                      700,
                    whiteSpace:
                      "nowrap",
                  }}
                >
                  No clube
                </span>
              )
            : (
                <span
                  style={{
                    display:
                      "inline-flex",
                    alignItems:
                      "center",
                    gap:
                      "5px",
                    padding:
                      "5px 8px",
                    borderRadius:
                      "999px",
                    background:
                      "rgba(107, 184, 255, 0.10)",
                    color:
                      "#6bb8ff",
                    fontSize:
                      "9px",
                    fontWeight:
                      700,
                    whiteSpace:
                      "nowrap",
                  }}
                >
                  Atualmente{" "}
                  {
                    player.current_club_name
                    ?? "em outro clube"
                  }
                </span>
              )
        }
      </td>

      <td>
        {
          player.profile_url
            ? (
                <a
                  href={
                    player.profile_url
                  }
                  target="_blank"
                  rel="noreferrer"
                  aria-label={
                    `Abrir perfil de ${displayName} na CBF`
                  }
                  style={{
                    display:
                      "inline-flex",
                    alignItems:
                      "center",
                    justifyContent:
                      "center",
                    width:
                      "28px",
                    height:
                      "28px",
                    border:
                      "1px solid #20282e",
                    borderRadius:
                      "7px",
                    color:
                      "#829089",
                    textDecoration:
                      "none",
                    background:
                      "#11181d",
                  }}
                >
                  <ExternalLink
                    size={13}
                  />
                </a>
              )
            : (
                <span
                  style={{
                    color:
                      "#4d5a54",
                  }}
                >
                  -
                </span>
              )
        }
      </td>
    </tr>
  );
}


function StatsTab({
  team,
  recentForm,
}: {
  team: Standing;
  recentForm:
    RecentForm | null;
}) {
  const goalsPerMatch =
    team.matches
    > 0
      ? (
          team.goals_for
          / team.matches
        )
      : 0;

  const goalsAgainstPerMatch =
    team.matches
    > 0
      ? (
          team.goals_against
          / team.matches
        )
      : 0;

  return (
    <>
      <section className="metric-grid">
        <MetricCard
          label="Vitórias"
          value={
            String(
              team.wins,
            )
          }
          detail={`${team.matches} jogos`}
          icon={
            <Trophy
              size={18}
            />
          }
        />

        <MetricCard
          label="Gols por jogo"
          value={
            goalsPerMatch.toFixed(
              2,
            )
          }
          detail={`${team.goals_for} gols marcados`}
          icon={
            <Goal
              size={18}
            />
          }
        />

        <MetricCard
          label="Gols sofridos / jogo"
          value={
            goalsAgainstPerMatch.toFixed(
              2,
            )
          }
          detail={`${team.goals_against} sofridos`}
          icon={
            <Shield
              size={18}
            />
          }
        />

        <MetricCard
          label="Forma recente"
          value={
            recentForm?.form
            || "-"
          }
          detail="Últimos 5 jogos"
          icon={
            <Activity
              size={18}
            />
          }
        />
      </section>


      <div
        className="panel"
        style={{
          marginTop:
            "18px",
        }}
      >
        <div className="panel-header">
          <div className="panel-icon">
            <BarChart3
              size={18}
            />
          </div>

          <div>
            <h2>
              Campanha
            </h2>

            <p>
              Números gerais do campeonato
            </p>
          </div>
        </div>

        <div className="table-wrapper">
          <table>
            <thead>
              <tr>
                <th>
                  J
                </th>

                <th>
                  V
                </th>

                <th>
                  E
                </th>

                <th>
                  D
                </th>

                <th>
                  GP
                </th>

                <th>
                  GC
                </th>

                <th>
                  SG
                </th>

                <th>
                  PTS
                </th>

                <th>
                  APR
                </th>
              </tr>
            </thead>

            <tbody>
              <tr>
                <td>
                  {team.matches}
                </td>

                <td>
                  {team.wins}
                </td>

                <td>
                  {team.draws}
                </td>

                <td>
                  {team.losses}
                </td>

                <td>
                  {team.goals_for}
                </td>

                <td>
                  {team.goals_against}
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
                  {team.points}
                </td>

                <td>
                  {
                    team.performance_pct.toFixed(
                      1,
                    )
                  }%
                </td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>
    </>
  );
}


function MetricCard({
  label,
  value,
  detail,
  icon,
}: {
  label: string;
  value: string;
  detail: string;
  icon:
    React.ReactNode;
}) {
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


function ResultBadge({
  result,
}: {
  result: string;
}) {
  const normalized =
    result.toUpperCase();

  const background =
    normalized
    === "V"
      ? "rgba(29, 205, 123, 0.13)"
      : normalized
      === "E"
        ? "rgba(222, 164, 50, 0.13)"
        : "rgba(233, 67, 78, 0.13)";

  const color =
    normalized
    === "V"
      ? "#5cefa7"
      : normalized
      === "E"
        ? "#f6c966"
        : "#ff787d";

  return (
    <span
      style={{
        width:
          "28px",
        height:
          "28px",
        display:
          "grid",
        placeItems:
          "center",
        borderRadius:
          "7px",
        background,
        color,
        fontSize:
          "10px",
        fontWeight:
          800,
      }}
    >
      {normalized}
    </span>
  );
}


function SimpleMatch({
  match,
  prediction,
}: {
  match:
    ChampionshipMatch;
  prediction?:
    MatchPrediction;
}) {
  const played =
    match.status
    === "played";

  return (
    <div
      style={{
        padding:
          "14px",
        border:
          "1px solid #20282e",
        borderRadius:
          "11px",
        background:
          "#11181d",
      }}
    >
      <div
        style={{
          display:
            "flex",
          justifyContent:
            "space-between",
          alignItems:
            "center",
          gap:
            "10px",
          marginBottom:
            "12px",
          color:
            "#718078",
          fontSize:
            "10px",
        }}
      >
        <span>
          Rodada{" "}
          {match.round}
        </span>

        <span
          style={{
            color:
              played
                ? "#5cefa7"
                : "#6bb8ff",
          }}
        >
          {
            played
              ? "Finalizado"
              : "Próximo"
          }
        </span>
      </div>


      <div
        style={{
          display:
            "grid",
          gridTemplateColumns:
            "minmax(0, 1fr) auto minmax(0, 1fr)",
          alignItems:
            "center",
          gap:
            "14px",
        }}
      >
        <strong
          style={{
            fontSize:
              "13px",
          }}
        >
          {match.home_team}
        </strong>

        <div
          style={{
            display:
              "flex",
            alignItems:
              "center",
            gap:
              "8px",
            color:
              "#eff8f3",
            fontWeight:
              800,
          }}
        >
          {
            played
              ? (
                  <>
                    <span>
                      {match.home_goals}
                    </span>

                    <span
                      style={{
                        color:
                          "#65736c",
                      }}
                    >
                      x
                    </span>

                    <span>
                      {match.away_goals}
                    </span>
                  </>
                )
              : (
                  <span
                    style={{
                      color:
                        "#65736c",
                    }}
                  >
                    x
                  </span>
                )
          }
        </div>

        <strong
          style={{
            textAlign:
              "right",
            fontSize:
              "13px",
          }}
        >
          {match.away_team}
        </strong>
      </div>


      {
        !played
        && prediction
          ? (
              <div
                style={{
                  marginTop:
                    "13px",
                  padding:
                    "10px",
                  display:
                    "grid",
                  gridTemplateColumns:
                    "repeat(3, 1fr)",
                  gap:
                    "8px",
                  borderRadius:
                    "8px",
                  background:
                    "rgba(39, 214, 134, 0.05)",
                  color:
                    "#829089",
                  fontSize:
                    "10px",
                  textAlign:
                    "center",
                }}
              >
                <span>
                  Casa{" "}
                  <strong
                    style={{
                      color:
                        "#e5ece8",
                    }}
                  >
                    {
                      prediction.home_probability_pct.toFixed(
                        1,
                      )
                    }%
                  </strong>
                </span>

                <span>
                  Empate{" "}
                  <strong
                    style={{
                      color:
                        "#e5ece8",
                    }}
                  >
                    {
                      prediction.draw_probability_pct.toFixed(
                        1,
                      )
                    }%
                  </strong>
                </span>

                <span>
                  Fora{" "}
                  <strong
                    style={{
                      color:
                        "#e5ece8",
                    }}
                  >
                    {
                      prediction.away_probability_pct.toFixed(
                        1,
                      )
                    }%
                  </strong>
                </span>
              </div>
            )
          : null
      }


      <div
        style={{
          marginTop:
            "12px",
          display:
            "flex",
          gap:
            "14px",
          flexWrap:
            "wrap",
          color:
            "#65736c",
          fontSize:
            "10px",
        }}
      >
        <span
          style={{
            display:
              "inline-flex",
            gap:
              "5px",
            alignItems:
              "center",
          }}
        >
          <CalendarDays
            size={12}
          />

          {
            formatDate(
              match.date,
            )
          }
        </span>

        <span
          style={{
            display:
              "inline-flex",
            gap:
              "5px",
            alignItems:
              "center",
          }}
        >
          <Clock3
            size={12}
          />

          {
            formatTime(
              match.time,
            )
          }
        </span>

        <span
          style={{
            display:
              "inline-flex",
            gap:
              "5px",
            alignItems:
              "center",
          }}
        >
          <MapPin
            size={12}
          />

          {
            buildLocation(
              match,
            )
          }
        </span>
      </div>
    </div>
  );
}


function formatDate(
  value:
    string | null,
) {
  if (
    !value
  ) {
    return "Data a definir";
  }

  const parsed =
    new Date(
      `${value}T12:00:00`,
    );

  if (
    Number.isNaN(
      parsed.getTime(),
    )
  ) {
    return value;
  }

  return new Intl.DateTimeFormat(
    "pt-BR",
    {
      day:
        "2-digit",
      month:
        "2-digit",
      year:
        "numeric",
    },
  ).format(
    parsed,
  );
}


function formatTime(
  value:
    string | null,
) {
  if (
    !value
  ) {
    return "Horário a definir";
  }

  return value.slice(
    0,
    5,
  );
}


function buildLocation(
  match:
    ChampionshipMatch,
) {
  const parts = [
    match.venue,
    match.city,
    match.state,
  ].filter(
    Boolean,
  );

  return (
    parts.join(
      " • ",
    )
    || "Local a definir"
  );
}


export default ClubDetailsPage;