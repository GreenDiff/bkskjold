"""Dashboard page for Spond application."""

import streamlit as st
import app_config
from utils.data_loader import load_member_data, sync_data_wrapper
from utils.helpers import calculate_statistics
from components.charts import display_dashboard_charts
from components.player_display import display_player_fines_section


def display_dashboard():
    """Display the main dashboard."""
    st.title("⚽ BK Skjolds Bødekasse")
        
    # Sync button
    col1, col2 = st.columns([3, 1])
    with col2:
        if st.button("🔄 Synkronisér Data", use_container_width=True):
            with st.spinner("Synkroniserer data fra Spond..."):
                sync_data_wrapper()
            st.rerun()

    # Load fines data
    fines_data = st.session_state.fines_calculator.processed_fines_data
    member_data = load_member_data()
    
    if not fines_data:
        st.warning("Ingen bødedata tilgængelig. Venligst synkronisér data fra Spond først.")
        return
    
    # Calculate and display statistics
    stats = calculate_statistics(fines_data, member_data)
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("Total Trupantal", stats['total_players'])
    
    with col2:
        st.metric("Samlet Bøder", f"{stats['total_fines']:,} kr")

    with col3:
        st.metric("Gennemsnitlig Bøde", f"{stats['avg_fine']:.0f} kr")

    with col4:
        st.metric("Spillere med Bøder", stats['players_with_fines'])

    # Display charts
    st.subheader("📊 Overblik")
    display_dashboard_charts(fines_data)
    
    # Recent activity summary
    st.subheader("📅 Seneste Aktivitetsoversigt")
    
    # Show breakdown of fines by type
    if fines_data:
        total_no_show = sum(data['no_show_count'] for data in fines_data.values())
        total_late = sum(data['late_response_count'] for data in fines_data.values())
        
        col1, col2 = st.columns(2)
        with col1:
            st.info(f"**Udeblivelser:** {total_no_show} (Total: {total_no_show * app_config.NO_SHOW_FINE:,} kr)")
        with col2:
            st.info(f"**Sene Svar:** {total_late} (Total: {total_late * app_config.LATE_RESPONSE_FINE:,} kr)")
    
    # Player Fines Section (previously separate page)
    st.markdown("---")
    st.subheader("👥 Holdmedlemmers Bøder")
    st.info("Individuel oversigt over alle holdmedlemmers bøder med betalingsstatus")
    
    display_player_fines_section(fines_data, member_data)
    
    st.markdown("---")