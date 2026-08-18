from __future__ import annotations

import pytest

from brasileirao_data_lab.database.validate_analytics import (
    ANALYTICS_SECTIONS,
    print_validation_result,
    raise_for_analytics_validation,
)


# =============================================================================
# Validação aprovada
# =============================================================================


def test_raise_for_analytics_validation_accepts_match():
    result = {
        "exact_match": True,
        "sections": {
            "summary": True,
            "standings": True,
            "home_away": True,
            "recent_form": True,
            "position_history": True,
        },
    }

    raise_for_analytics_validation(
        result
    )


# =============================================================================
# Validação rejeitada
# =============================================================================


def test_raise_for_analytics_validation_rejects_difference():
    result = {
        "exact_match": False,
        "sections": {
            "summary": True,
            "standings": False,
            "home_away": True,
            "recent_form": False,
            "position_history": True,
        },
    }

    with pytest.raises(
        ValueError,
        match="standings, recent_form",
    ):

        raise_for_analytics_validation(
            result
        )


# =============================================================================
# Saída aprovada
# =============================================================================


def test_print_validation_result_success(
    capsys,
):
    result = {
        "exact_match": True,
        "sections": {
            section: True
            for section
            in ANALYTICS_SECTIONS
        },
    }

    print_validation_result(
        result
    )

    output = (
        capsys.readouterr().out
    )

    assert (
        "summary"
        in output
    )

    assert (
        "standings"
        in output
    )

    assert (
        "recent_form"
        in output
    )

    assert (
        "mesmos resultados analíticos"
        in output
    )


# =============================================================================
# Saída com divergência
# =============================================================================


def test_print_validation_result_difference(
    capsys,
):
    result = {
        "exact_match": False,
        "sections": {
            "summary": True,
            "standings": False,
            "home_away": True,
            "recent_form": True,
            "position_history": True,
        },
    }

    print_validation_result(
        result
    )

    output = (
        capsys.readouterr().out
    )

    assert (
        "DIFERENTE"
        in output
    )

    assert (
        "divergências"
        in output
    )