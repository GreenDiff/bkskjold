"""Dashboard page for Spond application."""

import streamlit as st
import app_config
from utils.data_loader import load_member_data, sync_data_wrapper
from utils.helpers import calculate_statistics
from components.charts import display_dashboard_charts
from components.player_display import display_player_fines_section


def display_dashboard():
    """Display the main team management dashboard with charts and tables only."""
    st.title("📊 BK Skjolds Statistik Dashboard")
    
    # Sync button
    col1, col2, col3 = st.columns([3, 2, 1])
    with col3:
        if st.button("🔄 Synkronisér Data", use_container_width=True):
            with st.spinner("Synkroniserer data fra Spond..."):
                sync_data_wrapper()
            st.rerun()
    st.markdown("---")

    # Load data
    fines_data = st.session_state.fines_calculator.processed_fines_data
    member_data = load_member_data()
    
    # Load training data
    try:
        import json
        with open('training_matches.json', 'r') as f:
            training_data = json.load(f)
    except FileNotFoundError:
        training_data = []
    
    # Load detailed fines data
    try:
        with open('fines_data.json', 'r') as f:
            detailed_fines = json.load(f)
    except FileNotFoundError:
        detailed_fines = {}

    # ========================================
    # TOP 3 INTRO SEKTION
    # ========================================
    st.header("🏆 Top Performere")
    
    # Calculate all stats first for top 3 sections
    player_stats = {}
    if training_data:
        for match in training_data:
            if 'team1' in match and 'team2' in match and 'winning_team' in match:
                team1 = match['team1']
                team2 = match['team2']
                winning_team_num = match['winning_team']
                
                if winning_team_num == 1:
                    winner_team = team1
                    loser_team = team2
                elif winning_team_num == 2:
                    winner_team = team2
                    loser_team = team1
                else:
                    continue
                
                for player in winner_team:
                    if player not in player_stats:
                        player_stats[player] = {'wins': 0, 'losses': 0, 'total': 0}
                    player_stats[player]['wins'] += 1
                    player_stats[player]['total'] += 1
                
                for player in loser_team:
                    if player not in player_stats:
                        player_stats[player] = {'wins': 0, 'losses': 0, 'total': 0}
                    player_stats[player]['losses'] += 1
                    player_stats[player]['total'] += 1

    # Calculate player fines for top 3 bøder
    player_fines_data = {}
    for fine_id, fine in detailed_fines.items():
        player_name = fine['player_name']
        fine_amount = fine['fine_amount']
        
        if player_name not in player_fines_data:
            player_fines_data[player_name] = {'total': 0}
        player_fines_data[player_name]['total'] += fine_amount

    # Also include legacy fines data
    if fines_data:
        for member_id, data in fines_data.items():
            if member_data and member_id in member_data:
                player_name = member_data[member_id]['name']
            else:
                player_name = f"Medlem {member_id}"
            
            legacy_total = (data.get('no_show_count', 0) * app_config.NO_SHOW_FINE +
                          data.get('late_response_count', 0) * app_config.LATE_RESPONSE_FINE)
            
            if player_name not in player_fines_data:
                player_fines_data[player_name] = {'total': 0}
            player_fines_data[player_name]['total'] += legacy_total

    # Helper function to get player photo
    def get_player_photo(player_name):
        if member_data:
            for member in member_data.values():
                if member['name'] == player_name:
                    return member.get('profilePicture', '')
        return ''
    
    # Helper function to get first name only
    def get_first_name(full_name):
        return full_name.split()[0] if full_name else full_name

    # Helper function to display top 3 with photos  
    def display_top3(title, emoji, players_data, value_key, value_suffix=""):
        st.subheader(f"{emoji} {title}")
        
        if not players_data:
            st.info("Ingen data tilgængelig endnu.")
            return
        
        medals = ["🥇", "🥈", "🥉"]
        colors = ["#FFD700", "#C0C0C0", "#CD7F32"]  # Guld, Sølv, Bronze
        
        # Display top 3 in a vertical layout for each section
        for i, (player_name, data) in enumerate(players_data[:3]):
            first_name = get_first_name(player_name)
            # Format value without decimals for percentages and with proper formatting
            if value_suffix == "%":
                formatted_value = f"{data[value_key]:.0f}"
            else:
                formatted_value = str(data[value_key])
            
            photo_url = get_player_photo(player_name)
            
            if photo_url:
                photo_html = f'<img src="{photo_url}" style="width: 50px; height: 50px; border-radius: 50%; object-fit: cover; margin-right: 10px;">'
            else:
                photo_html = '''
                <div style="width: 50px; height: 50px; background-color: #f0f0f0; 
                            display: flex; align-items: center; justify-content: center; 
                            border-radius: 50%; margin-right: 10px;">
                    <span style="font-size: 20px;">👤</span>
                </div>
                '''
            
            st.markdown(f"""
            <div style="display: flex; align-items: center; padding: 10px; margin: 5px 0;
                       border: 2px solid {colors[i]}; border-radius: 10px; 
                       background-color: {colors[i]}15; pointer-events: none;">
                {photo_html}
                <div style="flex-grow: 1;">
                    <div style="font-weight: bold; font-size: 16px;">{medals[i]} {first_name}</div>
                    <div style="color: {colors[i]}; font-weight: bold; font-size: 18px;">{formatted_value}{value_suffix}</div>
                </div>
            </div>
            """, unsafe_allow_html=True)

    # Create top 3 sections with fixed CSS to prevent sidebar issues
    st.markdown("""
    <style>
    .top3-container {
        display: flex !important;
        justify-content: space-between !important;
        gap: 15px !important;
        margin: 20px 0 !important;
        width: 100% !important;
    }
    .top3-section {
        flex: 1 !important;
        min-width: 0 !important;
    }
    </style>
    """, unsafe_allow_html=True)
    
    st.markdown('<div class="top3-container">', unsafe_allow_html=True)
    
    col1, col2, col3 = st.columns(3, gap="medium")
    
    with col1:
        st.markdown('<div class="top3-section">', unsafe_allow_html=True)
        # Top 3 Træningssejre
        if player_stats:
            top_wins = sorted(player_stats.items(), key=lambda x: x[1]['wins'], reverse=True)
            display_top3("Træningssejre", "⚽", top_wins, 'wins', " sejre")
        else:
            st.subheader("⚽ Træningssejre")
            st.info("Ingen data tilgængelig endnu.")
        st.markdown('</div>', unsafe_allow_html=True)
    
    with col2:
        st.markdown('<div class="top3-section">', unsafe_allow_html=True)
        # Top 3 Winrates
        if player_stats:
            winrate_list = []
            for player, stats in player_stats.items():
                if stats['total'] > 0:
                    winrate = (stats['wins'] / stats['total']) * 100
                    winrate_list.append((player, {'winrate': winrate}))
            
            top_winrates = sorted(winrate_list, key=lambda x: x[1]['winrate'], reverse=True)
            display_top3("Winrates", "📈", top_winrates, 'winrate', "%")
        else:
            st.subheader("📈 Winrates")
            st.info("Ingen data tilgængelig endnu.")
        st.markdown('</div>', unsafe_allow_html=True)
    
    with col3:
        st.markdown('<div class="top3-section">', unsafe_allow_html=True)
        # Top 3 Bøder (højeste beløb)
        if player_fines_data:
            top_fines = sorted([(name, data) for name, data in player_fines_data.items() if data['total'] > 0], 
                             key=lambda x: x[1]['total'], reverse=True)
            display_top3("Bøder", "💰", top_fines, 'total', " kr")
        else:
            st.subheader("💰 Bøder")
            st.info("Ingen data tilgængelig endnu.")
        st.markdown('</div>', unsafe_allow_html=True)
    
    st.markdown('</div>', unsafe_allow_html=True)

    st.markdown("---")

    # ========================================
    # TRÆNINGER SEKTION
    # ========================================
    st.header("⚽ Træninger")
    
    if player_stats:
        import plotly.graph_objects as go
        
        # Prepare data - sorteret efter flest træninger først, så flest sejre
        sorted_players = sorted(player_stats.items(), key=lambda x: (x[1]['total'], x[1]['wins']), reverse=True)
        players = [item[0] for item in sorted_players]
        wins = [item[1]['wins'] for item in sorted_players]
        losses = [item[1]['losses'] for item in sorted_players]
        
        fig = go.Figure()
        
        # Add wins (bottom of stack)
        fig.add_trace(go.Bar(
            name='Sejre',
            x=players,
            y=wins,
            marker_color='#2ca02c'
        ))
        
        # Add losses (top of stack)
        fig.add_trace(go.Bar(
            name='Tab',
            x=players,
            y=losses,
            marker_color='#d62728'
        ))
        
        fig.update_layout(
            barmode='stack',
            title='Træningskampe',
            xaxis_title='Spillere',
            yaxis_title='Antal Kampe',
            height=500,
            xaxis_tickangle=-45
        )
        
        st.plotly_chart(fig, use_container_width=True)
        
        # Calculate win rates and sort by winrate percentage
        winrate_data = []
        for player, stats in player_stats.items():
            total = stats['total']
            if total > 0:
                winrate = (stats['wins'] / total) * 100
                winrate_data.append((player, winrate))
        
        # Sort by winrate percentage (highest first)
        winrate_data.sort(key=lambda x: x[1], reverse=True)
        win_rates = [item[0] for item in winrate_data]
        winrate_values = [item[1] for item in winrate_data]
        
        # Farvekodning baseret på winrate: >50% = grøn, =50% = blå, <50% = rød
        colors = []
        for rate in winrate_values:
            if rate > 50:
                colors.append('#2ca02c')  # Grøn
            elif rate == 50:
                colors.append('#1f77b4')  # Blå
            else:
                colors.append('#d62728')  # Rød
        
        fig = go.Figure()
        fig.add_trace(go.Bar(
            x=win_rates,
            y=winrate_values,
            marker_color=colors,
            text=[f'{rate:.1f}%' for rate in winrate_values],
            textposition='outside'
        ))
        
        fig.update_layout(
            title='Spilleres Winrates',
            xaxis_title='Spillere',
            yaxis_title='Winrate (%)',
            height=500,
            xaxis_tickangle=-45,
            yaxis_range=[0, 100]
        )
        
        st.plotly_chart(fig, use_container_width=True)
        
    else:
        st.info("Ingen træningsdata tilgængelig endnu.")
    
    st.markdown("---")

    # ========================================
    # BØDER SEKTION
    # ========================================
    st.header("💰 Bøder")
    
    # Recalculate detailed fines data for charts (including paid/unpaid info)
    detailed_player_fines = {}
    fine_type_totals = {}
    
    for fine_id, fine in detailed_fines.items():
        player_name = fine['player_name']
        fine_type = fine['fine_type']
        fine_amount = fine['fine_amount']
        is_paid = fine.get('paid', False)
        
        if player_name not in detailed_player_fines:
            detailed_player_fines[player_name] = {
                'paid': 0,
                'unpaid': 0,
                'total': 0
            }
        
        if is_paid:
            detailed_player_fines[player_name]['paid'] += fine_amount
        else:
            detailed_player_fines[player_name]['unpaid'] += fine_amount
        
        detailed_player_fines[player_name]['total'] += fine_amount
        
        # Count by fine type - handle manual fines separately
        if fine_type == 'manual':
            # For manual fines, use the fine_subtype or get name from session state
            fine_subtype = fine.get('fine_subtype', 'unknown_manual')
            
            # Try to get the actual name from permanent manual_fine_types file
            try:
                import json
                with open('manual_fine_types.json', 'r') as f:
                    manual_fine_types = json.load(f)
            except (FileNotFoundError, json.JSONDecodeError):
                manual_fine_types = st.session_state.get('manual_fine_types', {})
            if fine_subtype in manual_fine_types:
                display_name = manual_fine_types[fine_subtype]['name']
            else:
                # Fallback to formatting the subtype nicely
                display_name = fine_subtype.replace('_', ' ').title()
            
            if display_name not in fine_type_totals:
                fine_type_totals[display_name] = 0
            fine_type_totals[display_name] += fine_amount
        else:
            # For non-manual fines, use the original logic
            if fine_type not in fine_type_totals:
                fine_type_totals[fine_type] = 0
            fine_type_totals[fine_type] += fine_amount
    
    # Also include legacy fines data
    if fines_data:
        for member_id, data in fines_data.items():
            # Get member name
            if member_data and member_id in member_data:
                player_name = member_data[member_id]['name']
            else:
                player_name = f"Medlem {member_id}"
            
            no_show_total = data.get('no_show_count', 0) * app_config.NO_SHOW_FINE
            late_response_total = data.get('late_response_count', 0) * app_config.LATE_RESPONSE_FINE
            
            if player_name not in detailed_player_fines:
                detailed_player_fines[player_name] = {'paid': 0, 'unpaid': 0, 'total': 0}
            
            # Assume legacy fines are unpaid
            detailed_player_fines[player_name]['unpaid'] += no_show_total + late_response_total
            detailed_player_fines[player_name]['total'] += no_show_total + late_response_total
            
            # Add to type totals
            if no_show_total > 0:
                fine_type_totals['no_show'] = fine_type_totals.get('no_show', 0) + no_show_total
            if late_response_total > 0:
                fine_type_totals['late_response'] = fine_type_totals.get('late_response', 0) + late_response_total
    
    if detailed_player_fines:
        
        # Sort players by total fines
        sorted_players = sorted(detailed_player_fines.items(), key=lambda x: x[1]['total'], reverse=True)
        
        players = [item[0] for item in sorted_players if item[1]['total'] > 0]
        paid_amounts = [item[1]['paid'] for item in sorted_players if item[1]['total'] > 0]
        unpaid_amounts = [item[1]['unpaid'] for item in sorted_players if item[1]['total'] > 0]
        
        fig = go.Figure()
        
        # Add paid fines (bottom of stack)
        fig.add_trace(go.Bar(
            name='Betalt',
            x=players,
            y=paid_amounts,
            marker_color='#2ca02c'
        ))
        
        # Add unpaid fines (top of stack)
        fig.add_trace(go.Bar(
            name='Ubetalt',
            x=players,
            y=unpaid_amounts,
            marker_color='#d62728'
        ))
        
        fig.update_layout(
            barmode='stack',
            title='Bøder - Betalt & Ubetalt',
            xaxis_title='Spillere',
            yaxis_title='Bøde Beløb',
            height=500,
            xaxis_tickangle=-45
        )
        
        st.plotly_chart(fig, use_container_width=True)
        
        if fine_type_totals:
            # Map fine types to Danish names (only for automatic types)
            type_name_map = {
                'training_loss': 'Tab af Træningskamp',
                'no_show': 'Udeblivelser',
                'late_response': 'Sene Svar'
            }
            
            # Create labels - manual fine types already have their display names
            labels = []
            for ft in fine_type_totals.keys():
                # If it's a standard fine type, use the map, otherwise use as-is (for manual fines)
                if ft in type_name_map:
                    labels.append(type_name_map[ft])
                else:
                    # This is already a formatted name from manual fine types
                    labels.append(ft)
            
            values = list(fine_type_totals.values())
            
            fig = go.Figure(data=[go.Pie(
                labels=labels,
                values=values,
                textinfo='label+percent',
                textposition='outside'
            )])
            
            fig.update_layout(
                title='Fordeling af Bødetyper (%)',
                height=500
            )
            
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("Ingen bødedata at vise.")
    else:
        st.info("Ingen bødedata tilgængelig endnu.")
    
    # Information footer
    st.markdown("---")
    st.info(f"📅 **Information:** Data fra {app_config.FINES_CUTOFF_DATE} og fremefter")