"""Chart components for Spond application."""

import streamlit as st
import plotly.express as px
from utils.helpers import prepare_chart_data


def display_total_fines_bar_chart(fines_data):
    """Display bar chart of total fines."""
    df = prepare_chart_data(fines_data)
    
    if not df.empty:
        # Bar chart of total fines
        fig_bar = px.bar(
            df.head(10), 
            x='Player', 
            y='Total Fine',
            title="Top 10 Spillere efter Samlet Bøder",
            color='Total Fine',
            color_continuous_scale='Reds'
        )
        fig_bar.update_xaxes(tickangle=45)
        st.plotly_chart(fig_bar, use_container_width=True)


def display_fine_distribution_pie_chart(fines_data):
    """Display pie chart of fine distribution."""
    df = prepare_chart_data(fines_data)
    
    if not df.empty:
        # Pie chart of fine distribution
        fig_pie = px.pie(
            df[df['Total Fine'] > 0].head(10),
            values='Total Fine',
            names='Player',
            title="Bødefordeling (Top 10)"
        )
        st.plotly_chart(fig_pie, use_container_width=True)


def display_dashboard_charts(fines_data):
    """Display both dashboard charts side by side."""
    col1, col2 = st.columns(2)
    
    with col1:
        display_total_fines_bar_chart(fines_data)
    
    with col2:
        display_fine_distribution_pie_chart(fines_data)