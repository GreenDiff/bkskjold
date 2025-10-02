#!/usr/bin/env python3
"""Test the match analysis functionality."""

import json
import pandas as pd
from utils.match_history_scraper import fetch_match_history, cross_reference_with_spond, calculate_player_match_winrates

def load_spond_data():
    """Load Spond data from local files."""
    try:
        # Load member data (it's a dict with member IDs as keys)
        with open('member_data.json', 'r', encoding='utf-8') as f:
            member_data = json.load(f)
        # Convert dict values to list for DataFrame
        members_list = list(member_data.values())
        members_df = pd.DataFrame(members_list)
        
        # Load training matches (it's a list of matches)
        try:
            with open('training_matches.json', 'r', encoding='utf-8') as f:
                events_list = json.load(f)
            events_df = pd.DataFrame(events_list)
        except FileNotFoundError:
            # Create empty events DataFrame if file doesn't exist
            events_df = pd.DataFrame()
        
        return events_df, members_df
    except Exception as e:
        print(f"Error loading Spond data: {e}")
        return pd.DataFrame(), pd.DataFrame()

def test_match_analysis():
    """Test the complete match analysis pipeline."""
    print("Testing match analysis functionality...")
    
    # Test DBU match scraping
    print("\n1. Fetching match history from DBU...")
    try:
        matches = fetch_match_history()
        print(f"Fetched {len(matches)} matches from DBU")
        
        # Show first few matches
        if matches:
            print("\nSample matches:")
            for i, match in enumerate(matches[:3]):
                print(f"Match {i+1}: {match}")
                print()
    except Exception as e:
        print(f"Error fetching matches: {e}")
        return
    
    # Test Spond data loading
    print("\n2. Loading Spond data...")
    try:
        events_df, members_df = load_spond_data()
        
        print(f"Loaded {len(events_df)} events and {len(members_df)} members from Spond")
        
        # Show event info
        if not events_df.empty:
            print("\nEvents sample:")
            print(events_df.head(2).to_string())
        
        # Show member info
        if not members_df.empty:
            print(f"\nMembers sample (showing first 3 names):")
            names = [m.get('firstName', '') + ' ' + m.get('lastName', '') for m in members_df.head(3).to_dict('records')]
            print(names)
            
    except Exception as e:
        print(f"Error loading Spond data: {e}")
        return
    
    # Test cross-referencing
    print("\n3. Cross-referencing matches with Spond events...")
    try:
        cross_referenced = cross_reference_with_spond(matches, events_df)
        print(f"Cross-referenced {len(cross_referenced)} matches")
        
        # Show sample cross-referenced matches
        if cross_referenced:
            print("\nSample cross-referenced matches:")
            for i, match in enumerate(cross_referenced[:2]):
                print(f"Match {i+1}:")
                print(f"  Date: {match.get('match_date')}")
                print(f"  Opponent: {match.get('opponent')}")
                print(f"  Result: {match.get('result')}")
                print(f"  Attendees: {len(match.get('attendees', []))}")
                print()
    except Exception as e:
        print(f"Error cross-referencing: {e}")
        return
    
    # Test win rate calculation
    print("\n4. Calculating player win rates...")
    try:
        winrates = calculate_player_match_winrates(cross_referenced)
        print(f"Calculated win rates for {len(winrates)} players")
        
        # Show top performers
        if winrates:
            sorted_players = sorted(winrates.items(), key=lambda x: x[1]['win_rate'], reverse=True)
            print("\nTop 5 performers:")
            for name, stats in sorted_players[:5]:
                print(f"  {name}: {stats['wins']}/{stats['total']} ({stats['win_rate']:.1%})")
    except Exception as e:
        print(f"Error calculating win rates: {e}")
        return
    
    print("\n✅ Match analysis test completed successfully!")

if __name__ == "__main__":
    test_match_analysis()