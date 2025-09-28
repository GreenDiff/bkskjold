"""
Intelligent Team Generator
=========================

Smart team balancing algorithm that uses historical win rate data to create 
equally balanced teams based on player performance statistics.
"""

import json
import os
from typing import List, Dict, Tuple, Optional
from datetime import datetime
import random
from itertools import combinations


class IntelligentTeamGenerator:
    """
    Smart team generator that analyzes player win rates and creates balanced teams.
    """
    
    def __init__(self, training_matches_file: str = "training_matches.json"):
        """
        Initialize the intelligent team generator.
        
        Args:
            training_matches_file: Path to the training matches JSON file
        """
        self.training_matches_file = training_matches_file
        self.player_stats = {}
        self.default_win_rate = 0.5  # Neutral win rate for new players
        
    def load_training_history(self) -> List[Dict]:
        """Load training match history from JSON file."""
        if not os.path.exists(self.training_matches_file):
            return []
            
        try:
            with open(self.training_matches_file, 'r', encoding='utf-8') as f:
                matches = json.load(f)
                # Only return completed matches
                return [match for match in matches if match.get('status') == 'completed']
        except Exception as e:
            print(f"Error loading training history: {e}")
            return []
    
    def calculate_player_statistics(self) -> Dict[str, Dict]:
        """
        Calculate win rate statistics for each player based on training history.
        
        Returns:
            Dictionary with player names as keys and stats as values:
            {
                'player_name': {
                    'wins': int,
                    'losses': int, 
                    'matches': int,
                    'win_rate': float
                }
            }
        """
        matches = self.load_training_history()
        player_stats = {}
        
        for match in matches:
            winning_team = match.get('winning_team')
            if not winning_team:
                continue
                
            team1 = match.get('team1', [])
            team2 = match.get('team2', [])
            
            # Determine winners and losers
            winning_players = team1 if winning_team == 1 else team2
            losing_players = team2 if winning_team == 1 else team1
            
            # Update winner stats
            for player in winning_players:
                if player not in player_stats:
                    player_stats[player] = {'wins': 0, 'losses': 0, 'matches': 0, 'win_rate': 0.0}
                player_stats[player]['wins'] += 1
                player_stats[player]['matches'] += 1
            
            # Update loser stats
            for player in losing_players:
                if player not in player_stats:
                    player_stats[player] = {'wins': 0, 'losses': 0, 'matches': 0, 'win_rate': 0.0}
                player_stats[player]['losses'] += 1
                player_stats[player]['matches'] += 1
        
        # Calculate win rates
        for player in player_stats:
            matches = player_stats[player]['matches']
            if matches > 0:
                player_stats[player]['win_rate'] = player_stats[player]['wins'] / matches
            else:
                player_stats[player]['win_rate'] = self.default_win_rate
        
        self.player_stats = player_stats
        return player_stats
    
    def get_player_win_rate(self, player: str) -> float:
        """
        Get win rate for a specific player.
        
        Args:
            player: Player name
            
        Returns:
            Win rate (0.0 to 1.0), default_win_rate if no history
        """
        if not self.player_stats:
            self.calculate_player_statistics()
            
        return self.player_stats.get(player, {}).get('win_rate', self.default_win_rate)
    
    def calculate_team_strength(self, team: List[str]) -> float:
        """
        Calculate the overall strength of a team based on average win rate.
        
        Args:
            team: List of player names
            
        Returns:
            Average win rate of the team (0.0 to 1.0)
        """
        if not team:
            return 0.0
            
        total_win_rate = sum(self.get_player_win_rate(player) for player in team)
        return total_win_rate / len(team)
    
    def generate_balanced_teams_greedy(self, players: List[str]) -> Tuple[List[str], List[str]]:
        """
        Generate balanced teams using a greedy algorithm.
        
        This algorithm sorts players by win rate and alternately assigns them
        to teams, ensuring equal team sizes while trying to balance overall strength.
        
        Args:
            players: List of all available players
            
        Returns:
            Tuple of (team1, team2) with equal sizes (or team1 has 1 extra if odd number)
        """
        if len(players) < 2:
            return players[:1], players[1:]
        
        # Calculate player statistics if not already done
        if not self.player_stats:
            self.calculate_player_statistics()
        
        # Calculate team sizes - ensure equal sizes
        num_players = len(players)
        team_size = num_players // 2
        
        # Sort players by win rate and add some randomness
        players_with_rates = [(player, self.get_player_win_rate(player)) for player in players]
        
        # Group players by similar skill levels for better distribution
        players_with_rates.sort(key=lambda x: x[1], reverse=True)
        
        # Add randomness by shuffling within skill groups
        import random
        random.shuffle(players_with_rates)  # Add complete randomness first
        
        team1, team2 = [], []
        
        # Alternate assignment with balance checking
        for i, (player, win_rate) in enumerate(players_with_rates):
            # Stop adding to teams when they reach target size
            if len(team1) >= team_size and len(team2) >= team_size:
                break
                
            # If team1 is full, add to team2
            if len(team1) >= team_size:
                team2.append(player)
            # If team2 is full, add to team1  
            elif len(team2) >= team_size:
                team1.append(player)
            # Both teams have space - check balance and assign
            else:
                team1_strength = self.calculate_team_strength(team1 + [player])
                team2_strength = self.calculate_team_strength(team2 + [player])
                current_team1_strength = self.calculate_team_strength(team1)
                current_team2_strength = self.calculate_team_strength(team2)
                
                # Add to team that would create better balance
                team1_diff = abs(team1_strength - current_team2_strength)
                team2_diff = abs(team2_strength - current_team1_strength)
                
                if team1_diff <= team2_diff:
                    team1.append(player)
                else:
                    team2.append(player)
        
        return team1, team2
    
    def generate_balanced_teams_optimal(self, players: List[str], max_iterations: int = 1000) -> Tuple[List[str], List[str]]:
        """
        Generate balanced teams using a more sophisticated algorithm.
        
        This tries multiple random combinations and picks the most balanced one.
        
        Args:
            players: List of all available players
            max_iterations: Maximum number of combinations to try
            
        Returns:
            Tuple of (team1, team2) with minimal strength difference
        """
        if len(players) < 2:
            return players[:1], players[1:]
        
        # Calculate player statistics if not already done
        if not self.player_stats:
            self.calculate_player_statistics()
        
        num_players = len(players)
        team_size = num_players // 2
        
        # If we have many players, use random sampling approach
        if num_players > 16:
            return self.generate_balanced_teams_greedy(players)
        
        best_team1, best_team2 = [], []
        best_difference = float('inf')
        
        # Use random sampling for better performance and variety
        import random
        from itertools import combinations
        
        # Generate random combinations instead of systematic ones
        all_combinations = list(combinations(range(num_players), team_size))
        random.shuffle(all_combinations)  # Add randomness to combination order
        
        iterations = 0
        max_combinations = min(max_iterations, len(all_combinations))
        
        for team1_indices in all_combinations[:max_combinations]:
            team1 = [players[i] for i in team1_indices]
            team2 = [players[i] for i in range(num_players) if i not in team1_indices]
            
            strength1 = self.calculate_team_strength(team1)
            strength2 = self.calculate_team_strength(team2)
            
            difference = abs(strength1 - strength2)
            
            if difference < best_difference:
                best_difference = difference
                best_team1, best_team2 = team1.copy(), team2.copy()
            
            iterations += 1
            
            # Early exit if we find a very good balance
            if difference < 0.05:  # Less than 5% difference
                break
        
        # If no combinations were tried, fall back to greedy
        if not best_team1 and not best_team2:
            return self.generate_balanced_teams_greedy(players)
        
        return best_team1, best_team2
    
    def get_team_balance_info(self, team1: List[str], team2: List[str]) -> Dict:
        """
        Get detailed information about team balance.
        
        Args:
            team1: First team players
            team2: Second team players
            
        Returns:
            Dictionary with balance information
        """
        strength1 = self.calculate_team_strength(team1)
        strength2 = self.calculate_team_strength(team2)
        
        return {
            'team1_strength': strength1,
            'team2_strength': strength2, 
            'strength_difference': abs(strength1 - strength2),
            'balance_percentage': (1 - abs(strength1 - strength2)) * 100,
            'team1_players_stats': [(player, self.get_player_win_rate(player)) for player in team1],
            'team2_players_stats': [(player, self.get_player_win_rate(player)) for player in team2]
        }
    
    def generate_smart_teams(self, players: List[str], algorithm: str = "optimal") -> Tuple[List[str], List[str], Dict]:
        """
        Main function to generate smart, balanced teams.
        
        Args:
            players: List of all available players
            algorithm: "greedy" or "optimal"
            
        Returns:
            Tuple of (team1, team2, balance_info)
        """
        if algorithm == "greedy":
            team1, team2 = self.generate_balanced_teams_greedy(players)
        else:
            team1, team2 = self.generate_balanced_teams_optimal(players)
        
        balance_info = self.get_team_balance_info(team1, team2)
        
        return team1, team2, balance_info


def main():
    """Example usage and testing."""
    generator = IntelligentTeamGenerator()
    
    # Test with some example players
    test_players = ["Alice", "Bob", "Charlie", "David", "Eve", "Frank", "Grace", "Henry"]
    
    print("🤖 Intelligent Team Generator Test")
    print("=" * 40)
    
    # Calculate statistics
    stats = generator.calculate_player_statistics()
    print(f"📊 Player Statistics (from {len(generator.load_training_history())} matches):")
    for player, data in stats.items():
        print(f"  {player}: {data['wins']}W/{data['losses']}L ({data['win_rate']:.1%})")
    
    if not stats:
        print("  No historical data found - using default win rates")
    
    print("\n🔀 Generating Balanced Teams...")
    
    # Generate teams using both algorithms
    for algorithm in ["greedy", "optimal"]:
        print(f"\n--- {algorithm.title()} Algorithm ---")
        team1, team2, balance_info = generator.generate_smart_teams(test_players, algorithm)
        
        print(f"⚪ Hold 1: {', '.join(team1)}")
        print(f"   Styrke: {balance_info['team1_strength']:.1%}")
        
        print(f"⚫ Hold 2: {', '.join(team2)}")
        print(f"   Styrke: {balance_info['team2_strength']:.1%}")
        
        print(f"⚖️  Balance: {balance_info['balance_percentage']:.1f}%")
        print(f"📊 Forskel: {balance_info['strength_difference']:.1%}")


if __name__ == "__main__":
    main()