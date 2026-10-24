"""
Chart builders module using Plotly for data visualization.
Provides consistent styling and chart generation functions for the dashboard.
"""

# file connections / imports
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd


# style figure
def _style_figure(fig, title: str):
    """
    Apply consistent styling to a Plotly figure.

    Matches the existing dashboard design language with professional
    typography and clean visual appearance.

    Args:
        fig: Plotly figure object
        title: Chart title text

    Returns:
        Styled figure object
    """
    fig.update_layout(
        title=dict(
            text=title,
            x=0.02,
            xanchor="left",
            font=dict(size=20, color="#0f172a", family="Inter, sans-serif")
        ),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(248,250,252,0.82)",
        margin=dict(l=28, r=28, t=78, b=36),
        font=dict(family="Inter, sans-serif", color="#334155", size=14),
        hoverlabel=dict(font_size=14, font_family="Inter, sans-serif")
    )
    return fig


# subject avg bar chart
def subject_avg_bar_chart(avg_series: pd.Series, class_name: str):
    """
    Create a horizontal bar chart showing average marks per subject.

    Includes a vertical benchmark line at 70 to highlight performance thresholds.

    Args:
        avg_series: Series with subject names as index and averages as values
        class_name: Class identifier for the title

    Returns:
        Plotly figure object
    """
    fig = px.bar(
        x=avg_series.values,
        y=avg_series.index,
        orientation='h',
        labels={'x': 'Average Mark', 'y': 'Subject'}
    )

    fig.update_traces(marker_color="#004080")

    fig = _style_figure(fig, f"Average Marks per Subject — {class_name}")

    fig.add_vline(
        x=70,
        line_dash="dash",
        line_color="red",
        annotation_text="Benchmark (70)",
        annotation_position="top"
    )

    fig.update_yaxes(categoryorder='total ascending')

    return fig


# performance trend chart
def performance_trend_chart(avg_series: pd.Series, class_name: str):
    """
    Create a line chart showing subject performance trend.

    Visualizes per-subject averages as connected dots with a benchmark line.

    Args:
        avg_series: Series with subject names as index and averages as values
        class_name: Class identifier for the title

    Returns:
        Plotly figure object
    """
    fig = go.Figure()

    fig.add_trace(go.Scatter(
        x=avg_series.index.tolist(),
        y=avg_series.values,
        mode='lines+markers',
        name='Subject Average',
        line=dict(color="#004080", width=3),
        marker=dict(color="#004080", size=10)
    ))

    fig.add_hline(
        y=70,
        line_dash="dash",
        line_color="red",
        annotation_text="Benchmark (70)",
        annotation_position="right"
    )

    fig = _style_figure(fig, f"Subject Performance Trend — {class_name}")

    fig.update_xaxes(title_text="Subject", tickangle=45)
    fig.update_yaxes(title_text="Average Mark")

    return fig


# grade comparison chart
def grade_comparison_chart(grade_data: dict, grade: int):
    """
    Create a bar chart comparing class averages within a grade.

    Args:
        grade_data: Dict mapping class names to average marks
                   (e.g., {"9A": 72.3, "9B": 68.1, ...})
        grade: Grade number for the title

    Returns:
        Plotly figure object
    """
    classes = list(grade_data.keys())
    averages = list(grade_data.values())

    fig = px.bar(
        x=classes,
        y=averages,
        labels={'x': 'Class Section', 'y': 'Class Average'},
        color=averages,
        color_continuous_scale=['#1e3a5f', '#2563eb', '#3b82f6', '#60a5fa']
    )

    fig = _style_figure(fig, f"Grade {grade} — Section Comparison")

    fig.update_coloraxes(showscale=False)

    fig.update_traces(texttemplate='%{y:.1f}', textposition='outside')

    return fig


# top students chart
def top_students_chart(top_df: pd.DataFrame, title: str):
    """
    Create a grouped bar chart showing marks per subject for top students.

    Args:
        top_df: DataFrame with Student column and subject columns
        title: Chart title

    Returns:
        Plotly figure object
    """
    students = top_df["Student"].tolist()

    exclude_cols = ["Student", "Average", "Class"]
    subject_cols = [col for col in top_df.columns if col not in exclude_cols]

    colors = ["#004080", "#2563eb", "#60a5fa"]

    fig = go.Figure()

    for idx, student in enumerate(students):
        student_data = top_df[top_df["Student"] == student]
        marks = [student_data[subj].values[0] for subj in subject_cols]

        fig.add_trace(go.Bar(
            name=student,
            x=subject_cols,
            y=marks,
            marker_color=colors[idx % len(colors)]
        ))

    fig.update_layout(barmode='group')

    fig = _style_figure(fig, title)

    fig.update_xaxes(title_text="Subject", tickangle=45)
    fig.update_yaxes(title_text="Mark")

    fig.update_layout(
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="right",
            x=1
        )
    )

    return fig
