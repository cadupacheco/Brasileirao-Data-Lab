import {
  Activity,
  Goal,
  Shield,
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


function ClubsPage() {
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
      async function loadClubs() {
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
            "Não foi possível carregar os clubes.",
          );
        } finally {
          setLoading(false);
        }
      }

      loadClubs();
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
              Carregando clubes...
            </h2>

            <p>
              Consultando dados do campeonato.
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
            Clubes
          </h1>

          <p>
            Desempenho dos participantes
            da Série A {summary.season}.
          </p>
        </div>

        <div className="round-badge">
          <Shield size={17} />

          {standings.length} clubes
        </div>
      </header>


      <section className="clubs-grid">
        {
          standings.map(
            (
              team,
            ) => (
              <article
                className="club-card"
                key={
                  team.team_id
                }
              >
                <div className="club-card-header">
                  <div className="club-position">
                    {
                      team.position
                    }º
                  </div>

                  <div className="club-badge">
                    <Shield size={21} />
                  </div>
                </div>


                <div className="club-title">
                  <h2>
                    {
                      team.team
                    }
                  </h2>

                  <span>
                    {
                      team.points
                    } pontos
                  </span>
                </div>


                <div className="club-main-stat">
                  <strong>
                    {
                      team.performance_pct.toFixed(
                        1,
                      )
                    }%
                  </strong>

                  <span>
                    aproveitamento
                  </span>
                </div>


                <div className="club-stats">
                  <ClubStat
                    label="Jogos"
                    value={
                      team.matches
                    }
                  />

                  <ClubStat
                    label="Vitórias"
                    value={
                      team.wins
                    }
                  />

                  <ClubStat
                    label="Empates"
                    value={
                      team.draws
                    }
                  />

                  <ClubStat
                    label="Derrotas"
                    value={
                      team.losses
                    }
                  />
                </div>


                <div className="club-footer">
                  <div>
                    <Goal size={15} />

                    <span>
                      {
                        team.goals_for
                      } GP
                    </span>
                  </div>

                  <div>
                    <Shield size={15} />

                    <span>
                      {
                        team.goals_against
                      } GC
                    </span>
                  </div>

                  <div>
                    <Trophy size={15} />

                    <span>
                      SG{" "}
                      {
                        team.goal_difference
                        > 0
                          ? `+${team.goal_difference}`
                          : team.goal_difference
                      }
                    </span>
                  </div>
                </div>
              </article>
            ),
          )
        }
      </section>
    </>
  );
}


interface ClubStatProps {
  label: string;
  value: number;
}


function ClubStat({
  label,
  value,
}: ClubStatProps) {
  return (
    <div className="club-stat">
      <span>
        {label}
      </span>

      <strong>
        {value}
      </strong>
    </div>
  );
}


export default ClubsPage;