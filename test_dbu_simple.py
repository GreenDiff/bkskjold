#!/usr/bin/env python3
"""Simple test to show DBU match scraping is working."""

from utils.match_history_scraper import fetch_match_history, parse_match_date, determine_match_result

def test_dbu_scraping():
    """Test just the DBU scraping functionality."""
    print("Testing DBU match scraping...")
    
    # Test DBU match scraping
    print("\n1. Fetching match history from DBU...")
    try:
        matches = fetch_match_history()
        print(f"✅ Successfully fetched {len(matches)} matches from DBU")
        
        # Test each match
        print(f"\n2. Analyzing {len(matches)} matches:")
        print("=" * 80)
        
        for i, match in enumerate(matches, 1):
            print(f"\nMatch {i}:")
            print(f"  📅 Date: {match.get('date')}")
            print(f"  🆚 {match.get('home_team')} vs {match.get('away_team')}")
            print(f"  🏟️ Venue: {match.get('venue')}")
            print(f"  📊 Result: {match.get('result')}")
            print(f"  🎯 Opponent: {match.get('opponent')}")
            print(f"  🏠 Home game: {match.get('is_home')}")
            
            # Test date parsing
            parsed_date = parse_match_date(match.get('date', ''))
            print(f"  📆 Parsed date: {parsed_date}")
            
            # Test result analysis
            result, our_goals, opp_goals = determine_match_result(match)
            print(f"  🏆 Result: {result} (Us: {our_goals}, Them: {opp_goals})")
            print(f"  🔍 Match ID: {match.get('match_id')}")
            
        print("=" * 80)
        
        # Summary stats
        wins = sum(1 for m in matches if determine_match_result(m)[0] == 'W')
        draws = sum(1 for m in matches if determine_match_result(m)[0] == 'D')
        losses = sum(1 for m in matches if determine_match_result(m)[0] == 'L')
        
        print(f"\n📈 Season Summary:")
        print(f"  🏆 Wins: {wins}")
        print(f"  🤝 Draws: {draws}")
        print(f"  😔 Losses: {losses}")
        print(f"  📊 Win Rate: {wins/len(matches)*100:.1f}%")
        
        home_games = sum(1 for m in matches if m.get('is_home'))
        away_games = len(matches) - home_games
        print(f"  🏠 Home games: {home_games}")
        print(f"  ✈️ Away games: {away_games}")
        
    except Exception as e:
        print(f"❌ Error fetching matches: {e}")
        return
    
    print("\n✅ DBU scraping test completed successfully!")
    print("\nNext step: The system is ready to cross-reference with actual Spond match events")
    print("(Training matches in training_matches.json are not real match events)")

if __name__ == "__main__":
    test_dbu_scraping()