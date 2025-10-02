"""Match history scraper for DBU website."""

import requests
from bs4 import BeautifulSoup
import json
import pandas as pd
from datetime import datetime
import streamlit as st


@st.cache_data(ttl=1800)  # Cache for 30 minutes
def fetch_match_history():
    """Fetch match history from DBU website."""
    try:
        # We know the specific URL that works
        url = 'https://www.dbu.dk/resultater/hold/460174_472317/kampprogram'
        headers = {'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36'}
        
        response = requests.get(url, headers=headers)
        if response.status_code == 200:
            soup = BeautifulSoup(response.text, 'html.parser')
            
            table = soup.find('table')
            if table:
                matches = parse_dbu_match_table(table)
                return matches
        
        return None
        
    except Exception as e:
        st.error(f"Fejl ved hentning af kamphistorik: {e}")
        return None


def parse_dbu_match_table(table):
    """Parse specific DBU match table format."""
    matches = []
    
    try:
        rows = table.find_all('tr')
        
        # Skip header row
        for row in rows[1:]:
            cells = row.find_all(['td', 'th'])
            
            # Expected columns: [empty, Kampnr, Dato, Tid, Hjemme, Ude, Spillested, Resultat]
            if len(cells) >= 7:
                try:
                    match_id = cells[1].get_text(strip=True) if len(cells) > 1 else ""
                    date_str = cells[2].get_text(strip=True) if len(cells) > 2 else ""
                    time_str = cells[3].get_text(strip=True) if len(cells) > 3 else ""
                    home_team = cells[4].get_text(strip=True) if len(cells) > 4 else ""
                    away_team = cells[5].get_text(strip=True) if len(cells) > 5 else ""
                    venue = cells[6].get_text(strip=True) if len(cells) > 6 else ""
                    result = cells[7].get_text(strip=True) if len(cells) > 7 else ""
                    
                    # Only process if we have essential data and result exists
                    if date_str and home_team and away_team and result and '-' in result:
                        
                        # Determine if we're home or away and who the opponent is
                        our_team_names = ['Skjold 13', 'BK Skjold', 'Skjold']
                        is_home = any(name.lower() in home_team.lower() for name in our_team_names)
                        is_away = any(name.lower() in away_team.lower() for name in our_team_names)
                        
                        if is_home or is_away:
                            opponent = away_team if is_home else home_team
                            
                            match_data = {
                                'match_id': match_id,
                                'date': date_str,
                                'time': time_str,
                                'home_team': home_team,
                                'away_team': away_team,
                                'venue': venue,
                                'result': result,
                                'opponent': opponent,
                                'is_home': is_home,
                                'raw_row': [cell.get_text(strip=True) for cell in cells]
                            }
                            matches.append(match_data)
                            
                except Exception as row_error:
                    # Skip problematic rows but continue processing
                    continue
        
        return matches if matches else None
        
    except Exception as e:
        print(f"Error parsing table: {e}")
        return None


def determine_match_result(match_data):
    """Determine if we won, lost, or drew based on match data."""
    try:
        result_str = match_data['result']
        is_home = match_data['is_home']
        
        # Parse score formats like "2-1", "1:3", "0 - 2"
        result_str = result_str.replace(' ', '').replace(':', '-')
        
        if '-' in result_str:
            parts = result_str.split('-')
            if len(parts) == 2:
                home_goals = int(parts[0])
                away_goals = int(parts[1])
                
                # Determine our goals vs opponent goals
                if is_home:
                    our_goals = home_goals
                    opponent_goals = away_goals
                else:
                    our_goals = away_goals
                    opponent_goals = home_goals
                
                # Determine result
                if our_goals > opponent_goals:
                    return 'W', our_goals, opponent_goals
                elif our_goals < opponent_goals:
                    return 'L', our_goals, opponent_goals
                else:
                    return 'D', our_goals, opponent_goals
        
        return None, None, None
        
    except (ValueError, IndexError, KeyError):
        return None, None, None


def cross_reference_with_spond(matches, spond_events):
    """Cross-reference DBU matches with Spond attendance data."""
    
    matched_data = []
    
    for match in matches:
        if not match.get('date') or not match.get('result'):
            continue
            
        # Try to parse the date
        match_date = parse_match_date(match['date'])
        if not match_date:
            continue
            
        # Find corresponding Spond event (within 3 days of match)
        closest_event = find_closest_spond_event(match_date, spond_events)
        
        if closest_event:
            result, our_goals, opp_goals = determine_match_result(match)
            
            if result:
                # Extract attendees from Spond event format
                if isinstance(closest_event, dict):
                    # Dict format from API
                    responses = closest_event.get('responses', {})
                    attendee_ids = responses.get('acceptedIds', [])
                    event_id = closest_event.get('id', '')
                else:
                    # DataFrame row format
                    responses = getattr(closest_event, 'responses', {}) or {}
                    attendee_ids = responses.get('acceptedIds', []) if isinstance(responses, dict) else []
                    event_id = getattr(closest_event, 'id', '')
                
                match_analysis = {
                    'date': match_date,
                    'opponent': match.get('opponent', 'Unknown'),
                    'venue': match.get('venue', 'Unknown'),
                    'is_home': match.get('is_home', False),
                    'result': result,  # W/L/D
                    'our_goals': our_goals,
                    'opponent_goals': opp_goals,
                    'match_id': match.get('match_id', ''),
                    'spond_event_id': event_id,
                    'attendees': attendee_ids,  # List of member IDs who accepted
                    'total_attendees': len(attendee_ids)
                }
                matched_data.append(match_analysis)
    
    return matched_data


def parse_match_date(date_str):
    """Parse DBU date formats like 'fre.22-08 2025' or 'søn.07-09 2025'."""
    try:
        # DBU format: "fre.22-08 2025" -> day.DD-MM YYYY
        if '.' in date_str and '-' in date_str:
            # Split by space to get date part and year
            parts = date_str.split()
            if len(parts) >= 2:
                year = parts[1]
                date_part = parts[0]
                
                # Extract DD-MM from "day.DD-MM"
                if '.' in date_part:
                    day_month = date_part.split('.')[1]  # Get "DD-MM"
                    if '-' in day_month:
                        day, month = day_month.split('-')
                        
                        # Create date string in standard format
                        date_string = f"{day}/{month}/{year}"
                        return datetime.strptime(date_string, '%d/%m/%Y').date()
        
        # Fallback: try other common formats
        formats = [
            '%d/%m/%Y',
            '%d-%m-%Y', 
            '%Y-%m-%d',
            '%d.%m.%Y'
        ]
        
        for fmt in formats:
            try:
                return datetime.strptime(date_str, fmt).date()
            except ValueError:
                continue
    
    except Exception as e:
        print(f"Error parsing date '{date_str}': {e}")
    
    return None


def find_closest_spond_event(match_date, spond_events, max_days_diff=3):
    """Find Spond event closest to match date."""
    from datetime import timedelta
    
    closest_event = None
    min_diff = timedelta(days=max_days_diff + 1)
    
    for event in spond_events:
        # Handle both dict format and DataFrame row format
        if isinstance(event, dict):
            timestamp_field = event.get('startTimestamp') or event.get('date')
        else:
            # DataFrame row - use .get() method
            timestamp_field = getattr(event, 'startTimestamp', None) or getattr(event, 'date', None)
            
        if timestamp_field:
            try:
                if isinstance(timestamp_field, str):
                    # Parse ISO format timestamp
                    event_date = datetime.fromisoformat(timestamp_field.replace('Z', '+00:00')).date()
                else:
                    event_date = timestamp_field
                
                diff = abs((match_date - event_date).days)
                if diff <= max_days_diff and diff < min_diff.days:
                    min_diff = timedelta(days=diff)
                    closest_event = event
            except (ValueError, AttributeError) as e:
                print(f"Error parsing event date {timestamp_field}: {e}")
                continue
    
    return closest_event


def calculate_player_match_winrates(matched_matches, spond_members=None):
    """Calculate win rates for each player based on actual matches."""
    
    # Create member ID to name mapping
    member_map = {}
    if spond_members:
        for member in spond_members:
            member_id = member.get('id')
            first_name = member.get('firstName', '')
            last_name = member.get('lastName', '')
            full_name = f"{first_name} {last_name}".strip()
            if member_id and full_name:
                member_map[member_id] = full_name
    
    player_stats = {}
    
    for match in matched_matches:
        attendee_ids = match.get('attendees', [])
        result = match['result']
        
        for attendee_id in attendee_ids:
            # Convert member ID to name
            if isinstance(attendee_id, str) and attendee_id in member_map:
                player_name = member_map[attendee_id]
            elif isinstance(attendee_id, dict):
                player_name = attendee_id.get('name', 'Unknown')
            else:
                player_name = f"Unknown ({attendee_id})"
            
            if player_name not in player_stats:
                player_stats[player_name] = {
                    'matches_played': 0,
                    'wins': 0,
                    'draws': 0,
                    'losses': 0,
                    'goals_for': 0,
                    'goals_against': 0,
                    'match_history': []
                }
            
            stats = player_stats[player_name]
            stats['matches_played'] += 1
            stats['goals_for'] += match['our_goals']
            stats['goals_against'] += match['opponent_goals']
            
            if result == 'W':
                stats['wins'] += 1
            elif result == 'D':
                stats['draws'] += 1
            elif result == 'L':
                stats['losses'] += 1
            
            stats['match_history'].append({
                'date': match['date'],
                'opponent': match['opponent'],
                'result': result,
                'score': f"{match['our_goals']}-{match['opponent_goals']}"
            })
    
    # Calculate win rates and additional metrics
    for player_name, stats in player_stats.items():
        if stats['matches_played'] > 0:
            stats['win_rate'] = stats['wins'] / stats['matches_played']
            stats['points_per_match'] = (stats['wins'] * 3 + stats['draws']) / stats['matches_played']
            stats['avg_goals_for'] = stats['goals_for'] / stats['matches_played']
            stats['avg_goals_against'] = stats['goals_against'] / stats['matches_played']
            stats['goal_difference'] = stats['goals_for'] - stats['goals_against']
        else:
            stats['win_rate'] = 0.0
            stats['points_per_match'] = 0.0
    
    return player_stats


# Test function to explore DBU structure
def explore_dbu_structure():
    """Explore DBU website structure to find match data."""
    base_url = 'https://www.dbu.dk/resultater/hold/460174_472317'
    headers = {'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36'}
    
    try:
        response = requests.get(base_url, headers=headers)
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Find all links that might lead to match history
        links = soup.find_all('a', href=True)
        match_links = []
        
        for link in links:
            href = link['href']
            text = link.get_text(strip=True).lower()
            
            if any(keyword in text for keyword in ['kamp', 'resultat', 'program', 'historie']):
                match_links.append({
                    'text': text,
                    'href': href,
                    'full_url': 'https://www.dbu.dk' + href if href.startswith('/') else href
                })
        
        return match_links
        
    except Exception as e:
        print(f"Error exploring DBU structure: {e}")
        return []