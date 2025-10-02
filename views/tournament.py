"""Tournament standings view for Spond application."""

import streamlit as st
import requests
from bs4 import BeautifulSoup
import json
import os
from datetime import datetime, timedelta
import pandas as pd


@st.cache_data(ttl=3600)  # Cache for 1 hour
def fetch_league_standings():
    """Fetch current league standings from DBU website."""
    try:
        url = 'https://www.dbu.dk/resultater/hold/460174_472317/stilling'
        headers = {'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36'}
        
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Find standings table
        table = soup.find('table', class_='sr--pool-position--table')
        if not table:
            return None
            
        rows = table.find_all('tr')[1:]  # Skip header
        standings = []
        
        for row in rows:
            cells = row.find_all('td')
            if len(cells) >= 8:
                # Get team name and logo
                team_name = cells[1].text.strip()
                logo_img = cells[1].find('img', class_='logo')
                logo_url = logo_img.get('src') if logo_img else None
                
                # Fix logo URL if relative
                if logo_url and not logo_url.startswith('http'):
                    logo_url = 'https://file.dbu.dk' + logo_url
                
                team_data = {
                    'position': int(cells[0].text.strip()),
                    'team': team_name,
                    'matches': int(cells[2].text.strip()),
                    'wins': int(cells[3].text.strip()),
                    'draws': int(cells[4].text.strip()),
                    'losses': int(cells[5].text.strip()),
                    'goals': cells[6].text.strip(),
                    'points': int(cells[7].text.strip()),
                    'logo_url': logo_url
                }
                standings.append(team_data)
        
        return standings
        
    except Exception as e:
        st.error(f"Fejl ved hentning af stillingsdata: {e}")
        return None


def display_team_logo(logo_url, team_name, size=50):
    """Display team logo with fallback."""
    if logo_url:
        try:
            st.image(logo_url, width=size)
        except:
            st.write("🏆")  # Fallback emoji
    else:
        st.write("🏆")  # Fallback emoji


def get_position_color(position):
    """Get color based on league position."""
    if position <= 2:
        return "#2E8B57"  # Green for top 2
    elif position <= 8:
        return "#4682B4"  # Blue for middle
    else:
        return "#CD5C5C"  # Red for bottom


def display_tournament():
    """Display tournament standings page."""
    st.title("🏆 Turnerings Stilling")
    
    # Add CSS for ultra minimal spacing between teams
    st.markdown("""
    <style>
    .stColumns > div {
        padding: 0 !important;
        margin: 0 !important;
        gap: 0 !important;
    }
    .tournament-row {
        margin: 0 !important;
        padding: 0 !important;
        line-height: 1 !important;
        height: auto !important;
        min-height: 25px !important;
    }
    div[data-testid="column"] {
        padding: 0 2px !important;
        margin: 0 !important;
        gap: 0 !important;
    }
    .stContainer {
        padding: 0 !important;
        margin: 0 !important;
    }
    .stContainer > div {
        gap: 0 !important;
        padding: 0 !important;
        margin: 0 !important;
    }
    .element-container {
        margin: 0 !important;
        padding: 0 !important;
    }
    [data-testid="stVerticalBlock"] > div {
        gap: 0.1rem !important;
    }
    .centered-text {
        text-align: center !important;
    }
    .centered-header {
        text-align: center !important;
        font-weight: bold !important;
    }
    </style>
    """, unsafe_allow_html=True)
    
    # Header with sync button
    col1, col2, col3 = st.columns([1, 1, 2])
    with col1:
        if st.button("🔄 Opdater Stilling", help="Hent nyeste data fra DBU"):
            st.cache_data.clear()
            st.rerun()
    
    with col3:
        st.info("📅 Data opdateres automatisk hver time")
    
    # Fetch standings data
    with st.spinner("Henter stillingsdata fra DBU..."):
        standings = fetch_league_standings()
    
    if not standings:
        st.error("❌ Kunne ikke hente stillingsdata fra DBU")
        st.info("🔧 Prøv at opdatere siden eller kontakt systemadministrator")
        return
    
    st.subheader("📊 Aktuel Stilling i Rækken")
    
    # Find BK Skjold's position
    bk_skjold_data = None
    for team in standings:
        if "skjold" in team['team'].lower() or "bk skjold" in team['team'].lower():
            bk_skjold_data = team
            break
    
    # Highlight BK Skjold's position if found
    if bk_skjold_data:
        
        # Show quick stats
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("Kampe Spillet", bk_skjold_data['matches'])
        with col2:
            st.metric("Sejre", bk_skjold_data['wins'])
        with col3:
            st.metric("Uafgjort", bk_skjold_data['draws'])
        with col4:
            st.metric("Nederlag", bk_skjold_data['losses'])
    
    # Display full standings table
    st.subheader("📋 Komplet Stilling")
    
    # Add table headers
    header_col1, header_col2, header_col3, header_col4, header_col5, header_col6, header_col7, header_col8, header_col9 = st.columns([1, 1, 4, 1, 1, 1, 1, 2, 1])
    
    with header_col1:
        st.markdown("<div class='centered-header'>Position</div>", unsafe_allow_html=True)
    with header_col2:
        st.markdown("<div class='centered-header'>Logo</div>", unsafe_allow_html=True)
    with header_col3:
        st.markdown("<div class='centered-header'>Hold</div>", unsafe_allow_html=True)
    with header_col4:
        st.markdown("<div class='centered-header'>Kampe</div>", unsafe_allow_html=True)
    with header_col5:
        st.markdown("<div class='centered-header'>Sejre</div>", unsafe_allow_html=True)
    with header_col6:
        st.markdown("<div class='centered-header'>Uafgjort</div>", unsafe_allow_html=True)
    with header_col7:
        st.markdown("<div class='centered-header'>Nederlag</div>", unsafe_allow_html=True)
    with header_col8:
        st.markdown("<div class='centered-header'>Mål</div>", unsafe_allow_html=True)
    with header_col9:
        st.markdown("<div class='centered-header'>Point</div>", unsafe_allow_html=True)
    
    # Create columns for the table
    for i, team in enumerate(standings):
        # Color code based on position
        position_color = get_position_color(team['position'])
        
        # Highlight BK Skjold
        is_bk_skjold = "skjold" in team['team'].lower()
        
        # Add separators at key positions (BEFORE the team row)
        if team['position'] == 3:
            st.markdown("<hr style='margin: 5px 0; border: 1px solid #FFD700;'>", unsafe_allow_html=True)
        elif team['position'] == 9:
            st.markdown("<hr style='margin: 5px 0; border: 1px solid #CD5C5C;'>", unsafe_allow_html=True)
        
        # Create row columns (same for all teams)
        col1, col2, col3, col4, col5, col6, col7, col8, col9 = st.columns([1, 1, 4, 1, 1, 1, 1, 2, 1])
        
        with col1:
            # Position with color
            pos_color = "#0DAC35" if team['position'] <= 2 else "#3232EA" if team['position'] <= 8 else "#B71D1D" if team['position'] <= 10 else "#808080"
            st.markdown(f"<div style='text-align: center; font-weight: bold; color: {pos_color}; font-size: 18px;'>{team['position']}</div>", unsafe_allow_html=True)
        
        with col2:
            # Team logo
            if team['logo_url']:
                try:
                    col_left, col_center, col_right = st.columns([1, 1, 1])
                    with col_center:
                        st.image(team['logo_url'], width=30)
                except:
                    st.markdown("<div class='centered-text'>🏆</div>", unsafe_allow_html=True)
            else:
                st.markdown("<div class='centered-text'>🏆</div>", unsafe_allow_html=True)
        
        with col3:
            # Team name - only BK Skjold gets bold styling
            if is_bk_skjold:
                name_style = "font-weight: bold; font-size: 16px; text-align: left;"
            else:
                name_style = "font-size: 14px; text-align: left;"
            st.markdown(f"<div style='{name_style}'>{team['team']}</div>", unsafe_allow_html=True)
        
        with col4:
            st.markdown(f"<div class='centered-text'>{team['matches']}</div>", unsafe_allow_html=True)  # Matches
        
        with col5:
            st.markdown(f"<div class='centered-text'>{team['wins']}</div>", unsafe_allow_html=True)  # Wins
        
        with col6:
            st.markdown(f"<div class='centered-text'>{team['draws']}</div>", unsafe_allow_html=True)  # Draws
        
        with col7:
            st.markdown(f"<div class='centered-text'>{team['losses']}</div>", unsafe_allow_html=True)  # Losses
        
        with col8:
            st.markdown(f"<div class='centered-text'>{team['goals']}</div>", unsafe_allow_html=True)  # Goals
        
        with col9:
            # Points - all teams get bold styling for points
            points_style = "font-weight: bold; text-align: center;"
            st.markdown(f"<div style='{points_style}'>{team['points']}</div>", unsafe_allow_html=True)
    
    # Add table headers for clarity  
    st.markdown("**Forklaring:** Pos | Logo | Hold | K | S | U | N | Mål | Point")
    
    # Additional statistics
    st.subheader("📈 Statistik")
    
    if standings:
        total_teams = len(standings)
        avg_points = sum(team['points'] for team in standings) / total_teams
        
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Hold i Rækken", total_teams)
        with col2:
            st.metric("Gennemsnit Point", f"{avg_points:.1f}")
        with col3:
            leader = standings[0] if standings else None
            if leader:
                st.metric("Førsteplads", f"{leader['team']} ({leader['points']} pt)")
    
    # Last updated info
    current_time = datetime.now().strftime("%d/%m/%Y kl. %H:%M")
    st.caption(f"📅 Sidst opdateret: {current_time} | Data fra DBU.dk")