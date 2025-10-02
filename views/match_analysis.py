"""Match Analysis view - Player performance in actual matches."""

import streamlit as st
import pandas as pd
from datetime import datetime
from utils.match_history_scraper import (
    fetch_match_history, 
    explore_dbu_structure,
    cross_reference_with_spond,
    calculate_player_match_winrates
)


def display_match_analysis():
    """Display match analysis with player win rates from actual matches."""
    st.title("⚽ Kampanalyse - Rigtige Kampe")
    
    st.markdown("""
    Her kan du se hvordan hver spiller performer i **rigtige kampe** baseret på:
    - 🏆 **DBU kampresultater** (fra den officielle hjemmeside)  
    - 👥 **Spond fremmøde** (hvem spillede med i kampene)
    - 📊 **Individuel statistik** per spiller
    """)
    
    # Controls
    col1, col2, col3 = st.columns([1, 1, 2])
    
    with col1:
        if st.button("🔄 Opdater Kampdata", help="Hent nyeste kampe fra DBU"):
            st.cache_data.clear()
            st.rerun()
    
    with col2:
        if st.button("🔍 Undersøg DBU Struktur", help="Find kamphistorik links"):
            with st.spinner("Undersøger DBU hjemmeside..."):
                links = explore_dbu_structure()
                if links:
                    st.success(f"Fandt {len(links)} potentielle kamphistorik links:")
                    for link in links[:5]:  # Show first 5
                        st.write(f"- [{link['text']}]({link['full_url']})")
                else:
                    st.warning("Ingen kamphistorik links fundet")
    
    with col3:
        st.info("📅 Data sammenkører automatisk DBU kampe med Spond fremmøde")
    
    # Fetch and process data
    with st.spinner("Henter kampdata fra DBU..."):
        matches = fetch_match_history()
    
    if not matches:
        st.warning("⚠️ Kunne ikke hente kamphistorik fra DBU")
        st.markdown("""
        **Mulige årsager:**
        - DBU hjemmeside struktur er ændret
        - Kamphistorik findes på anden URL
        - Netværksproblemer
        
        **Debug information:**
        Prøv 'Undersøg DBU Struktur' knappen for at finde kampdata.
        """)
        return
    
    # Get real Spond events data
    with st.spinner("Henter Spond events..."):
        try:
            import asyncio
            from spond_integration import SpondIntegration
            
            # Function to get Spond events
            async def get_spond_events():
                spond = SpondIntegration()
                try:
                    # Get events from the last 90 days to cover the season
                    events = await spond.get_team_events(days_back=90)
                    members = await spond.get_team_members()
                    return events, members
                finally:
                    await spond.close()
            
            # Run async function
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            try:
                spond_events, spond_members = loop.run_until_complete(get_spond_events())
            finally:
                loop.close()
                
            st.success(f"✅ Hentet {len(spond_events)} Spond events og {len(spond_members)} medlemmer")
            
        except Exception as e:
            st.error(f"❌ Kunne ikke hente Spond data: {e}")
            spond_events = []
            spond_members = []
    
    # Cross-reference with Spond events
    if spond_events:
        with st.spinner("Sammenkører DBU kampe med Spond events..."):
            from utils.match_history_scraper import cross_reference_with_spond, calculate_player_match_winrates
            
            # Convert to DataFrame format expected by the function
            events_df = pd.DataFrame(spond_events)
            
            matched_matches = cross_reference_with_spond(matches, events_df)
            
            if matched_matches:
                st.success(f"🎉 Matchet {len(matched_matches)} kampe med Spond data!")
                
                # Calculate player statistics with member mapping
                player_stats = calculate_player_match_winrates(matched_matches, spond_members)
            else:
                st.warning("⚠️ Kunne ikke matche nogen kampe med Spond events")
                matched_matches = []
                player_stats = {}
    else:
        st.warning("Ingen Spond events fundet - viser kun DBU data")
        # Fallback to DBU-only data
        matched_matches = []
        for match in matches:
            if match.get('date') and match.get('result'):
                from utils.match_history_scraper import parse_match_date, determine_match_result
                
                match_date = parse_match_date(match['date'])
                if match_date:
                    result, our_goals, opp_goals = determine_match_result(match)
                    
                    if result:
                        match_analysis = {
                            'date': match_date,
                            'opponent': match.get('opponent', 'Unknown'),
                            'venue': match.get('venue', 'Unknown'),
                            'is_home': match.get('is_home', False),
                            'result': result,  # W/L/D
                            'our_goals': our_goals,
                            'opponent_goals': opp_goals,
                            'match_id': match.get('match_id', ''),
                            'spond_event_id': '',
                            'attendees': [],
                            'total_attendees': 0
                        }
                        matched_matches.append(match_analysis)
        player_stats = {}
    
    # Display results
    st.subheader("🏆 Kampresultater denne sæson")
    
    # Season overview
    total_matches = len(matched_matches)
    wins = sum(1 for m in matched_matches if m['result'] == 'W')
    draws = sum(1 for m in matched_matches if m['result'] == 'D') 
    losses = sum(1 for m in matched_matches if m['result'] == 'L')
    
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Kampe Spillet", total_matches)
    with col2:
        st.metric("Sejre", wins, f"{wins/total_matches*100:.1f}%" if total_matches > 0 else "0%")
    with col3:
        st.metric("Uafgjort", draws, f"{draws/total_matches*100:.1f}%" if total_matches > 0 else "0%")
    with col4:
        st.metric("Nederlag", losses, f"{losses/total_matches*100:.1f}%" if total_matches > 0 else "0%")
    
    # Match history table
    st.subheader("📋 Kamphistorik")
    
    if matched_matches:
        match_df = pd.DataFrame([
            {
                'Dato': match['date'].strftime('%d/%m/%Y'),
                'Modstander': match['opponent'],
                'Resultat': f"{match['our_goals']}-{match['opponent_goals']}",
                'Udfald': '🏆' if match['result'] == 'W' else '🤝' if match['result'] == 'D' else '❌',
                'Fremmødte': match['total_attendees']
            }
            for match in sorted(matched_matches, key=lambda x: x['date'], reverse=True)
        ])
        
        st.dataframe(match_df, width="stretch")
    
    # Player statistics
    st.subheader("👥 Spillerstatistikker (Rigtige Kampe)")
    
    if player_stats and len(player_stats) > 0:
        # Create DataFrame for player stats
        stats_data = []
        for player_name, stats in player_stats.items():
            if stats['matches_played'] > 0:
                stats_data.append({
                    'Spiller': player_name,
                    'Kampe': stats['matches_played'],
                    'Sejre': stats['wins'],
                    'Uafgjort': stats['draws'], 
                    'Nederlag': stats['losses'],
                    'Sejrsprocent': f"{stats['win_rate']*100:.1f}%",
                    'Point/Kamp': f"{stats['points_per_match']:.2f}",
                    'Mål For/Kamp': f"{stats['avg_goals_for']:.2f}",
                    'Mål Imod/Kamp': f"{stats['avg_goals_against']:.2f}",
                    'Målforskel': f"+{stats['goal_difference']}" if stats['goal_difference'] > 0 else str(stats['goal_difference'])
                })
        
        if stats_data:
            stats_df = pd.DataFrame(stats_data)
            
            # Sort by win rate (then by matches played for tie-breaking)
            stats_df['_win_rate_sort'] = [float(x.replace('%', '')) for x in stats_df['Sejrsprocent']]
            stats_df = stats_df.sort_values(['_win_rate_sort', 'Kampe'], ascending=[False, False])
            stats_df = stats_df.drop('_win_rate_sort', axis=1)
            
            st.dataframe(
                stats_df,
                width="stretch",
                column_config={
                    "Sejrsprocent": st.column_config.ProgressColumn(
                        "Sejrsprocent", 
                        help="Procentdel af kampe vundet",
                        min_value=0,
                        max_value=100,
                        format="%.1f%%"
                    )
                }
            )
            
            # Top performers
            st.subheader("🌟 Top Performere")
            
            # Filter players with at least 2 matches
            experienced_players = [p for p in stats_data if p['Kampe'] >= 2]
            
            if len(experienced_players) >= 3:
                col1, col2, col3 = st.columns(3)
                
                # Sort by win rate for experienced players
                experienced_players.sort(key=lambda x: float(x['Sejrsprocent'].replace('%', '')), reverse=True)
                
                with col1:
                    st.metric(
                        "🥇 Bedste Sejrsprocent",
                        experienced_players[0]['Spiller'],
                        experienced_players[0]['Sejrsprocent'] 
                    )
                
                with col2:
                    most_matches = max(stats_data, key=lambda x: x['Kampe'])
                    st.metric(
                        "⚽ Flest Kampe",
                        most_matches['Spiller'], 
                        f"{most_matches['Kampe']} kampe"
                    )
                
                with col3:
                    # Find player with highest points per match (min 2 games)
                    if experienced_players:
                        best_points = max(experienced_players, key=lambda x: float(x['Point/Kamp']))
                        st.metric(
                            "📈 Bedst Point/Kamp",
                            best_points['Spiller'],
                            best_points['Point/Kamp']
                        )
        else:
            st.info("Ingen spillerdata med kampdeltagelse fundet.")
            
    else:
        st.info("""
        **Spillerstatistikker vises når:**
        1. � Spond kampevents er hentet (✅ Done)
        2. 🔗 DBU kampe matches med Spond events
        3. 📊 Der er deltagere registreret i kampevents
        
        **Mulige årsager til ingen data:**
        - Kampevents i Spond har ingen deltagere registreret
        - Datoer matcher ikke mellem DBU og Spond (+/- 3 dage tolerance)
        - Kampevents er markeret som træning i stedet for kampe
        """)
    
    # Debug information
    with st.expander("🔧 Debug Information"):
        col1, col2 = st.columns(2)
        
        with col1:
            st.write("**DBU Data:**")
            st.write(f"- Fundne kampe: {len(matches) if matches else 0}")
            if matches:
                st.write("- Første kamp:")
                first_match = matches[0]
                st.json({
                    'dato': first_match.get('date'),
                    'modstander': first_match.get('opponent'),
                    'resultat': first_match.get('result'),
                    'hjemmebane': first_match.get('is_home')
                })
        
        with col2:
            st.write("**Spond Integration:**")
            st.write(f"- Spond events hentet: {len(spond_events) if 'spond_events' in locals() else 0}")
            st.write(f"- Matchede kampe: {len(matched_matches)}")
            st.write(f"- Spillere med data: {len(player_stats) if player_stats else 0}")
            
            if matched_matches:
                st.write("- Første matchede kamp:")
                first_matched = matched_matches[0]
                st.json({
                    'dato': str(first_matched.get('date')),
                    'modstander': first_matched.get('opponent'),
                    'deltagere': first_matched.get('total_attendees'),
                    'spond_event_id': first_matched.get('spond_event_id', 'N/A')[:10] + '...' if first_matched.get('spond_event_id') else 'N/A'
                })
        
        if 'spond_events' in locals() and spond_events:
            st.write("**Spond Events Sample:**")
            sample_events = []
            for event in spond_events[:3]:
                sample_events.append({
                    'heading': event.get('heading', 'No title'),
                    'start': event.get('startTimestamp', 'No date')[:10] if event.get('startTimestamp') else 'No date',
                    'responses': len(event.get('responses', {}).get('acceptedIds', []))
                })
            st.json(sample_events)