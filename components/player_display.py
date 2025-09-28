"""Player display components for Spond application."""

import streamlit as st
from utils.helpers import get_fine_color, calculate_bar_percentages


def display_player_profile_image(member):
    """Display player profile image with fallback."""
    profile_image = member.get('profilePicture', '')
    
    if profile_image:
        st.image(profile_image, width=80)
    else:
        default_image = "https://i2-prod.birminghammail.co.uk/article10620537.ece/ALTERNATES/s1200c/Obese-Manchester-united-supporter.jpg"
        st.image(default_image, width=80)


def display_player_fine_bar(member_fines, total_fine):
    """Display stacked bar visualization for player fines."""
    # Calculate paid and unpaid amounts
    unpaid_amount = member_fines.get('unpaid_amount', 0)
    paid_amount = total_fine - unpaid_amount
    
    # Color coding for fine amounts
    base_color = get_fine_color(total_fine)
    
    # Calculate percentages for bar width
    total_width, paid_percentage, unpaid_percentage = calculate_bar_percentages(
        total_fine, paid_amount, unpaid_amount
    )
    
    # Create stacked bar: paid (lighter) + unpaid (darker)
    st.markdown(f"""
    <div style="background-color: #f0f0f0; border-radius: 10px; padding: 2px; margin: 5px 0;">
        <div style="position: relative; width: {total_width}%; height: 25px; border-radius: 8px; overflow: hidden;">
            <!-- Paid amount (lighter color) -->
            <div style="position: absolute; left: 0; top: 0; 
                        background-color: {base_color}80; 
                        width: {paid_percentage}%; height: 100%; 
                        border-radius: 8px 0 0 8px;"></div>
            <!-- Unpaid amount (darker color) -->
            <div style="position: absolute; left: {paid_percentage}%; top: 0; 
                        background-color: {base_color}; 
                        width: {unpaid_percentage}%; height: 100%; 
                        border-radius: 0 8px 8px 0;"></div>
            <!-- Text overlay -->
            <div style="position: absolute; top: 0; left: 0; width: 100%; height: 100%; 
                        display: flex; align-items: center; justify-content: flex-start; 
                        color: white; font-weight: bold; padding-left: 10px; z-index: 10;">
                {total_fine} kr
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)


def display_player_stats(member_fines, total_fine):
    """Display player statistics below the fine bar."""
    no_show_count = member_fines.get('no_show_count', 0)
    late_response_count = member_fines.get('late_response_count', 0)
    training_loss_count = member_fines.get('training_loss_count', 0)
    unpaid_amount = member_fines.get('unpaid_amount', 0)
    paid_amount = total_fine - unpaid_amount
    
    st.markdown(f"""
    <div style="font-size: 12px; color: #666; margin-top: 5px;">
        🚫 Udeblivelser: {no_show_count} | ⏰ Sene: {late_response_count} | 🏆 Træningskamp tab: {training_loss_count} | 
        💰 Betalt: {paid_amount} kr | 🔴 Ubetalt: {unpaid_amount} kr
    </div>
    """, unsafe_allow_html=True)


def display_player_fines_section(fines_data, member_data):
    """Display the complete player fines section."""
    if not member_data:
        st.warning("Ingen medlemsdata tilgængelige.")
        return
    
    # Collect all player data with fines for sorting
    players_with_data = []
    for member in member_data.values():
        # Use player name instead of ID to match with fines_data
        player_name = member.get('name', '')
        # Show all players, even those with zero fines
        if player_name in fines_data:
            member_fines = fines_data[player_name]
            total_fine = member_fines.get('total_fine', 0)
        else:
            # Player has no fines
            member_fines = {
                'total_fine': 0, 
                'no_show_count': 0, 
                'late_response_count': 0, 
                'training_loss_count': 0,
                'unpaid_amount': 0
            }
            total_fine = 0
        
        players_with_data.append({
            'member': member,
            'member_fines': member_fines,
            'total_fine': total_fine
        })
    
    # Sort players by total fine (descending - highest fines first)
    players_with_data.sort(key=lambda x: x['total_fine'], reverse=True)
    
    # Display sorted players
    for player_data in players_with_data:
        member = player_data['member']
        member_fines = player_data['member_fines']
        total_fine = player_data['total_fine']
        
        col1, col2 = st.columns([1, 4])
        
        with col1:
            display_player_profile_image(member)
        
        with col2:
            # Member name and stats
            name = member.get('firstName', 'Unknown') + ' ' + member.get('lastName', '')
            
            st.markdown(f"### {name}")
            display_player_fine_bar(member_fines, total_fine)
            display_player_stats(member_fines, total_fine)