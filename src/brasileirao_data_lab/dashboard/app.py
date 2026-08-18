from __future__ import annotations

from pathlib import Path

import streamlit as st


# =============================================================================
# Configuração
# =============================================================================


st.set_page_config(
    page_title="Brasileirão Data Lab",
    page_icon="⚽",
    layout="wide",
    initial_sidebar_state="expanded",
)


# =============================================================================
# Caminhos
# =============================================================================


CURRENT_DIR = Path(__file__).resolve().parent

OVERVIEW_PAGE = (
    CURRENT_DIR
    / "pages"
    / "overview.py"
)


# =============================================================================
# Navegação
# =============================================================================


overview_page = st.Page(
    OVERVIEW_PAGE,
    title="Visão Geral",
    icon="🏠",
    default=True,
)


navigation = st.navigation(
    [
        overview_page,
    ]
)


# =============================================================================
# Sidebar
# =============================================================================


with st.sidebar:

    st.title(
        "⚽ Brasileirão Data Lab"
    )

    st.caption(
        "Campeonato Brasileiro Série A"
    )

    st.divider()

    st.caption(
        "V0.4 Dashboard"
    )


# =============================================================================
# Execução
# =============================================================================


navigation.run()