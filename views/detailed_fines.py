"""Detailed fines page for Spond application."""

import streamlit as st
import pandas as pd
import json
from datetime import datetime
import app_config
from utils.data_loader import load_member_data
from components.player_display import display_player_fines_section


def display_detailed_fines():
    """Display comprehensive fines overview with player selection."""
    st.title("� Bødeoversigt")
    
    # Load all data
    fines_data = st.session_state.fines_calculator.processed_fines_data
    member_data = load_member_data()
    
    # Load fines_data.json directly for detailed view
    try:
        with open('fines_data.json', 'r') as f:
            detailed_fines = json.load(f)
    except FileNotFoundError:
        detailed_fines = {}
    
    if not detailed_fines and not fines_data:
        st.warning("Ingen bødedata tilgængelig. Venligst synkronisér data fra Spond først.")
        return
    
    # Initialize session state for selected player
    if 'selected_player_id' not in st.session_state:
        st.session_state.selected_player_id = None
    
    # Check if we should show detailed view
    if st.session_state.selected_player_id:
        show_player_detail(st.session_state.selected_player_id, detailed_fines, member_data)
    else:
        show_fines_overview(fines_data, member_data, detailed_fines)


def show_fines_overview(fines_data, member_data, detailed_fines):
    """Show overview of all players with fines using the original player display component."""
    st.markdown("### 👥 Alle Spilleres Bøder")
    st.info("🖱️ Klik på en spiller for at se deres detaljerede bødehistorik")
    
    # Convert detailed_fines to the format expected by display_player_fines_section
    converted_fines_data = {}
    
    # Process detailed fines data
    for fine_id, fine in detailed_fines.items():
        player_name = fine['player_name']
        if player_name not in converted_fines_data:
            converted_fines_data[player_name] = {
                'total_fine': 0,
                'no_show_count': 0,
                'late_response_count': 0,
                'training_loss_count': 0,
                'unpaid_amount': 0
            }
        
        converted_fines_data[player_name]['total_fine'] += fine['fine_amount']
        
        # Count by type
        if fine['fine_type'] == 'training_loss':
            converted_fines_data[player_name]['training_loss_count'] += 1
        elif fine['fine_type'] == 'no_show':
            converted_fines_data[player_name]['no_show_count'] += 1
        elif fine['fine_type'] == 'late_response':
            converted_fines_data[player_name]['late_response_count'] += 1
        
        # Add to unpaid amount if not paid
        if not fine.get('paid', False):
            converted_fines_data[player_name]['unpaid_amount'] += fine['fine_amount']
    
    # Also include data from legacy format if available
    if fines_data:
        for member_id, data in fines_data.items():
            # Get member name from member_data dictionary
            if member_data and member_id in member_data:
                member_name = member_data[member_id]['name']
            else:
                member_name = f"Medlem {member_id}"
            
            if member_name not in converted_fines_data:
                converted_fines_data[member_name] = {
                    'total_fine': 0,
                    'no_show_count': 0,
                    'late_response_count': 0,
                    'training_loss_count': 0,
                    'unpaid_amount': 0
                }
            
            # Add legacy data
            legacy_total = (
                data.get('no_show_count', 0) * app_config.NO_SHOW_FINE +
                data.get('late_response_count', 0) * app_config.LATE_RESPONSE_FINE
            )
            converted_fines_data[member_name]['total_fine'] += legacy_total
            converted_fines_data[member_name]['no_show_count'] += data.get('no_show_count', 0)
            converted_fines_data[member_name]['late_response_count'] += data.get('late_response_count', 0)
            converted_fines_data[member_name]['unpaid_amount'] += legacy_total  # Assume legacy fines are unpaid
    
    # Use the original player display component with click functionality enabled
    display_player_fines_section(converted_fines_data, member_data, enable_click=True)


def show_player_detail(player_id, detailed_fines, member_data):
    """Show detailed view for a specific player."""
    # Back button
    if st.button("← Tilbage til oversigt"):
        st.session_state.selected_player_id = None
        st.rerun()
    
    # Get player name from member_data first
    player_name = "Ukendt spiller"
    if member_data and player_id in member_data:
        player_name = member_data[player_id]['name']
    
    # Find player fines by matching player_name (since player_id format differs)
    player_fines = []
    for fine_id, fine in detailed_fines.items():
        if fine['player_name'] == player_name:
            player_fines.append(fine)
    
    # If no fines found by name, try the original ID matching as fallback
    if not player_fines:
        for fine_id, fine in detailed_fines.items():
            if fine['player_id'] == player_id:
                player_name = fine['player_name']
                player_fines.append(fine)
    
    st.title(f"💰 {player_name} - Detaljeret Bødeoversigt")
    
    if not player_fines:
        st.info(f"Ingen detaljerede bøder fundet for {player_name}.")
        return
    
    # Calculate totals
    total_amount = sum(fine['fine_amount'] for fine in player_fines)
    training_losses = sum(1 for fine in player_fines if fine['fine_type'] == 'training_loss')
    no_shows = sum(1 for fine in player_fines if fine['fine_type'] == 'no_show')
    late_responses = sum(1 for fine in player_fines if fine['fine_type'] == 'late_response')
    
    # Summary metrics
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("💰 Total Bøde", f"{total_amount} kr")
    
    with col2:
        st.metric("⚽ Træning Tab", training_losses)
    
    with col3:
        st.metric("🚫 Udeblivelser", no_shows)
    
    with col4:
        st.metric("⏰ Sene Svar", late_responses)
    
    # Detailed fines table
    st.markdown("---")
    st.subheader("📋 Alle Bøder")
    
    # Create DataFrame
    fines_list = []
    for fine in sorted(player_fines, key=lambda x: x['event_date'], reverse=True):
        try:
            # Parse date
            date_obj = datetime.fromisoformat(fine['event_date'].replace('Z', '+00:00'))
            formatted_date = date_obj.strftime('%d-%m-%Y %H:%M')
        except:
            formatted_date = fine['event_date']
        
        # Map fine types to Danish
        fine_type_map = {
            'training_loss': 'Træning Tab',
            'no_show': 'Udeblivelse',
            'late_response': 'Sent Svar'
        }
        
        fine_type_danish = fine_type_map.get(fine['fine_type'], fine['fine_type'])
        
        fines_list.append({
            'Dato': formatted_date,
            'Event': fine['event_name'],
            'Type': fine_type_danish,
            'Beløb': f"{fine['fine_amount']} kr",
            'Betalt': "✅ Ja" if fine.get('paid', False) else "❌ Nej"
        })
    
    if fines_list:
        df = pd.DataFrame(fines_list)
        st.dataframe(df, use_container_width=True, hide_index=True)
    
    # Payment status summary
    st.markdown("---")
    paid_count = sum(1 for fine in player_fines if fine.get('paid', False))
    unpaid_count = len(player_fines) - paid_count
    unpaid_amount = sum(fine['fine_amount'] for fine in player_fines if not fine.get('paid', False))
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric("✅ Betalte Bøder", paid_count)
    
    with col2:
        st.metric("❌ Ubetalte Bøder", unpaid_count)
    
    with col3:
        st.metric("💸 Udestående", f"{unpaid_amount} kr")