"""Team selector page for random team generation with football pitch layout."""

import streamlit as st
import random
import json
import os
from datetime import datetime
from utils.data_loader import load_member_data, get_training_accepted_players, initialize_fines_calculator
from intelligent_team_generator import IntelligentTeamGenerator


def get_player_data_dict(member_data):
    """Convert member data to a dictionary with names as keys."""
    player_dict = {}
    if member_data:
        for member in member_data.values():
            name = f"{member.get('firstName', '')} {member.get('lastName', '')}".strip()
            if name:
                player_dict[name] = member
    return player_dict


def load_training_matches():
    """Load training match history from JSON file."""
    try:
        if os.path.exists('training_matches.json'):
            with open('training_matches.json', 'r', encoding='utf-8') as f:
                return json.load(f)
    except Exception as e:
        st.error(f"Fejl ved indlæsning af træningskampe: {e}")
    return []


def save_training_match(team1, team2, winning_team, match_date=None):
    """Save a training match to the history file."""
    try:
        matches = load_training_matches()
        
        # Generate unique match_id with microseconds to avoid duplicates
        import time
        timestamp = datetime.now()
        unique_id = f"training_{timestamp.strftime('%Y%m%d_%H%M%S')}_{int(time.time() * 1000000) % 1000000}"
        
        match_data = {
            'date': match_date or timestamp.isoformat(),
            'team1': team1,
            'team2': team2,
            'winning_team': winning_team,  # 1 or 2
            'created_at': timestamp.isoformat(),
            'match_id': unique_id,
            'status': 'completed'
        }
        
        matches.append(match_data)
        
        with open('training_matches.json', 'w', encoding='utf-8') as f:
            json.dump(matches, f, indent=2, ensure_ascii=False)
            
        return True
    except Exception as e:
        st.error(f"Fejl ved gemning af træningskamp: {e}")
        return False


def save_pending_match(team1, team2):
    """Save a pending training match that awaits result."""
    try:
        matches = load_training_matches()
        
        # Generate unique match_id with microseconds to avoid duplicates
        import time
        timestamp = datetime.now()
        unique_id = f"pending_{timestamp.strftime('%Y%m%d_%H%M%S')}_{int(time.time() * 1000000) % 1000000}"
        
        match_data = {
            'date': timestamp.isoformat(),
            'team1': team1,
            'team2': team2,
            'winning_team': None,  # To be determined later
            'created_at': timestamp.isoformat(),
            'match_id': unique_id,
            'status': 'pending'
        }
        
        matches.append(match_data)
        
        with open('training_matches.json', 'w', encoding='utf-8') as f:
            json.dump(matches, f, indent=2, ensure_ascii=False)
            
        return match_data['match_id']
    except Exception as e:
        st.error(f"Fejl ved gemning af ventende kamp: {e}")
        return None


def complete_pending_match(match_id, winning_team):
    """Complete a pending match by setting the winner."""
    try:
        matches = load_training_matches()
        
        for match in matches:
            if match.get('match_id') == match_id and match.get('status') == 'pending':
                match['winning_team'] = winning_team
                match['status'] = 'completed'
                match['completed_at'] = datetime.now().isoformat()
                
                with open('training_matches.json', 'w', encoding='utf-8') as f:
                    json.dump(matches, f, indent=2, ensure_ascii=False)
                
                return True
        
        return False
    except Exception as e:
        st.error(f"Fejl ved fuldførelse af kamp: {e}")
        return False


def display_player_row(player_name, player_data, team_color="#28a745"):
    """Display a player in a compact row with small photo and name."""
    col1, col2 = st.columns([1, 5])
    
    with col1:
        if player_data:
            profile_image = player_data.get('profilePicture', '')
            if profile_image:
                st.image(profile_image, width=40)
            else:
                # Default football player image for team members without photos
                default_image = "https://i2-prod.birminghammail.co.uk/article10620537.ece/ALTERNATES/s1200c/Obese-Manchester-united-supporter.jpg"
                st.image(default_image, width=40)
        else:
            # For manual players - use same default as team members without photos
            default_image = "https://i2-prod.birminghammail.co.uk/article10620537.ece/ALTERNATES/s1200c/Obese-Manchester-united-supporter.jpg"
            st.image(default_image, width=40)
    
    with col2:
        # Use smaller text for more compact display
        st.markdown(f"**{player_name}**")



def display_teams_layout(teams, player_dict):
    """Display teams in a simple side-by-side layout."""
    # Display teams side by side
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("### ⚪ Hold 1 (Hvid)")
        if teams['team1']:
            for player in teams['team1']:
                player_data = player_dict.get(player)
                display_player_row(player, player_data, "#1f77b4")
        else:
            st.write("Ingen spillere på hold 1")
    
    with col2:
        st.markdown("### ⚫ Hold 2 (Sort)")
        if teams['team2']:
            for player in teams['team2']:
                player_data = player_dict.get(player)
                display_player_row(player, player_data, "#ff7f0e")
        else:
            st.write("Ingen spillere på hold 2")
    
    # Display reserves if any
    if teams.get('remaining'):
        st.markdown("### ⚪ Reserve Spillere")
        for player in teams['remaining']:
            player_data = player_dict.get(player)
            display_player_row(player, player_data, "#2ca02c")




def add_player_callback():
    """Callback to add manual player."""
    current_input = st.session_state.get(f'new_player_input_{st.session_state.input_counter}', '').strip()
    if current_input and current_input not in st.session_state.manual_players:
        st.session_state.manual_players.append(current_input)
        if current_input not in st.session_state.selected_players:
            st.session_state.selected_players.append(current_input)
        st.session_state.input_counter += 1



def generate_teams_callback():
    """Callback to generate intelligently balanced teams."""
    selected_players = st.session_state.selected_players
    if len(selected_players) >= 2:
        try:
            # Initialize intelligent team generator
            generator = IntelligentTeamGenerator()
            
            # Add some randomness to ensure different teams each time
            import random
            random.shuffle(selected_players)
            
            # Generate balanced teams using optimal algorithm
            team1, team2, balance_info = generator.generate_smart_teams(selected_players, 'optimal')
            
            # Handle remaining players - smart algorithms should create equal teams
            remaining = []
            num_selected = len(selected_players)
            expected_team_size = num_selected // 2
            
            # Verify team sizes are correct
            if len(team1) != expected_team_size or len(team2) != expected_team_size:
                # If teams are not equal size, fix it
                st.warning(f"Justerer holdstørrelser: Hold1={len(team1)}, Hold2={len(team2)}, Forventet={expected_team_size}")
                
                # Combine all players and redistribute properly
                all_players = team1 + team2
                team1 = all_players[:expected_team_size]
                team2 = all_players[expected_team_size:expected_team_size*2]
                
            # Handle any remaining player for odd numbers
            if num_selected % 2 == 1:
                remaining = selected_players[expected_team_size*2:]
            
            # Store balance information for display
            st.session_state.team_balance_info = balance_info
            
            st.session_state.generated_teams = {
                'team1': team1,
                'team2': team2,
                'remaining': remaining,
                'team_size': len(team1)  # Both teams now have equal size
            }
            
            # Reset saved status when generating new teams
            st.session_state.teams_saved = False
            if 'pending_match_id' in st.session_state:
                del st.session_state.pending_match_id
            
            st.success(f"✅ Hold genereret! Hold 1: {len(team1)} spillere, Hold 2: {len(team2)} spillere")
            
        except Exception as e:
            st.error(f"Fejl ved intelligent holdgenerering: {e}")
            # Fallback to simple random if smart generation fails
            all_players = selected_players.copy()
            random.shuffle(all_players)
            team_size = len(all_players) // 2
            team1 = all_players[:team_size]
            team2 = all_players[team_size:team_size*2]
            remaining = all_players[team_size*2:]
            
            st.session_state.generated_teams = {
                'team1': team1,
                'team2': team2,
                'remaining': remaining,
                'team_size': team_size
            }
            
            # Reset saved status when generating new teams
            st.session_state.teams_saved = False
            if 'pending_match_id' in st.session_state:
                del st.session_state.pending_match_id
    else:
        st.warning("Vælg mindst 2 spillere for at generere hold")

def clear_teams_callback():
    """Callback to clear teams."""
    st.session_state.generated_teams = None
    st.session_state.teams_saved = False
    if 'pending_match_id' in st.session_state:
        del st.session_state.pending_match_id

def copy_teams_callback():
    """Callback to copy teams to display."""
    teams = st.session_state.generated_teams
    if teams:
        team_text = f"""⚪ Hold 1:
{chr(10).join([f"{i}. {player}" for i, player in enumerate(teams['team1'], 1)])}

⚫ Hold 2:
{chr(10).join([f"{i}. {player}" for i, player in enumerate(teams['team2'], 1)])}"""
        
        if teams.get('remaining'):
            team_text += f"""

⚪ Reserve:
{chr(10).join([f"{i}. {player}" for i, player in enumerate(teams['remaining'], 1)])}"""
        
        st.session_state.team_text_to_display = team_text
        st.session_state.show_team_text = True

def team1_wins_callback():
    """Callback when Team 1 wins - add fines to Team 2."""
    teams = st.session_state.generated_teams
    if teams and teams.get('team2'):
        # Complete pending match or save new match
        success = False
        if st.session_state.get('pending_match_id'):
            success = complete_pending_match(st.session_state.pending_match_id, winning_team=1)
        else:
            success = save_training_match(teams['team1'], teams['team2'], winning_team=1)
        
        if success:
            st.session_state.winning_team = 1
            add_training_fines(teams['team2'], "Hold 1 vandt træningskampen")
            st.session_state.fines_added = True
            st.session_state.match_logged = True
        else:
            st.error("Fejl ved logging af træningskamp")

def team2_wins_callback():
    """Callback when Team 2 wins - add fines to Team 1."""
    teams = st.session_state.generated_teams
    if teams and teams.get('team1'):
        # Complete pending match or save new match
        success = False
        if st.session_state.get('pending_match_id'):
            success = complete_pending_match(st.session_state.pending_match_id, winning_team=2)
        else:
            success = save_training_match(teams['team1'], teams['team2'], winning_team=2)
        
        if success:
            st.session_state.winning_team = 2
            add_training_fines(teams['team1'], "Hold 2 vandt træningskampen")
            st.session_state.fines_added = True
            st.session_state.match_logged = True
        else:
            st.error("Fejl ved logging af træningskamp")

def add_training_fines(losing_players, reason):
    """Add fines to players on losing team."""
    # Initialize fines calculator
    initialize_fines_calculator()
    fines_calculator = st.session_state.fines_calculator
    
    # Create a training event ID for training match fines
    training_event_id = f"TRAINING_MATCH_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    
    # Store the event ID for potential undo
    st.session_state.last_training_event_id = training_event_id
    
    for player_name in losing_players:
        fine_key = f"{training_event_id}_{player_name.replace(' ', '_')}"
        
        fine_info = {
            'player_id': player_name.replace(' ', '_'),  # Use name as ID for manual players
            'player_name': player_name,
            'event_id': training_event_id,
            'event_name': f"Træningskamp - {reason}",
            'event_date': datetime.now().isoformat(),
            'fine_type': 'training_loss',
            'fine_amount': 25,  # Smaller fine for training loss
            'paid': False,
            'created_date': datetime.now().isoformat()
        }
        
        # Add to fines data
        fines_calculator.fines_data[fine_key] = fine_info
    
    # Save the updated fines
    fines_calculator.save_fines_data()

def undo_training_fines():
    """Remove the last added training fines and logged match."""
    if 'last_training_event_id' in st.session_state:
        # Initialize fines calculator
        initialize_fines_calculator()
        fines_calculator = st.session_state.fines_calculator
        
        training_event_id = st.session_state.last_training_event_id
        
        # Remove all fines for this training event
        keys_to_remove = [key for key in fines_calculator.fines_data.keys() 
                         if key.startswith(training_event_id)]
        
        for key in keys_to_remove:
            del fines_calculator.fines_data[key]
        
        # Save the updated fines
        fines_calculator.save_fines_data()
        
        # Clear the stored event ID
        del st.session_state.last_training_event_id
    
    # Also remove the last logged match if it exists
    if st.session_state.get('match_logged', False):
        try:
            matches = load_training_matches()
            if matches:
                # Remove the last match (most recent one)
                matches.pop()
                with open('training_matches.json', 'w', encoding='utf-8') as f:
                    json.dump(matches, f, indent=2, ensure_ascii=False)
        except Exception as e:
            st.error(f"Fejl ved sletning af træningskamp: {e}")

def clear_all_callback():
    """Callback to clear everything."""
    st.session_state.manual_players = []
    # Get fresh player data
    member_data = load_member_data()
    player_dict = get_player_data_dict(member_data)
    
    # Reset to accepted players for next training
    try:
        accepted_players = get_training_accepted_players()
        valid_accepted_players = [p for p in accepted_players if p in player_dict.keys()]
        st.session_state.selected_players = valid_accepted_players if valid_accepted_players else list(player_dict.keys())
    except:
        st.session_state.selected_players = list(player_dict.keys())
    
    st.session_state.generated_teams = None
    st.session_state.input_counter += 1
    # Clear any match results
    if 'winning_team' in st.session_state:
        del st.session_state.winning_team
    if 'fines_added' in st.session_state:
        del st.session_state.fines_added
    if 'last_training_event_id' in st.session_state:
        del st.session_state.last_training_event_id
    if 'match_logged' in st.session_state:
        del st.session_state.match_logged
    if 'teams_saved' in st.session_state:
        del st.session_state.teams_saved
    if 'pending_match_id' in st.session_state:
        del st.session_state.pending_match_id

def display_team_selector():
    """Display the team selector page for training."""
    st.title("⚽ Hold Udvælger")
    st.info("🎯 Spillere der har accepteret næste træning er automatisk valgt. Fravælg utilgængelige og generer tilfældige hold.")
    
    # Check for pending matches
    matches = load_training_matches()
    pending_matches = [m for m in matches if m.get('status') == 'pending']
    
    if pending_matches:
        st.warning(f"⏳ Du har {len(pending_matches)} ventende kamp(e) der afventer resultater. Gå til **Træningshistorik** for at registrere vindere.")
    
    # Load member data
    member_data = load_member_data()
    player_dict = get_player_data_dict(member_data)
    
    # Initialize session state
    if 'manual_players' not in st.session_state:
        st.session_state.manual_players = []
    if 'selected_players' not in st.session_state:
        # Get players who accepted the next training session
        try:
            accepted_players = get_training_accepted_players()
            # Filter to only include players that exist in our member data
            valid_accepted_players = [p for p in accepted_players if p in player_dict.keys()]
            st.session_state.selected_players = valid_accepted_players
            
            # Show info about automatic selection
            if valid_accepted_players:
                st.info(f"🎯 Automatisk valgt {len(valid_accepted_players)} spillere der har accepteret næste træning")
            else:
                # Fallback to all players if no training found or no accepted players
                st.session_state.selected_players = list(player_dict.keys())
                st.warning("⚠️ Ingen træning fundet eller ingen spillere har accepteret - viser alle spillere")
        except Exception as e:
            # Fallback to all players on error
            st.session_state.selected_players = list(player_dict.keys())
            st.warning(f"⚠️ Fejl ved hentning af træningsdata - viser alle spillere")
    if 'generated_teams' not in st.session_state:
        st.session_state.generated_teams = None
    if 'input_counter' not in st.session_state:
        st.session_state.input_counter = 0
    
    # Clean up session state - remove any invalid players that no longer exist
    team_members = list(player_dict.keys())
    all_valid_players = team_members + st.session_state.manual_players
    st.session_state.selected_players = [p for p in st.session_state.selected_players if p in all_valid_players]
    
    # Create two columns for layout - make player selection area bigger
    col1, col2 = st.columns([3, 1])
    
    with col1:
        st.subheader("📋 Spillervalg")
        
        # Available players from team roster - auto-selected based on training acceptance
        if member_data:
            st.write("**Spillere til næste træning (fravælg utilgængelige):**")
            # Include both team members and manual players in the available options
            team_members = list(player_dict.keys())
            all_available_players = team_members + st.session_state.manual_players
            
            # Filter selected players to only include those that exist in available options
            valid_selected_players = [p for p in st.session_state.selected_players if p in all_available_players]
            
            # Multiselect for team members - now defaults to all selected with larger height
            selected_team_members = st.multiselect(
                "Tilgængelige spillere:",
                all_available_players,
                default=valid_selected_players,
                help="Fravælg spillere der ikke er tilgængelige til træning"
            )
            
            # Add some styling to make the multiselect larger
            st.markdown("""
            <style>
            .stMultiSelect > div > div > div {
                min-height: 200px !important;
            }
            </style>
            """, unsafe_allow_html=True)
            
            # Update session state
            st.session_state.selected_players = selected_team_members
        else:
            st.warning("Ingen holddata tilgængelig. Synkronisér data først.")
            selected_team_members = []
        
        # Manual player addition
        st.write("**Tilføj Eksterne Spillere:**")
        
        # Input for new manual player
        col_input, col_add = st.columns([3, 1])
        with col_input:
            new_player = st.text_input(
                "Spillernavn:", 
                placeholder="Indtast navn på ekstern spiller",
                key=f"new_player_input_{st.session_state.input_counter}"
            )
        with col_add:
            st.write("")  # Space for alignment
            st.button("➕ Tilføj", on_click=add_player_callback)
        
        # Display manual players with remove option
        if st.session_state.manual_players:
            st.write("**Eksterne Spillere:**")
            
            for i, player in enumerate(st.session_state.manual_players):
                col_name, col_remove = st.columns([4, 1])
                with col_name:
                    st.write(f"• {player}")
                with col_remove:
                    def make_remove_callback(player_name):
                        def callback():
                            if player_name in st.session_state.manual_players:
                                st.session_state.manual_players.remove(player_name)
                            if player_name in st.session_state.selected_players:
                                st.session_state.selected_players.remove(player_name)
                        return callback
                    
                    st.button("🗑️", key=f"remove_{i}", help=f"Fjern {player}",
                             on_click=make_remove_callback(player))
    
    with col2:
        st.subheader("⚙️ Hold Indstillinger")
        
        # Get total available players (manual players are now included in selected_team_members)
        total_selected = len(selected_team_members)
        
        st.metric("Tilgængelige Spillere", total_selected)
        
        # Team generation options
        if total_selected >= 2:
            st.info(f"Hold størrelse: {total_selected // 2} spillere per hold")
            
            st.info("🧠 Bruger intelligent balance baseret på sejrsrate historik")
            
            st.button("🧠 Generer Balancerede Hold", use_container_width=True, type="primary",
                     on_click=generate_teams_callback)
        else:
            st.info("Vælg mindst 2 spillere for at generere hold")
    
    # Display generated teams
    if st.session_state.generated_teams:
        st.markdown("---")
        st.subheader("🏆 Genererede Hold")
        
        teams = st.session_state.generated_teams
        
        # Display teams layout
        display_teams_layout(teams, player_dict)
        
        # Display balance information if available
        if 'team_balance_info' in st.session_state and st.session_state.team_balance_info:
            balance_info = st.session_state.team_balance_info
            
            st.markdown("### 📊 Hold Balance")
            col1, col2, col3 = st.columns(3)
            
            with col1:
                st.metric("Hold 1 Styrke", 
                         f"{balance_info['team1_strength']:.1%}")
            
            with col2:
                st.metric("Hold 2 Styrke", 
                         f"{balance_info['team2_strength']:.1%}")
            
            with col3:
                difference = balance_info['strength_difference']
                balance_quality = "Perfekt" if difference < 0.05 else "Meget godt" if difference < 0.10 else "Godt" if difference < 0.20 else "Acceptabelt"
                st.metric("Balance Score", 
                         f"{balance_info['balance_percentage']:.1f}%",
                         delta=f"{balance_quality}")
        
        # Action buttons
        st.markdown("---")
        
        # Check if teams are already confirmed
        if st.session_state.get('teams_saved', False):
            st.success("✅ Hold er bekræftet og gemt! Gå til **Træningshistorik** for at registrere vinder efter kampen.")
            
            # Show confirmed teams actions
            col1, col2, col3 = st.columns(3)
            
            with col1:
                st.button("🔄 Generer Nye Hold", use_container_width=True,
                         on_click=generate_teams_callback)
            
            with col2:
                st.button("🗑️ Ryd Hold", use_container_width=True,
                         on_click=clear_teams_callback)
            
            with col3:
                st.button("📋 Kopiér til Clipboard", use_container_width=True,
                         on_click=copy_teams_callback)
        else:
            # Show confirm button for new teams
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                def confirm_teams_callback():
                    # Save as pending match
                    teams = st.session_state.generated_teams
                    if teams:
                        pending_match_id = save_pending_match(teams['team1'], teams['team2'])
                        if pending_match_id:
                            st.session_state.pending_match_id = pending_match_id
                            st.session_state.teams_saved = True
                
                st.button("✅ Bekræft Hold", use_container_width=True, type="primary",
                         help="Bekræft hold og gem til træningshistorik",
                         on_click=confirm_teams_callback)
            
            with col2:
                st.button("🔄 Generer Nye Hold", use_container_width=True,
                         on_click=generate_teams_callback)
            
            with col3:
                st.button("🗑️ Ryd Hold", use_container_width=True,
                         on_click=clear_teams_callback)
            
            with col4:
                st.button("📋 Kopiér til Clipboard", use_container_width=True,
                         on_click=copy_teams_callback)
        
        # Display team text if requested
        if st.session_state.get('show_team_text', False):
            st.code(st.session_state.get('team_text_to_display', ''), language="text")
            st.success("Hold information vist ovenfor - kopiér manuelt")
            # Clear the display flag
            st.session_state.show_team_text = False
    
    
    # Clear all button
    st.markdown("---")
    st.button("🗑️ Ryd Alt", help="Ryd alle valg og generede hold",
             on_click=clear_all_callback)