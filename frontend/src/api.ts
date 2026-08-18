export interface Leader {
  team_id: number;
  team: string;
  position: number;
  points: number;
}

export interface ChampionshipSummary {
  season: number;
  total_matches: number;
  played_matches: number;
  future_matches: number;
  total_goals: number;
  average_goals_per_match: number;
  home_wins: number;
  draws: number;
  away_wins: number;
  latest_played_round: number | null;
  leader: Leader | null;
}

export interface Standing {
  position: number;
  team_id: number;
  team: string;
  matches: number;
  wins: number;
  draws: number;
  losses: number;
  goals_for: number;
  goals_against: number;
  goal_difference: number;
  points: number;
  performance_pct: number;
}

export interface RecentForm {
  position: number;
  team_id: number;
  team: string;
  matches: number;
  wins: number;
  draws: number;
  losses: number;
  points: number;
  goals_for: number;
  goals_against: number;
  goal_difference: number;
  performance_pct: number;
  form: string;
}

const API_URL =
  import.meta.env.VITE_API_URL ??
  "http://127.0.0.1:8000";

async function request<T>(
  endpoint: string,
): Promise<T> {
  const response = await fetch(
    `${API_URL}${endpoint}`,
  );

  if (!response.ok) {
    throw new Error(
      `Erro HTTP ${response.status}`,
    );
  }

  return response.json() as Promise<T>;
}

export function getChampionshipSummary() {
  return request<ChampionshipSummary>(
    "/api/championship/summary",
  );
}

export function getStandings() {
  return request<Standing[]>(
    "/api/standings",
  );
}

export function getRecentForm() {
  return request<RecentForm[]>(
    "/api/recent-form?last_n=5",
  );
}
