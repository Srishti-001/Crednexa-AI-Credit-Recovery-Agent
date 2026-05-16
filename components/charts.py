"""
Chart components — reusable Plotly charts for the application.
"""

import plotly.express as px
import plotly.graph_objects as go
import streamlit as st
from utils.constants import SEVERITY_COLORS, RISK_COLORS, TONE_COLORS, STATUS_COLORS


def _dark_layout(fig, title: str = ""):
    """Apply dark theme layout to a Plotly figure."""
    fig.update_layout(
        template="plotly_dark",
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        title=dict(text=title, font=dict(size=16, color="#e2e8f0")),
        font=dict(color="#94a3b8"),
        margin=dict(l=40, r=20, t=50, b=40),
        legend=dict(bgcolor="rgba(0,0,0,0)"),
    )
    return fig


def donut_chart(labels: list, values: list, colors: list = None, title: str = "",
                hole: float = 0.6):
    """Render a donut chart."""
    fig = go.Figure(data=[go.Pie(
        labels=labels,
        values=values,
        hole=hole,
        marker_colors=colors or px.colors.qualitative.Set2,
        textinfo="label+percent",
        textposition="outside",
        textfont_size=11,
    )])
    fig = _dark_layout(fig, title)
    fig.update_layout(height=350, showlegend=True)
    st.plotly_chart(fig, use_container_width=True)


def bar_chart(x_data: list, y_data: list, colors: list = None, title: str = "",
              x_label: str = "", y_label: str = "", horizontal: bool = False):
    """Render a bar chart."""
    if horizontal:
        fig = go.Figure(data=[go.Bar(
            y=x_data, x=y_data, orientation='h',
            marker_color=colors or "#667eea",
        )])
    else:
        fig = go.Figure(data=[go.Bar(
            x=x_data, y=y_data,
            marker_color=colors or "#667eea",
        )])
    fig = _dark_layout(fig, title)
    fig.update_layout(
        height=350,
        xaxis_title=x_label,
        yaxis_title=y_label,
    )
    st.plotly_chart(fig, use_container_width=True)


def _hex_to_rgba(hex_color: str, alpha: float) -> str:
    """Convert a hex color (#RRGGBB) to an rgba() string."""
    hex_color = hex_color.lstrip('#')
    try:
        r, g, b = tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))
        return f"rgba({r}, {g}, {b}, {alpha})"
    except Exception:
        return f"rgba(100, 100, 100, {alpha})"


def line_chart(x_data: list, y_data: list, title: str = "",
               x_label: str = "", y_label: str = "", color: str = "#667eea"):
    """Render a line chart."""
    fig = go.Figure(data=[go.Scatter(
        x=x_data, y=y_data, mode='lines+markers',
        line=dict(color=color, width=2),
        marker=dict(size=6),
        fill='tozeroy',
        fillcolor=_hex_to_rgba(color, 0.12),
    )])
    fig = _dark_layout(fig, title)
    fig.update_layout(height=350, xaxis_title=x_label, yaxis_title=y_label)
    st.plotly_chart(fig, use_container_width=True)


def status_distribution_chart(status_data: dict, title: str = "Invoice Status Distribution"):
    """Render invoice status distribution as a donut chart."""
    labels = list(status_data.keys())
    values = list(status_data.values())
    colors = [STATUS_COLORS.get(s, "#6B7280") for s in labels]
    donut_chart(labels, values, colors, title)


def risk_distribution_chart(risk_data: dict, title: str = "Risk Distribution"):
    """Render risk category distribution."""
    labels = list(risk_data.keys())
    values = list(risk_data.values())
    colors = [RISK_COLORS.get(r, "#6B7280") for r in labels]
    donut_chart(labels, values, colors, title)


def aging_chart(aging_data: dict, title: str = "Overdue Aging Analysis"):
    """Render aging analysis bar chart."""
    labels = list(aging_data.keys())
    values = list(aging_data.values())
    colors = ["#22c55e", "#84cc16", "#f59e0b", "#ef4444", "#dc2626"][:len(labels)]
    bar_chart(labels, values, colors, title, y_label="Number of Invoices")


def gauge_chart(value: float, title: str = "Recovery Rate", max_val: float = 100,
                thresholds: dict = None):
    """Render a gauge chart."""
    color = "#22c55e" if value >= 75 else "#f59e0b" if value >= 50 else "#ef4444"

    fig = go.Figure(go.Indicator(
        mode="gauge+number+delta",
        value=value,
        title=dict(text=title, font=dict(size=14, color="#e2e8f0")),
        number=dict(suffix="%", font=dict(color="#e2e8f0")),
        gauge=dict(
            axis=dict(range=[0, max_val], tickcolor="#64748b"),
            bar=dict(color=color),
            bgcolor="rgba(30,30,60,0.5)",
            borderwidth=0,
            steps=[
                dict(range=[0, 50], color="rgba(239,68,68,0.1)"),
                dict(range=[50, 75], color="rgba(245,158,11,0.1)"),
                dict(range=[75, 100], color="rgba(34,197,94,0.1)"),
            ],
        ),
    ))
    fig = _dark_layout(fig)
    fig.update_layout(height=280)
    st.plotly_chart(fig, use_container_width=True)
