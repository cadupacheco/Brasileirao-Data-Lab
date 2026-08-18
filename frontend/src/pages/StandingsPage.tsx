import {
  Activity,
  Trophy,
} from "lucide-react";

import {
  useEffect,
  useState,
} from "react";

import {
  getChampionshipSummary,
  getStandings,
} from "../api";

import type {
  ChampionshipSummary,
  Standing,
} from "../api";


function StandingsPage() {
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
            "Não foi possível carregar a classificação.",
          );
        } finally {
          setLoading(false);
        }
      }

      loadPage();
    },
    [],
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
              Carregando classificação...
            </h2>

            <p>
              Consultando o FastAPI.
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
            Classificação
          </h1>

          <p>
            Tabela completa da Série A{" "}
            {summary.season}.
          </p>
        </div>

        <div className="round-badge">
          <Trophy size={17} />

          Rodada{" "}
          {
            summary.latest_played_round
            ?? "-"
          }
        </div>
      </header>


      <section className="panel">
        <div className="panel-header">
          <div className="panel-icon">
            <Trophy size={19} />
          </div>

          <div>
            <h2>
              Brasileirão Série A
            </h2>

            <p>
              Classificação calculada pelo
              Brasileirão Data Lab
            </p>
          </div>
        </div>


        <div className="table-wrapper">
          <table>
            <thead>
              <tr>
                <th>
                  Pos
                </th>

                <th>
                  Clube
                </th>

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
                  %
                </th>

                <th>
                  PTS
                </th>
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
                          team.goals_for
                        }
                      </td>

                      <td>
                        {
                          team.goals_against
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

                      <td>
                        {
                          team.performance_pct.toFixed(
                            1,
                          )
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
      </section>
    </>
  );
}


function PositionBadge({
  position,
}: {
  position: number;
}) {
  let className =
    "position";

  if (
    position <= 4
  ) {
    className +=
      " champions";
  } else if (
    position <= 6
  ) {
    className +=
      " continental";
  } else if (
    position >= 17
  ) {
    className +=
      " relegation";
  }

  return (
    <span className={className}>
      {position}
    </span>
  );
}


export default StandingsPage;