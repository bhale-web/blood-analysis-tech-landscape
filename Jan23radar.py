"""
Technology Selector - Live Radar (No Submit Button)

The radar chart always reflects the current selections in the grid.
"""

import streamlit as st
import pandas as pd
import plotly.graph_objects as go

# ─────────────────────────────────────────────────────────────────────────────
# PAGE CONFIG
# ─────────────────────────────────────────────────────────────────────────────

st.set_page_config(
    page_title="Technology Selector",
    page_icon="⚖️",
    layout="wide",
)

st.title("⚖️ Technology Selector")
st.markdown(
    "Use the grid below to mark which technologies meet each criterion. "
    "The radar chart updates live as you edit."
)

# ─────────────────────────────────────────────────────────────────────────────
# CONSTANTS
# ─────────────────────────────────────────────────────────────────────────────

TECHNOLOGIES = ["Tech A", "Tech B", "Tech C", "Tech D", "Tech E"]
CRITERIA = ["Criteria 1", "Criteria 2", "Criteria 3", "Criteria 4", "Criteria 5"]

# ─────────────────────────────────────────────────────────────────────────────
# SESSION STATE INITIALIZATION
# ─────────────────────────────────────────────────────────────────────────────

if "current_selections" not in st.session_state:
    st.session_state.current_selections = {
        tech: {criterion: False for criterion in CRITERIA}
        for tech in TECHNOLOGIES
    }

# Optional: keep lightweight snapshots of previous configurations
if "snapshots" not in st.session_state:
    st.session_state.snapshots = []  # each snapshot is a dict of selections


# ─────────────────────────────────────────────────────────────────────────────
# HELPER FUNCTIONS
# ─────────────────────────────────────────────────────────────────────────────

def compute_completion_progress(current_selections, technologies, criteria):
    total_cells = len(technologies) * len(criteria)
    filled_cells = sum(
        1
        for tech in technologies
        for c in criteria
        if current_selections[tech][c]
    )
    return filled_cells / total_cells if total_cells else 0.0


def criteria_coverage(current_selections, technologies, criteria):
    covered = {}
    for c in criteria:
        covered[c] = any(current_selections[tech][c] for tech in technologies)
    return covered


def compute_live_scores(current_selections, technologies, criteria):
    """
    For a single 'live' evaluator: treat each checked box as 1, unchecked as 0,
    and normalize to 0–100 just by using the boolean (i.e. 100 if checked, 0 if not).
    If you'd rather use 0/1 instead of 0/100, change 100 to 1 below.
    """
    tech_scores = {tech: [] for tech in technologies}
    for criterion in criteria:
        for tech in technologies:
            value = 100 if current_selections[tech][criterion] else 0
            tech_scores[tech].append(value)
    return tech_scores


def build_radar_figure(tech_scores, criteria, technologies):
    colors = {
        "Tech A": "#1f86b8",
        "Tech B": "#e67e22",
        "Tech C": "#27ae60",
        "Tech D": "#8e44ad",
        "Tech E": "#e74c3c",
    }
    fig = go.Figure()
    for tech in technologies:
        fig.add_trace(
            go.Scatterpolar(
                r=tech_scores[tech],
                theta=criteria,
                fill="toself",
                name=tech,
                line=dict(color=colors.get(tech, "#999")),
                marker=dict(size=8),
            )
        )

    fig.update_layout(
        polar=dict(
            radialaxis=dict(
                visible=True,
                range=[0, 100],
                ticksuffix="%",
            )
        ),
        showlegend=True,
        height=500,
        font=dict(size=12),
        hovermode="closest",
    )
    return fig


def take_snapshot():
    # Store a shallow snapshot of the current selections
    snap = {
        tech: {c: v for c, v in st.session_state.current_selections[tech].items()}
        for tech in TECHNOLOGIES
    }
    st.session_state.snapshots.append(snap)


# ─────────────────────────────────────────────────────────────────────────────
# MAIN LAYOUT
# ─────────────────────────────────────────────────────────────────────────────

left_col, right_col = st.columns([1.2, 1])

with left_col:
    st.markdown("### Evaluation Grid")
    st.markdown(
        "Click cells to toggle ✓ for each technology that meets each criterion."
    )

    # Build table from session_state
    table_data = []
    for tech in TECHNOLOGIES:
        row = {"Technology": tech}
        for criterion in CRITERIA:
            row[criterion] = st.session_state.current_selections[tech][criterion]
        table_data.append(row)

    table_df = pd.DataFrame(table_data)

    edited_df = st.data_editor(
        table_df,
        column_config={
            "Technology": st.column_config.TextColumn(
                width=120,
                disabled=True,
            ),
            **{
                criterion: st.column_config.CheckboxColumn(
                    criterion,
                    help=f"Does {criterion} apply to this technology?",
                    width=100,
                )
                for criterion in CRITERIA
            },
        },
        hide_index=True,
        use_container_width=True,
        key="evaluation_table",
    )

    # Update state from edits
    for idx, tech in enumerate(TECHNOLOGIES):
        for criterion in CRITERIA:
            st.session_state.current_selections[tech][criterion] = bool(
                edited_df.loc[idx, criterion]
            )

    # Live completion and coverage
    progress = compute_completion_progress(
        st.session_state.current_selections,
        TECHNOLOGIES,
        CRITERIA,
    )
    st.progress(progress)
    st.caption(
        f"{int(progress * 100)}% of technology–criterion cells are selected."
    )

    coverage = criteria_coverage(
        st.session_state.current_selections,
        TECHNOLOGIES,
        CRITERIA,
    )
    all_covered = all(coverage.values())
    if all_covered:
        st.success("All criteria have at least one technology selected.")
    else:
        missing = [c for c, ok in coverage.items() if not ok]
        st.warning(
            "Some criteria have no selected technologies: " + ", ".join(missing)
        )

with right_col:
    st.markdown("### Live Technology Match Radar")

    live_scores = compute_live_scores(
        st.session_state.current_selections,
        TECHNOLOGIES,
        CRITERIA,
    )
    fig = build_radar_figure(live_scores, CRITERIA, TECHNOLOGIES)
    st.plotly_chart(fig, use_container_width=True)

    # Optional snapshot button
    st.markdown("#### Optional: Save this configuration")
    st.button("📸 Save snapshot", on_click=take_snapshot)

    if st.session_state.snapshots:
        st.markdown("Saved snapshots:")
        st.write(f"{len(st.session_state.snapshots)} snapshot(s) stored this session.")


st.divider()
st.markdown(
    """
**Notes**

- The radar chart is always in sync with the grid (no submit needed).  
- Snapshots are kept only in browser session memory and are cleared when the app is reloaded.
"""
)
