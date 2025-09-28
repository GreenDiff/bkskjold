"""Detailed fines page for Spond application."""

import streamlit as st
import pandas as pd


def display_detailed_fines():
    """Display detailed fines breakdown."""
    st.title("📋 Detaljeret Bødeoversigt")
    
    fines_data = st.session_state.fines_calculator.processed_fines_data
    
    if not fines_data:
        st.warning("Ingen bødedata tilgængelig. Venligst synkronisér data fra Spond først.")
        return
    
    # Player selection
    player_names = list(fines_data.keys())
    if not player_names:
        st.info("Ingen spillere med bøder fundet.")
        return
    
    selected_player = st.selectbox("Vælg en spiller:", player_names)
    
    if selected_player:
        player_data = fines_data[selected_player]
        
        # Display player summary
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.metric("Samlet Bøde", f"{player_data['total_fine']} kr")
        
        with col2:
            st.metric("Udeblivelser", player_data['no_show_count'])
        
        with col3:
            st.metric("Sene Svar", player_data['late_response_count'])
        
        # Display events details
        st.subheader("Begivenhedsdetaljer")
        
        if player_data['events']:
            events_df = pd.DataFrame(player_data['events'])
            
            # Format datetime columns
            if 'startTimestamp' in events_df.columns:
                events_df['Date'] = pd.to_datetime(events_df['startTimestamp']).dt.strftime('%Y-%m-%d %H:%M')
            
            # Display table
            st.dataframe(
                events_df[['Date', 'heading', 'fine_reason', 'fine_amount']],
                use_container_width=True,
                hide_index=True
            )
        else:
            st.info("Ingen begivenheder fundet for denne spiller.")