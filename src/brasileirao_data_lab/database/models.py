from __future__ import annotations

from datetime import date, time

from sqlalchemy import (
    Date,
    Float,
    ForeignKey,
    Index,
    Integer,
    String,
    Time,
)
from sqlalchemy.orm import (
    DeclarativeBase,
    Mapped,
    mapped_column,
)


# =============================================================================
# Base
# =============================================================================


class Base(
    DeclarativeBase
):
    """Classe base dos modelos ORM."""

    pass


# =============================================================================
# Times
# =============================================================================


class Team(Base):
    """
    Clube participante do campeonato.

    O team_id utiliza o identificador
    fornecido pela CBF.
    """

    __tablename__ = "teams"

    team_id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        autoincrement=False,
    )

    name: Mapped[str] = mapped_column(
        String(150),
        nullable=False,
        index=True,
    )

    def __repr__(self) -> str:

        return (
            f"Team("
            f"team_id={self.team_id!r}, "
            f"name={self.name!r}"
            f")"
        )


# =============================================================================
# Partidas
# =============================================================================


class Match(Base):
    """
    Partida do Campeonato Brasileiro.
    """

    __tablename__ = "matches"

    match_id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        autoincrement=False,
    )

    season: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
    )

    round: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
    )

    match_number: Mapped[int | None] = mapped_column(
        Integer,
        nullable=True,
    )

    group: Mapped[str | None] = mapped_column(
        String(50),
        nullable=True,
    )

    date: Mapped[date | None] = mapped_column(
        Date,
        nullable=True,
    )

    time: Mapped[time | None] = mapped_column(
        Time,
        nullable=True,
    )

    home_team_id: Mapped[int] = mapped_column(
        ForeignKey(
            "teams.team_id"
        ),
        nullable=False,
    )

    home_goals: Mapped[int | None] = mapped_column(
        Integer,
        nullable=True,
    )

    away_team_id: Mapped[int] = mapped_column(
        ForeignKey(
            "teams.team_id"
        ),
        nullable=False,
    )

    away_goals: Mapped[int | None] = mapped_column(
        Integer,
        nullable=True,
    )

    venue: Mapped[str | None] = mapped_column(
        String(200),
        nullable=True,
    )

    city: Mapped[str | None] = mapped_column(
        String(150),
        nullable=True,
    )

    state: Mapped[str | None] = mapped_column(
        String(10),
        nullable=True,
    )

    championship: Mapped[str | None] = mapped_column(
        String(150),
        nullable=True,
    )

    __table_args__ = (
        Index(
            "ix_matches_season_round",
            "season",
            "round",
        ),
        Index(
            "ix_matches_home_team",
            "home_team_id",
        ),
        Index(
            "ix_matches_away_team",
            "away_team_id",
        ),
    )

    def __repr__(self) -> str:

        return (
            f"Match("
            f"match_id={self.match_id!r}, "
            f"season={self.season!r}, "
            f"round={self.round!r}"
            f")"
        )


# =============================================================================
# Snapshots da classificação
# =============================================================================


class StandingsSnapshot(Base):
    """
    Fotografia da classificação
    de um clube ao final de uma rodada.

    A chave primária é composta por:

    season + round + team_id
    """

    __tablename__ = (
        "standings_snapshots"
    )

    season: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
    )

    round: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
    )

    team_id: Mapped[int] = mapped_column(
        ForeignKey(
            "teams.team_id"
        ),
        primary_key=True,
    )

    position: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
    )

    matches: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
    )

    wins: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
    )

    draws: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
    )

    losses: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
    )

    goals_for: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
    )

    goals_against: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
    )

    goal_difference: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
    )

    points: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
    )

    performance_pct: Mapped[float] = mapped_column(
        Float,
        nullable=False,
    )

    __table_args__ = (
        Index(
            "ix_standings_snapshots_season_round",
            "season",
            "round",
        ),
        Index(
            "ix_standings_snapshots_team",
            "team_id",
        ),
    )

    def __repr__(self) -> str:

        return (
            "StandingsSnapshot("
            f"season={self.season!r}, "
            f"round={self.round!r}, "
            f"team_id={self.team_id!r}, "
            f"position={self.position!r}, "
            f"points={self.points!r}"
            ")"
        )