"""
Technology Selector - Complete Collaborative Evaluation Tool
Allows multiple evaluators to assess technology options with a data grid,
radar chart visualization, and results export.
"""

import streamlit as st
import pandas as pd
import json
from datetime import datetime
import numpy as np
import plotly.graph_objects as go

# Page configuration
st.set_page_config(
    page_title="Technology Selector",
    page_icon="⚖️",
    layout="wide",
    initial_sidebar_state="expanded"
)

st.title("⚖️ Technology Selector")
st.markdown("Collaborate with your team to evaluate and select technologies.")

# ─────────────────────────────────────────────────────────────────────────────
# SESSION STATE INITIALIZATION
# ─────────────────────────────────────────────────────────────────────────────

# Define the technologies and criteria
TECHNOLOGIES = ["Tech A", "Tech B", "Tech C", "Tech D", "Tech E"]
CRITERIA = ["Criteria 1", "Criteria 2", "Criteria 3", "Criteria 4", "Criteria 5"]

# Initialize session state for storing evaluations
if "evaluations" not in st.session_state:
    st.session_state.evaluations = []

if "current_evaluator" not in st.session_state:
    st.session_state.current_evaluator = None

if "current_selections" not in st.session_state:
    st.session_state.current_selections = {tech: {criterion: False for criterion in CRITERIA} for tech in TECHNOLOGIES}

if "current_comment" not in st.session_state:
    st.session_state.current_comment = ""

# ─────────────────────────────────────────────────────────────────────────────
# SIDEBAR: EVALUATOR INFO & SUBMISSION
# ─────────────────────────────────────────────────────────────────────────────

st.sidebar.markdown("## Your Evaluation")
st.sidebar.markdown("---")

evaluator_name = st.sidebar.text_input(
    "Your name",
    placeholder="Enter your name for tracking",
    key="evaluator_input"
)

st.sidebar.markdown("---")
st.sidebar.markdown("### Instructions")
st.sidebar.markdown("""
1. **Select** which technologies meet each criterion by clicking cells in the table
2. **Add comments** about your selections
3. **Submit** your evaluation
4. View the **radar chart** update in real-time
""")

# ─────────────────────────────────────────────────────────────────────────────
# MAIN: EVALUATION TABLE (EDITABLE GRID)
# ─────────────────────────────────────────────────────────────────────────────

st.markdown("## Evaluation Grid")
st.markdown("Click cells to toggle ✓ for each technology that meets the criterion.")

# Create a data structure for the editable table
table_data = []
for tech in TECHNOLOGIES:
    row = {"Technology": tech}
    for criterion in CRITERIA:
        row[criterion] = st.session_state.current_selections[tech][criterion]
    table_data.append(row)

table_df = pd.DataFrame(table_data)

# Display editable data editor
edited_df = st.data_editor(
    table_df,
    column_config={
        "Technology": st.column_config.TextColumn(width=120, disabled=True),
        **{
            criterion: st.column_config.CheckboxColumn(
                criterion,
                help=f"Does {criterion} apply to this technology?",
                width=100
            )
            for criterion in CRITERIA
        }
    },
    hide_index=True,
    use_container_width=True,
    key="evaluation_table"
)

# Update session state with edited values
for idx, tech in enumerate(TECHNOLOGIES):
    for criterion in CRITERIA:
        st.session_state.current_selections[tech][criterion] = edited_df.loc[idx, criterion]

# ─────────────────────────────────────────────────────────────────────────────
# COMMENTS SECTION
# ─────────────────────────────────────────────────────────────────────────────

st.markdown("## Comments")
comment_text = st.text_area(
    "Add any comments about your selections (optional)",
    placeholder="E.g., 'Tech A is preferred because...', 'Tech C needs more evaluation...'",
    height=100,
    key="comments_area"
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
            # Create evaluation record
            evaluation = {
                "evaluator_name": evaluator_name.strip(),
                "timestamp": datetime.now().isoformat(timespec="seconds"),
                "selections": st.session_state.current_selections.copy(),
                "comments": comment_text.strip()
            }
            
            # Add to evaluations list
            st.session_state.evaluations.append(evaluation)
            
            # Clear form
            st.session_state.current_selections = {
                tech: {criterion: False for criterion in CRITERIA} 
                for tech in TECHNOLOGIES
            }
            st.session_state.current_comment = ""
            
            st.success(f"✅ Thank you, {evaluator_name}! Your evaluation has been submitted.")
            st.balloons()

# ─────────────────────────────────────────────────────────────────────────────
# RESULTS SECTION
# ─────────────────────────────────────────────────────────────────────────────

st.divider()
st.markdown("## Results & Analysis")

if st.session_state.evaluations:
    # Calculate aggregated scores for radar chart
    tech_scores = {tech: [] for tech in TECHNOLOGIES}
    
    for criterion in CRITERIA:
        for tech in TECHNOLOGIES:
            # Count how many evaluators selected this tech for this criterion
            count = sum(
                1 for eval in st.session_state.evaluations
                if eval["selections"][tech][criterion]
            )
            # Convert to percentage (0-100)
            percentage = (count / len(st.session_state.evaluations)) * 100
            tech_scores[tech].append(percentage)
    
    # ───────── RADAR CHART ─────────
    st.markdown("### Technology Match Scores")
    
    fig = go.Figure()
    
    colors = {
        "Tech A": "#1f86b8",
        "Tech B": "#e67e22",
        "Tech C": "#27ae60",
        "Tech D": "#8e44ad",
        "Tech E": "#e74c3c"
    }
    
    for tech in TECHNOLOGIES:
        fig.add_trace(go.Scatterpolar(
            r=tech_scores[tech],
            theta=CRITERIA,
            fill='toself',
            name=tech,
            line=dict(color=colors.get(tech, "#999")),
            marker=dict(size=8)
        ))
    
    fig.update_layout(
        polar=dict(
            radialaxis=dict(
                visible=True,
                range=[0, 100],
                ticksuffix="%"
            )
        ),
        showlegend=True,
        height=500,
        font=dict(size=12),
        hovermode='closest'
    )
    
    st.plotly_chart(fig, use_container_width=True)
    
    # ───────── EVALUATION COUNT ─────────
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Total Evaluators", len(st.session_state.evaluations))
    with col2:
        st.metric("Criteria Assessed", len(CRITERIA))
    with col3:
        st.metric("Technologies Evaluated", len(TECHNOLOGIES))
    
    # ───────── DETAILED RESULTS TABLE ─────────
    st.markdown("### All Evaluations")
    
    # Create a detailed results dataframe for display
    results_for_display = []
    for eval in st.session_state.evaluations:
        row = {
            "Evaluator": eval["evaluator_name"],
            "Timestamp": eval["timestamp"],
            "Comments": eval["comments"] if eval["comments"] else "(no comments)"
        }
        # Add selected technologies
        selected_techs = [
            tech for tech in TECHNOLOGIES
            if any(eval["selections"][tech].values())
        ]
        row["Selected Technologies"] = ", ".join(selected_techs) if selected_techs else "(none selected)"
        results_for_display.append(row)
    
    results_df = pd.DataFrame(results_for_display)
    st.dataframe(results_df, use_container_width=True, hide_index=True)
    
    # ───────── CSV EXPORT ─────────
    st.markdown("### Export Results")
    
    # Create detailed CSV export
    csv_rows = []
    for eval in st.session_state.evaluations:
        for tech in TECHNOLOGIES:
            row = {
                "Evaluator": eval["evaluator_name"],
                "Timestamp": eval["timestamp"],
                "Technology": tech,
                "Comments": eval["comments"]
            }
            for criterion in CRITERIA:
                row[criterion] = "✓" if eval["selections"][tech][criterion] else ""
            csv_rows.append(row)
    
    csv_df = pd.DataFrame(csv_rows)
    csv_buffer = csv_df.to_csv(index=False)
    
    st.download_button(
        label="📥 Download Results as CSV",
        data=csv_buffer,
        file_name=f"technology_evaluation_{datetime.now().strftime('%Y-%m-%d_%H-%M-%S')}.csv",
        mime="text/csv",
        use_container_width=True
    )
    
    # Also offer summary CSV
    summary_csv = results_df.to_csv(index=False)
    st.download_button(
        label="📄 Download Summary CSV",
        data=summary_csv,
        file_name=f"technology_evaluation_summary_{datetime.now().strftime('%Y-%m-%d_%H-%M-%S')}.csv",
        mime="text/csv",
        use_container_width=True
    )

else:
    st.info("No evaluations submitted yet. Start evaluating above to see results!")

# ─────────────────────────────────────────────────────────────────────────────
# FOOTER
# ─────────────────────────────────────────────────────────────────────────────

st.divider()
st.markdown("""
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
""")
