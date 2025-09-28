"""Team selector page for random team generation with football pitch layout."""

import streamlit as st
import random
from utils.data_loader import load_member_data


def get_player_data_dict(member_data):
    """Convert member data to a dictionary with names as keys."""
    player_dict = {}
    if member_data:
        for member in member_data.values():
            name = f"{member.get('firstName', '')} {member.get('lastName', '')}".strip()
            if name:
                player_dict[name] = member
    return player_dict


def display_player_row(player_name, player_data, team_color="#28a745"):
    """Display a player in a row with photo and name."""
    col1, col2 = st.columns([1, 4])
    
    with col1:
        if player_data:
            profile_image = player_data.get('profilePicture', '')
            if profile_image:
                st.image(profile_image, width=80)
            else:
                # Default football player image for team members without photos
                default_image = "https://i2-prod.birminghammail.co.uk/article10620537.ece/ALTERNATES/s1200c/Obese-Manchester-united-supporter.jpg"
                st.image(default_image, width=80)
        else:
            # For manual players - use same default as team members without photos
            default_image = "https://i2-prod.birminghammail.co.uk/article10620537.ece/ALTERNATES/s1200c/Obese-Manchester-united-supporter.jpg"
            st.image(default_image, width=80)
    
    with col2:
        # Use larger text that automatically adapts to theme
        st.markdown(f"### {player_name}")



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
                st.markdown("---")
        else:
            st.write("Ingen spillere på hold 1")
    
    with col2:
        st.markdown("### ⚫ Hold 2 (Sort)")
        if teams['team2']:
            for player in teams['team2']:
                player_data = player_dict.get(player)
                display_player_row(player, player_data, "#ff7f0e")
                st.markdown("---")
        else:
            st.write("Ingen spillere på hold 2")
    
    # Display reserves if any
    if teams.get('remaining'):
        st.markdown("### ⚪ Reserve Spillere")
        for player in teams['remaining']:
            player_data = player_dict.get(player)
            display_player_row(player, player_data, "#2ca02c")
            st.markdown("---")


# Callback functions for buttons
def add_manual_player():
    """Add a manual player to the list."""
    new_player = st.session_state.get(f'new_player_input_{st.session_state.input_counter}', '').strip()
    if new_player and new_player not in st.session_state.manual_players:
        st.session_state.manual_players.append(new_player)
        if new_player not in st.session_state.selected_players:
            st.session_state.selected_players.append(new_player)
        st.session_state.input_counter += 1

def remove_manual_player(player_name):
    """Remove a manual player from the list."""
    if player_name in st.session_state.manual_players:
        st.session_state.manual_players.remove(player_name)
    if player_name in st.session_state.selected_players:
        st.session_state.selected_players.remove(player_name)

def generate_teams():
    """Generate random teams from selected players."""
    selected_players = st.session_state.selected_players
    if len(selected_players) >= 2:
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

def clear_teams():
    """Clear generated teams."""
    st.session_state.generated_teams = None

def clear_all():
    """Clear all selections and teams."""
    st.session_state.manual_players = []
    # Reset to all team players selected
    member_data = load_member_data()
    player_dict = get_player_data_dict(member_data)
    st.session_state.selected_players = list(player_dict.keys())
    st.session_state.generated_teams = None
    st.session_state.input_counter += 1

def display_team_selector():
    """Display the team selector page for training."""
    st.title("⚽ Hold Udvælger")
    st.info("Fravælg spillere der ikke er tilgængelige og generer tilfældige hold til træning")
    
    # Load member data
    member_data = load_member_data()
    player_dict = get_player_data_dict(member_data)
    
    # Initialize session state
    if 'manual_players' not in st.session_state:
        st.session_state.manual_players = []
    if 'selected_players' not in st.session_state:
        # Auto-select ALL players by default
        st.session_state.selected_players = list(player_dict.keys())
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
        
        # Available players from team roster - now auto-selected
        if member_data:
            st.write("**Holdmedlemmer (fravælg utilgængelige):**")
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
            st.button("➕ Tilføj", on_click=add_manual_player)
        
        # Display manual players with remove option
        if st.session_state.manual_players:
            st.write("**Eksterne Spillere:**")
            
            for i, player in enumerate(st.session_state.manual_players):
                col_name, col_remove = st.columns([4, 1])
                with col_name:
                    st.write(f"• {player}")
                with col_remove:
                    st.button("🗑️", key=f"remove_{player}_{i}", help=f"Fjern {player}", 
                             on_click=remove_manual_player, args=[player])
    
    with col2:
        st.subheader("⚙️ Hold Indstillinger")
        
        # Get total available players (manual players are now included in selected_team_members)
        total_selected = len(selected_team_members)
        
        st.metric("Tilgængelige Spillere", total_selected)
        
        # Generate teams button - automatic half and half split
        if total_selected >= 2:
            st.info(f"Hold størrelse: {total_selected // 2} spillere per hold")
            
            st.button("🎲 Generer Hold", use_container_width=True, type="primary", 
                     on_click=generate_teams)
            
            if total_selected < 2:
                st.error("Mindst 2 spillere nødvendig!")
        else:
            st.info("Vælg mindst 2 spillere for at generere hold")
    
    # Display generated teams
    if st.session_state.generated_teams:
        st.markdown("---")
        st.subheader("🏆 Genererede Hold")
        
        teams = st.session_state.generated_teams
        
        # Display teams layout
        display_teams_layout(teams, player_dict)
        
        # Action buttons
        st.markdown("---")
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.button("🔄 Generer Nye Hold", use_container_width=True, 
                     on_click=generate_teams)
        
        with col2:
            st.button("🗑️ Ryd Hold", use_container_width=True, 
                     on_click=clear_teams)
        
        with col3:
            # Export teams as text - this one can be inline since it just displays
            if st.button("📋 Kopiér til Clipboard", use_container_width=True):
                team_text = f"""⚪ Hold 1:
{chr(10).join([f"{i}. {player}" for i, player in enumerate(teams['team1'], 1)])}

⚫ Hold 2:
{chr(10).join([f"{i}. {player}" for i, player in enumerate(teams['team2'], 1)])}"""
                
                if teams['remaining']:
                    team_text += f"""

⚪ Reserve:
{chr(10).join([f"{i}. {player}" for i, player in enumerate(teams['remaining'], 1)])}"""
                
                st.code(team_text, language="text")
                st.success("Hold information vist ovenfor - kopiér manuelt")
    
    
    # Clear all button
    st.markdown("---")
    st.button("🗑️ Ryd Alt", help="Ryd alle valg og generede hold", 
             on_click=clear_all)