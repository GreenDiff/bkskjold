"""Helper functions for Spond application."""

from datetime import datetime
import pandas as pd


def format_datetime_string(timestamp_str):
    """Format datetime string for display."""
    try:
        if 'T' in timestamp_str:
            return timestamp_str[:19].replace('T', ' ')
        return timestamp_str
    except (TypeError, AttributeError):
        return "N/A"


def calculate_statistics(fines_data, member_data):
    """Calculate key statistics from fines and member data."""
    total_players = len(member_data)  # Count all team members, not just those with fines
    total_fines = sum(data['total_fine'] for data in fines_data.values())
    avg_fine = total_fines / total_players if total_players > 0 else 0
    
    # Count unique players with fines (ensure no duplicates)
    players_with_fines = len([name for name, data in fines_data.items() if data['total_fine'] > 0])
    
    # Debug: Check if there are more players with fines than total players
    if players_with_fines > total_players:
        print(f"⚠️  Warning: {players_with_fines} players with fines > {total_players} total players")
        print(f"Players with fines: {[name for name, data in fines_data.items() if data['total_fine'] > 0]}")
        print(f"All members: {list(member_data.keys()) if member_data else 'No member data'}")
        # Cap it to total players as a safety measure
        players_with_fines = min(players_with_fines, total_players)
    
    return {
        'total_players': total_players,
        'total_fines': total_fines,
        'avg_fine': avg_fine,
        'players_with_fines': players_with_fines
    }


def prepare_chart_data(fines_data):
    """Prepare data for chart visualization."""
    df = pd.DataFrame([
        {
            'Player': name,
            'Total Fine': data['total_fine'],
            'No Show': data['no_show_count'],
            'Late Response': data['late_response_count']
        }
        for name, data in fines_data.items()
    ])
    
    if not df.empty:
        # Sort by total fine descending
        df = df.sort_values('Total Fine', ascending=False)
    
    return df


def get_fine_color(total_fine):
    """Get color for fine visualization based on amount."""
    if total_fine <= 100:
        return "#28a745"  # Green
    elif total_fine <= 500:
        return "#ffc107"  # Yellow
    else:
        return "#dc3545"  # Red


def calculate_bar_percentages(total_fine, paid_amount, unpaid_amount):
    """Calculate percentages for stacked bar visualization."""
    total_width = min(100, (total_fine / 1000) * 100) if total_fine > 0 else 5
    paid_percentage = (paid_amount / total_fine * 100) if total_fine > 0 else 0
    unpaid_percentage = (unpaid_amount / total_fine * 100) if total_fine > 0 else 0
    
    return total_width, paid_percentage, unpaid_percentage