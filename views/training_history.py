"""Training match history page for viewing past training sessions and results."""

import streamlit as st
import json
import os
from datetime import datetime
import pandas as pd
from utils.github_storage import auto_backup_on_change


def load_training_matches():
    """Load training match history from JSON file."""
    try:
        if os.path.exists('training_matches.json'):
            with open('training_matches.json', 'r', encoding='utf-8') as f:
                return json.load(f)
    except Exception as e:
        st.error(f"Fejl ved indlæsning af træningskampe: {e}")
    return []


def complete_pending_match(match_id, winning_team):
    """Complete a pending match by setting the winner."""
    try:
        matches = load_training_matches()
        
        for match in matches:
            if match.get('match_id') == match_id and match.get('status') == 'pending':
                match['winning_team'] = winning_team
                match['status'] = 'completed'
                match['completed_at'] = datetime.now().isoformat()
                
                # Save locally first
                with open('training_matches.json', 'w', encoding='utf-8') as f:
                    json.dump(matches, f, indent=2, ensure_ascii=False)
                
                # Auto-backup to GitHub
                auto_backup_on_change(matches, 'training_matches.json', 'Kamp resultat opdateret')
                
                return True
        
        return False
    except Exception as e:
        st.error(f"Fejl ved fuldførelse af kamp: {e}")
        return False


def delete_pending_match(match_id):
    """Delete a pending match by match_id."""
    try:
        matches = load_training_matches()
        
        # Find and remove the match with the given ID
        original_length = len(matches)
        matches = [match for match in matches if match.get('match_id') != match_id]
        
        # Check if a match was actually removed
        if len(matches) < original_length:
            # Save locally first
            with open('training_matches.json', 'w', encoding='utf-8') as f:
                json.dump(matches, f, indent=2, ensure_ascii=False)
            
            # Auto-backup to GitHub
            auto_backup_on_change(matches, 'training_matches.json', 'Ventende kamp slettet')
            
            return True
        
        return False
    except Exception as e:
        st.error(f"Fejl ved sletning af ventende kamp: {e}")
        return False


def add_training_fines_from_history(losing_players, reason):
    """Add training fines when completing a match from history."""
    from utils.data_loader import initialize_fines_calculator
    
    # Initialize fines calculator
    initialize_fines_calculator()
    fines_calculator = st.session_state.fines_calculator
    
    # Create a training event ID for training match fines
    training_event_id = f"TRAINING_MATCH_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    
    for player_name in losing_players:
        fine_key = f"{training_event_id}_{player_name.replace(' ', '_')}"
        
        fine_info = {
            'player_id': player_name.replace(' ', '_'),
            'player_name': player_name,
            'event_id': training_event_id,
            'event_name': f"Træningskamp - {reason}",
            'event_date': datetime.now().isoformat(),
            'fine_type': 'training_loss',
            'fine_amount': 25,
            'paid': False,
            'created_date': datetime.now().isoformat()
        }
        
        fines_calculator.fines_data[fine_key] = fine_info
    
    fines_calculator.save_fines_data()


def display_training_history():
    """Display training match history page."""
    st.title("📋 Træningshistorik")
    st.markdown("Oversigt over alle træningskampe og resultater")
    
    # Load matches
    matches = load_training_matches()
    
    # Separate pending and completed matches
    pending_matches = [m for m in matches if m.get('status') == 'pending']
    completed_matches = [m for m in matches if m.get('status') != 'pending']
    
    # Show pending matches first
    if pending_matches:
        st.subheader("⏳ Ventende Kampe")
        st.markdown("Kampe der afventer resultat registrering")
        
        for i, match in enumerate(pending_matches):
            try:
                match_date = datetime.fromisoformat(match['date']).strftime("%d/%m/%Y %H:%M")
            except:
                match_date = match.get('date', 'Ukendt dato')
            
            with st.expander(f"⏳ Ventende Kamp - {match_date}", expanded=True):
                col1, col2 = st.columns(2)
                
                with col1:
                    st.markdown("### ⚪ Hold 1 (Hvid)")
                    if match.get('team1'):
                        for player in match['team1']:
                            st.markdown(f"• {player}")
                    else:
                        st.markdown("Ingen spillere registreret")
                        
                with col2:
                    st.markdown("### ⚫ Hold 2 (Sort)")
                    if match.get('team2'):
                        for player in match['team2']:
                            st.markdown(f"• {player}")
                    else:
                        st.markdown("Ingen spillere registreret")
                
                st.markdown("---")
                st.markdown("**Vælg handling:**")
                
                col_btn1, col_btn2, col_btn3 = st.columns([2, 2, 1])
                
                with col_btn1:
                    unique_key_1 = f"team1_wins_{match.get('match_id')}_{i}"
                    if st.button(f"🏆 Hold 1 Vandt", key=unique_key_1):
                        # Complete the match and add fines
                        success = complete_pending_match(match.get('match_id'), winning_team=1)
                        if success:
                            add_training_fines_from_history(match['team2'], "Hold 1 vandt træningskampen")
                            st.success("✅ Hold 1 registreret som vinder! Bøder tildelt til Hold 2.")
                            st.rerun()
                        else:
                            st.error("❌ Fejl ved registrering af resultat")
                
                with col_btn2:
                    unique_key_2 = f"team2_wins_{match.get('match_id')}_{i}"
                    if st.button(f"🏆 Hold 2 Vandt", key=unique_key_2):
                        # Complete the match and add fines
                        success = complete_pending_match(match.get('match_id'), winning_team=2)
                        if success:
                            add_training_fines_from_history(match['team1'], "Hold 2 vandt træningskampen")
                            st.success("✅ Hold 2 registreret som vinder! Bøder tildelt til Hold 1.")
                            st.rerun()
                        else:
                            st.error("❌ Fejl ved registrering af resultat")
                
                with col_btn3:
                    # Add delete functionality with confirmation
                    delete_key = f"delete_{match.get('match_id')}_{i}"
                    if st.button("🗑️ Slet", key=delete_key, type="secondary"):
                        # Store the match_id to delete in session state for confirmation
                        st.session_state[f"confirm_delete_{match.get('match_id')}"] = True
                        st.rerun()
                    
                    # Show confirmation if delete was clicked
                    if st.session_state.get(f"confirm_delete_{match.get('match_id')}", False):
                        st.warning("⚠️ Er du sikker på at du vil slette denne ventende kamp?")
                        col_confirm, col_cancel = st.columns(2)
                        
                        with col_confirm:
                            confirm_key = f"confirm_delete_{match.get('match_id')}_{i}"
                            if st.button("✅ Ja, slet", key=confirm_key, type="primary"):
                                success = delete_pending_match(match.get('match_id'))
                                if success:
                                    st.success("🗑️ Ventende kamp slettet!")
                                    # Clear the confirmation state
                                    del st.session_state[f"confirm_delete_{match.get('match_id')}"]
                                    st.rerun()
                                else:
                                    st.error("❌ Fejl ved sletning af kamp")
                        
                        with col_cancel:
                            cancel_key = f"cancel_delete_{match.get('match_id')}_{i}"
                            if st.button("❌ Annuller", key=cancel_key):
                                # Clear the confirmation state
                                del st.session_state[f"confirm_delete_{match.get('match_id')}"]
                                st.rerun()
        
        st.markdown("---")
    
    if not completed_matches and not pending_matches:
        st.info("🤷‍♂️ Ingen træningskampe registreret endnu.")
        st.markdown("Gå til **Hold Udvælger** for at generere hold og registrere træningskamp resultater.")
        return
    
    # Statistics summary (only for completed matches)
    if completed_matches:
        st.subheader("📊 Samlet Statistik")
        
        total_matches = len(completed_matches)
        
        # Count wins per team position
        team1_wins = sum(1 for match in completed_matches if match.get('winning_team') == 1)
        team2_wins = sum(1 for match in completed_matches if match.get('winning_team') == 2)
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.metric("Samlet Træningskampe", total_matches)
        
        with col2:
            st.metric("⚪ Hold 1 Sejre", team1_wins, f"{team1_wins/total_matches*100:.0f}%" if total_matches > 0 else "0%")
        
        with col3:
            st.metric("⚫ Hold 2 Sejre", team2_wins, f"{team2_wins/total_matches*100:.0f}%" if total_matches > 0 else "0%")
    
        # Player statistics
        st.subheader("🏆 Spillerstatistik")
        
        # Count wins and losses per player
        player_stats = {}
        
        for match in completed_matches:
            winning_team = match.get('winning_team')
            team1 = match['team1']
            team2 = match['team2']
            
            # Count wins
            winning_players = team1 if winning_team == 1 else team2
            losing_players = team2 if winning_team == 1 else team1
            
            for player in winning_players:
                if player not in player_stats:
                    player_stats[player] = {'wins': 0, 'losses': 0, 'matches': 0}
                player_stats[player]['wins'] += 1
                player_stats[player]['matches'] += 1
                
            for player in losing_players:
                if player not in player_stats:
                    player_stats[player] = {'wins': 0, 'losses': 0, 'matches': 0}
                player_stats[player]['losses'] += 1
                player_stats[player]['matches'] += 1
        
        if player_stats:
            # Create DataFrame for better display
            stats_data = []
            for player, stats in player_stats.items():
                win_rate = stats['wins'] / stats['matches'] * 100 if stats['matches'] > 0 else 0
                stats_data.append({
                    'Spiller': player,
                    'Kampe': stats['matches'],
                    'Sejre': stats['wins'],
                    'Tab': stats['losses'],
                    'Sejrsrate': f"{win_rate:.1f}%"
                })
            
            # Sort by win rate, then by total matches
            stats_df = pd.DataFrame(stats_data)
            stats_df['win_rate_num'] = stats_df['Sejrsrate'].str.replace('%', '').astype(float)
            stats_df = stats_df.sort_values(['win_rate_num', 'Kampe'], ascending=[False, False])
            stats_df = stats_df.drop('win_rate_num', axis=1)
            
            # Color code the win rates
            def color_win_rate(val):
                rate = float(val.replace('%', ''))
                if rate >= 70:
                    return 'background-color: #28a745; color: white'
                elif rate >= 50:
                    return 'background-color: #ffc107; color: black'
                else:
                    return 'background-color: #dc3545; color: white'
            
            styled_df = stats_df.style.map(color_win_rate, subset=['Sejrsrate'])
            st.dataframe(styled_df, use_container_width=True, hide_index=True)
    
    # Match history (completed matches only)
    if completed_matches:
        st.subheader("📝 Fuldførte Kampe")
        
        # Add filter options
        col1, col2 = st.columns(2)
        with col1:
            show_recent = st.selectbox("Vis kampe", ["Alle kampe", "Seneste 10", "Seneste 20"])
        with col2:
            sort_order = st.selectbox("Sortering", ["Nyeste først", "Ældste først"])
        
        # Filter matches
        display_matches = completed_matches.copy()
        
        if show_recent == "Seneste 10":
            display_matches = display_matches[-10:]
        elif show_recent == "Seneste 20":
            display_matches = display_matches[-20:]
        
        # Sort matches
        if sort_order == "Nyeste først":
            display_matches = list(reversed(display_matches))
        
        # Display matches
        for i, match in enumerate(display_matches):
            try:
                match_date = datetime.fromisoformat(match['date']).strftime("%d/%m/%Y %H:%M")
            except:
                match_date = match.get('date', 'Ukendt dato')
                
            winning_team = match['winning_team']
            match_number = len(completed_matches) - completed_matches[::-1].index(match) if sort_order == "Nyeste først" else completed_matches.index(match) + 1
            
            winner_emoji = "🏆"
            with st.expander(f"{winner_emoji} Træningskamp {match_number} - {match_date}"):
                col1, col2 = st.columns(2)
                
                with col1:
                    team1_emoji = "🏆" if winning_team == 1 else "❌"
                    st.markdown(f"### {team1_emoji} Hold 1 (Hvid)")
                    if match.get('team1'):
                        for player in match['team1']:
                            st.markdown(f"• {player}")
                    else:
                        st.markdown("Ingen spillere registreret")
                        
                with col2:
                    team2_emoji = "🏆" if winning_team == 2 else "❌"
                    st.markdown(f"### {team2_emoji} Hold 2 (Sort)")
                    if match.get('team2'):
                        for player in match['team2']:
                            st.markdown(f"• {player}")
                    else:
                        st.markdown("Ingen spillere registreret")
                
                winner_name = "Hold 1 (Hvid)" if winning_team == 1 else "Hold 2 (Sort)"
                st.success(f"🎉 **Vinder:** {winner_name}")
                
                # Show match details
                st.markdown("---")
                match_id = match.get('match_id', 'Ukendt')
                st.caption(f"Match ID: {match_id}")
        
        # Export functionality
        st.subheader("📤 Eksporter Data")
        
        if st.button("📥 Download Træningshistorik som CSV"):
            # Prepare data for CSV export
            export_data = []
            for i, match in enumerate(completed_matches):
                try:
                    match_date = datetime.fromisoformat(match['date']).strftime("%d/%m/%Y %H:%M")
                except:
                    match_date = match.get('date', 'Ukendt dato')
                
                winning_team = match['winning_team']
                winner_name = "Hold 1" if winning_team == 1 else "Hold 2"
                
                # Create rows for each player
                for player in match.get('team1', []):
                    export_data.append({
                        'Kamp Nr': i + 1,
                        'Dato': match_date,
                        'Spiller': player,
                        'Hold': 'Hold 1',
                        'Resultat': 'Vinder' if winning_team == 1 else 'Taber',
                        'Vinder': winner_name
                    })
                
                for player in match.get('team2', []):
                    export_data.append({
                        'Kamp Nr': i + 1,
                        'Dato': match_date,
                        'Spiller': player,
                        'Hold': 'Hold 2',
                        'Resultat': 'Vinder' if winning_team == 2 else 'Taber',
                        'Vinder': winner_name
                    })
            
            if export_data:
                df = pd.DataFrame(export_data)
                csv = df.to_csv(index=False, encoding='utf-8')
                st.download_button(
                    label="💾 Download CSV",
                    data=csv,
                    file_name=f"traening_historik_{datetime.now().strftime('%Y%m%d')}.csv",
                    mime='text/csv'
                )