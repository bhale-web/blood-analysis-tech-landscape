"""
Technology Selector - Complete Collaborative Evaluation Tool

Allows multiple evaluators to assess technology options with a data grid,
radar chart visualization, and results export.
"""

import streamlit as st
import pandas as pd
from datetime import datetime
import plotly.graph_objects as go

# ─────────────────────────────────────────────────────────────────────────────
# PAGE CONFIG
# ─────────────────────────────────────────────────────────────────────────────

st.set_page_config(
    page_title="Technology Selector",
    page_icon="⚖️",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.title("⚖️ Technology Selector")
st.markdown("Collaborate with your team to evaluate and select technologies.")

# ─────────────────────────────────────────────────────────────────────────────
# CONSTANTS
# ─────────────────────────────────────────────────────────────────────────────

TECHNOLOGIES = ["Tech A", "Tech B", "Tech C", "Tech D", "Tech E"]
CRITERIA = ["Criteria 1", "Criteria 2", "Criteria 3", "Criteria 4", "Criteria 5"]

# ─────────────────────────────────────────────────────────────────────────────
# SESSION STATE INITIALIZATION
# ─────────────────────────────────────────────────────────────────────────────

if "evaluations" not in st.session_state:
    st.session_state.evaluations = []

if "current_selections" not in st.session_state:
    st.session_state.current_selections = {
        tech: {criterion: False for criterion in CRITERIA}
        for tech in TECHNOLOGIES
    }

if "current_comment" not in st.session_state:
    st.session_state.current_comment = ""

# ─────────────────────────────────────────────────────────────────────────────
# HELPER FUNCTIONS (CACHED WHERE USEFUL)
# ─────────────────────────────────────────────────────────────────────────────

@st.cache_data
def compute_tech_scores(evaluations, technologies, criteria):
    """Aggregate scores for each technology/criterion as percentages."""
    tech_scores = {tech: [] for tech in technologies}
    if not evaluations:
        return tech_scores

    n = len(evaluations)
    for criterion in criteria:
        for tech in technologies:
            count = sum(
                1
                for ev in evaluations
                if ev["selections"][tech][criterion]
            )
            percentage = (count / n) * 100
            tech_scores[tech].append(percentage)
    return tech_scores


@st.cache_data
def build_radar_figure(tech_scores, criteria, technologies):
    """Build the radar chart figure from aggregated scores."""
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


def compute_completion_progress(current_selections, technologies, criteria):
    """Fraction of technology–criterion cells that are selected."""
    total_cells = len(technologies) * len(criteria)
    filled_cells = sum(
        1
        for tech in technologies
        for c in criteria
        if current_selections[tech][c]
    )
    return filled_cells / total_cells if total_cells else 0.0


def criteria_coverage(current_selections, technologies, criteria):
    """Whether each criterion has at least one technology selected."""
    covered = {}
    for c in criteria:
        covered[c] = any(current_selections[tech][c] for tech in technologies)
    return covered


def compute_preview_scores(evaluations, current, technologies, criteria):
    """
    Create a 'live preview' radar by combining submitted evaluations
    with current (unsent) selections.
    """
    temp_eval = {"selections": current}
    combined = list(evaluations) + [temp_eval]

    tech_scores = {tech: [] for tech in technologies}
    n = len(combined)
    if not n:
        return tech_scores

    for criterion in criteria:
        for tech in technologies:
            count = 0
            for ev in combined:
                sel = ev["selections"][tech][criterion]
                count += 1 if sel else 0
            percentage = (count / n) * 100
            tech_scores[tech].append(percentage)
    return tech_scores


@st.cache_data
def build_results_table(evaluations, technologies):
    rows = []
    for ev in evaluations:
        row = {
            "Evaluator": ev["evaluator_name"],
            "Timestamp": ev["timestamp"],
            "Comments": ev["comments"] if ev["comments"] else "(no comments)",
        }
        selected_techs = [
            tech for tech in technologies
            if any(ev["selections"][tech].values())
        ]
        row["Selected Technologies"] = (
            ", ".join(selected_techs) if selected_techs else "(none selected)"
        )
        rows.append(row)
    return pd.DataFrame(rows)


@st.cache_data
def build_detailed_csv(evaluations, technologies, criteria):
    csv_rows = []
    for ev in evaluations:
        for tech in technologies:
            row = {
                "Evaluator": ev["evaluator_name"],
                "Timestamp": ev["timestamp"],
                "Technology": tech,
                "Comments": ev["comments"],
            }
            for criterion in criteria:
                row[criterion] = "✓" if ev["selections"][tech][criterion] else ""
            csv_rows.append(row)
    csv_df = pd.DataFrame(csv_rows)
    return csv_df.to_csv(index=False)


@st.cache_data
def build_summary_csv(results_df):
    return results_df.to_csv(index=False)


# ─────────────────────────────────────────────────────────────────────────────
# SIDEBAR: EVALUATOR INFO & INSTRUCTIONS
# ─────────────────────────────────────────────────────────────────────────────

st.sidebar.markdown("## Your Evaluation")
st.sidebar.markdown("---")

evaluator_name = st.sidebar.text_input(
    "Your name",
    placeholder="Enter your name for tracking",
    key="evaluator_input",
)

st.sidebar.markdown("---")
st.sidebar.markdown("### Instructions")
st.sidebar.markdown(
    """
1. **Select** which technologies meet each criterion by clicking cells in the table  
2. **Add comments** about your selections  
3. **Submit** your evaluation  
4. View the **radar chart** update in real-time
"""
)

# ─────────────────────────────────────────────────────────────────────────────
# MAIN: EVALUATION TABLE
# ─────────────────────────────────────────────────────────────────────────────

st.markdown("## Evaluation Grid")
st.markdown(
    "Click cells to toggle ✓ for each technology that meets the criterion."
)

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

# Update session state with edited values
for idx, tech in enumerate(TECHNOLOGIES):
    for criterion in CRITERIA:
        st.session_state.current_selections[tech][criterion] = edited_df.loc[
            idx, criterion
        ]

# ─────────────────────────────────────────────────────────────────────────────
# LIVE COMPLETION & COVERAGE
# ─────────────────────────────────────────────────────────────────────────────

progress = compute_completion_progress(
    st.session_state.current_selections,
    TECHNOLOGIES,
    CRITERIA,
)
st.progress(progress)
st.caption(f"{int(progress * 100)}% of technology–criterion cells are selected.")

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

# ─────────────────────────────────────────────────────────────────────────────
# COMMENTS SECTION
# ─────────────────────────────────────────────────────────────────────────────

st.markdown("## Comments")
comment_text = st.text_area(
    "Add any comments about your selections (optional)",
    placeholder="E.g., 'Tech A is preferred because...', 'Tech C needs more evaluation...'",
    height=100,
    key="comments_area",
)

# ─────────────────────────────────────────────────────────────────────────────
# SUBMIT BUTTON
# ─────────────────────────────────────────────────────────────────────────────

col1, col2, col3 = st.columns([1, 1, 1])
with col2:
    if st.button("✅ Submit Evaluation", use_container_width=True, type="primary"):
        if not evaluator_name.strip():
            st.error("Please enter your name before submitting.")
        else:
            evaluation = {
                "evaluator_name": evaluator_name.strip(),
                "timestamp": datetime.now().isoformat(timespec="seconds"),
                "selections": st.session_state.current_selections.copy(),
                "comments": comment_text.strip(),
            }
            st.session_state.evaluations.append(evaluation)

            # Clear form for next evaluator
            st.session_state.current_selections = {
                tech: {criterion: False for criterion in CRITERIA}
                for tech in TECHNOLOGIES
            }
            st.session_state.current_comment = ""
            st.success(
                f"✅ Thank you, {evaluator_name}! Your evaluation has been submitted."
            )
            st.balloons()

# ─────────────────────────────────────────────────────────────────────────────
# RESULTS SECTION
# ─────────────────────────────────────────────────────────────────────────────

st.divider()
st.markdown("## Results & Analysis")

if st.session_state.evaluations:
    # Live radar preview including current selections
    st.markdown("### Live Technology Match Preview (including your current selections)")
    preview_scores = compute_preview_scores(
        st.session_state.evaluations,
        st.session_state.current_selections,
        TECHNOLOGIES,
        CRITERIA,
    )
    preview_fig = build_radar_figure(preview_scores, CRITERIA, TECHNOLOGIES)
    st.plotly_chart(preview_fig, use_container_width=True)

    # Radar based on submitted evaluations only
    st.markdown("### Submitted Technology Match Scores")
    tech_scores = compute_tech_scores(
        st.session_state.evaluations,
        TECHNOLOGIES,
        CRITERIA,
    )
    fig = build_radar_figure(tech_scores, CRITERIA, TECHNOLOGIES)
    st.plotly_chart(fig, use_container_width=True)

    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Total Evaluators", len(st.session_state.evaluations))
    with col2:
        st.metric("Criteria Assessed", len(CRITERIA))
    with col3:
        st.metric("Technologies Evaluated", len(TECHNOLOGIES))

    st.markdown("### All Evaluations")
    results_df = build_results_table(
        st.session_state.evaluations,
        TECHNOLOGIES,
    )
    with st.expander("Show all evaluations", expanded=True):
        st.dataframe(results_df, use_container_width=True, hide_index=True)

    # CSV EXPORTS
    st.markdown("### Export Results")
    csv_buffer = build_detailed_csv(
        st.session_state.evaluations,
        TECHNOLOGIES,
        CRITERIA,
    )
    st.download_button(
        label="📥 Download Results as CSV",
        data=csv_buffer,
        file_name=f"technology_evaluation_{datetime.now().strftime('%Y-%m-%d_%H-%M-%S')}.csv",
        mime="text/csv",
        use_container_width=True,
    )

    summary_csv = build_summary_csv(results_df)
    st.download_button(
        label="📄 Download Summary CSV",
        data=summary_csv,
        file_name=f"technology_evaluation_summary_{datetime.now().strftime('%Y-%m-%d_%H-%M-%S')}.csv",
        mime="text/csv",
        use_container_width=True,
    )
else:
    st.info("No evaluations submitted yet. Start evaluating above to see results!")

# ─────────────────────────────────────────────────────────────────────────────
# FOOTER
# ─────────────────────────────────────────────────────────────────────────────

st.divider()
st.markdown(
    """
---
### How to Share with Your Team

1. **Share the URL** of this app with your team members.  
2. Each person can independently:  
   - Enter their name  
   - Select technologies that match each criterion  
   - Add comments about their choices  
   - Submit their evaluation  
3. **Results update in real-time** as team members submit.  
4. Use the radar chart to see which technologies score highest across criteria.  
5. **Download results** for further analysis or record-keeping.  

---

**Technology Selector** | Built with [Streamlit](https://streamlit.io) | Evaluations are stored in session memory
"""
)
