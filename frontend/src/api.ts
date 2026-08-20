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

export interface EvolutionPoint {
  season: number;
  round: number;
  team_id: number;
  team: string;
  position: number;
  matches: number;
  points: number;
  wins: number;
  draws: number;
  losses: number;
  goals_for: number;
  goals_against: number;
  goal_difference: number;
  performance_pct: number;
}

export interface UpdateStatus {
  season: number;
  source: string;
  status: string;
  last_sync_at_utc: string;
  total_matches: number;
  played_matches: number;
  future_matches: number;
  automation_enabled: boolean;
  checks_per_day: number;
}

export type MatchStatus =
  | "all"
  | "played"
  | "upcoming";

export interface ChampionshipMatch {
  match_id: number;
  season: number;
  round: number;
  match_number: number | null;
  date: string | null;
  time: string | null;

  home_team_id: number;
  home_team: string;
  home_goals: number | null;

  away_team_id: number;
  away_team: string;
  away_goals: number | null;

  venue: string | null;
  city: string | null;
  state: string | null;

  status:
    | "played"
    | "upcoming";
}

export interface MatchFilters {
  roundNumber?: number;
  teamId?: number;
  status?: MatchStatus;
}

export type PredictionResult =
  | "HOME"
  | "DRAW"
  | "AWAY";

export interface MatchPrediction {
  season: number;
  round: number;
  match_id: number;
  date: string | null;
  time: string | null;

  home_team_id: number;
  home_team: string;
  home_team_key: string;

  away_team_id: number;
  away_team: string;
  away_team_key: string;

  home_probability: number;
  draw_probability: number;
  away_probability: number;

  predicted_result: PredictionResult;

  home_probability_pct: number;
  draw_probability_pct: number;
  away_probability_pct: number;
}

export interface PredictionFilters {
  roundNumber?: number;
  teamId?: number;
}

export interface StandingPrediction {
  projected_position: number;
  season: number;
  team_key: string;
  team_name: string;
  simulations: number;

  expected_points: number;
  average_position: number;

  champion_probability: number;
  top4_probability: number;
  top6_probability: number;
  relegation_probability: number;

  champion_probability_pct: number;
  top4_probability_pct: number;
  top6_probability_pct: number;
  relegation_probability_pct: number;
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


export function getUpdateStatus() {
  return request<UpdateStatus>(
    "/api/status",
  );
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


export function getEvolution(
  teamIds?: number[],
) {
  const params =
    new URLSearchParams();

  teamIds?.forEach(
    (
      teamId,
    ) => {
      params.append(
        "team_ids",
        String(
          teamId,
        ),
      );
    },
  );

  const query =
    params.toString();

  const endpoint =
    query
      ? `/api/evolution?${query}`
      : "/api/evolution";

  return request<EvolutionPoint[]>(
    endpoint,
  );
}


export function getMatches(
  filters: MatchFilters = {},
) {
  const params =
    new URLSearchParams();

  if (
    filters.roundNumber
    !== undefined
  ) {
    params.set(
      "round_number",
      String(
        filters.roundNumber,
      ),
    );
  }

  if (
    filters.teamId
    !== undefined
  ) {
    params.set(
      "team_id",
      String(
        filters.teamId,
      ),
    );
  }

  if (
    filters.status
    && filters.status
    !== "all"
  ) {
    params.set(
      "status",
      filters.status,
    );
  }

  const query =
    params.toString();

  const endpoint =
    query
      ? `/api/matches?${query}`
      : "/api/matches";

  return request<ChampionshipMatch[]>(
    endpoint,
  );
}


export function getMatchPredictions(
  filters: PredictionFilters = {},
) {
  const params =
    new URLSearchParams();

  if (
    filters.roundNumber
    !== undefined
  ) {
    params.set(
      "round_number",
      String(
        filters.roundNumber,
      ),
    );
  }

  if (
    filters.teamId
    !== undefined
  ) {
    params.set(
      "team_id",
      String(
        filters.teamId,
      ),
    );
  }

  const query =
    params.toString();

  const endpoint =
    query
      ? `/api/predictions/matches?${query}`
      : "/api/predictions/matches";

  return request<MatchPrediction[]>(
    endpoint,
  );
}


export function getPredictionStandings() {
  return request<StandingPrediction[]>(
    "/api/predictions/standings",
  );
}