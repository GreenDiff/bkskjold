import json
import os
from datetime import datetime, timedelta
from typing import Dict, List, Optional
import asyncio
import ssl
import aiohttp
from spond import spond
import app_config


class SpondIntegration:
    """Wrapper for Spond API to fetch team data and calculate fines."""
    
    def __init__(self):
        self.session = None
        self.groups = None
        self.events = None
    
    async def initialize(self):
        """Initialize the Spond session."""
        # Create SSL context that works on macOS
        ssl_context = ssl.create_default_context()
        # Note: In production, you should use proper SSL verification
        # This is a workaround for local development SSL issues
        ssl_context.check_hostname = False
        ssl_context.verify_mode = ssl.CERT_NONE
        
        # Create a connector with the SSL context
        connector = aiohttp.TCPConnector(ssl=ssl_context)
        
        self.session = spond.Spond(
            username=app_config.SPOND_USERNAME,
            password=app_config.SPOND_PASSWORD
        )
        
        # Replace the session's client with our SSL-fixed one
        if self.session.clientsession:
            await self.session.clientsession.close()
        
        self.session.clientsession = aiohttp.ClientSession(
            cookie_jar=aiohttp.CookieJar(),
            connector=connector
        )
        
    async def close(self):
        """Close the Spond session."""
        if self.session and self.session.clientsession:
            await self.session.clientsession.close()
    
    async def get_team_events(self, days_back: int = 30) -> List[Dict]:
        """Fetch team events from the last specified days."""
        if not self.session:
            await self.initialize()
            
        # Calculate date range
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days_back)
        
        try:
            events = await self.session.get_events(
                group_id=app_config.GROUP_ID,
                min_start=start_date,
                max_start=end_date,
                max_events=200
            )
            return events or []
        except Exception as e:
            print(f"Error fetching events: {e}")
            return []
    
    async def get_team_members(self) -> List[Dict]:
        """Fetch team members."""
        if not self.session:
            await self.initialize()
            
        try:
            groups = await self.session.get_groups()
            for group in groups:
                if group['id'] == app_config.GROUP_ID:
                    return group.get('members', [])
            return []
        except Exception as e:
            print(f"Error fetching members: {e}")
            return []
    
    async def get_future_events(self, days_ahead: int = 7) -> List[Dict]:
        """Fetch future team events."""
        if not self.session:
            await self.initialize()
            
        # Calculate date range for future events
        start_date = datetime.now()
        end_date = start_date + timedelta(days=days_ahead)
        
        try:
            events = await self.session.get_events(
                group_id=app_config.GROUP_ID,
                min_start=start_date,
                max_start=end_date,
                max_events=50
            )
            return events or []
        except Exception as e:
            print(f"Error fetching future events: {e}")
            return []
    
    async def get_next_training_accepted_players(self) -> List[str]:
        """Get list of player names who have accepted the next training session."""
        if not self.session:
            await self.initialize()
            
        try:
            # Get future events
            future_events = await self.get_future_events(days_ahead=7)
            
            # Get team members to map IDs to names
            members = await self.get_team_members()
            member_map = {member['id']: f"{member.get('firstName', '')} {member.get('lastName', '')}".strip() 
                         for member in members}
            
            # Find the next training session (look for "træning" or "training" in event name)
            next_training = None
            for event in sorted(future_events, key=lambda x: x.get('startTimestamp', '')):
                event_name = event.get('heading', '').lower()
                if 'træning' in event_name or 'training' in event_name:
                    next_training = event
                    break
            
            if not next_training:
                print("No upcoming training session found")
                return []
            
            print(f"Found next training: {next_training.get('heading', 'Unknown')} at {next_training.get('startTimestamp', 'Unknown time')}")
            
            # Get accepted players from the training event
            responses = next_training.get('responses', {})
            accepted_ids = responses.get('acceptedIds', [])
            
            # Convert IDs to names
            accepted_players = []
            for player_id in accepted_ids:
                player_name = member_map.get(player_id, f"Unknown ({player_id})")
                if player_name and player_name != f"Unknown ({player_id})":
                    accepted_players.append(player_name)
            
            print(f"Found {len(accepted_players)} players who accepted the training")
            return accepted_players
            
        except Exception as e:
            print(f"Error fetching training accepted players: {e}")
            return []
    
    async def get_next_training_event(self):
        """Get the next training event details."""
        if not self.session:
            await self.initialize()
            
        try:
            # Get future events
            future_events = await self.get_future_events(days_ahead=7)
            
            # Find the next training session (look for "træning" or "training" in event name)
            next_training = None
            for event in sorted(future_events, key=lambda x: x.get('startTimestamp', '')):
                event_name = event.get('heading', '').lower()
                if 'træning' in event_name or 'training' in event_name:
                    next_training = event
                    break
            
            return next_training
            
        except Exception as e:
            print(f"Error fetching next training event: {e}")
            return None


class FinesCalculator:
    """Calculate fines based on attendance and response times."""
    
    def __init__(self):
        self.load_fines_data()
    
    def load_fines_data(self):
        """Load existing fines data from file."""
        if os.path.exists(app_config.DATABASE_FILE):
            try:
                with open(app_config.DATABASE_FILE, 'r') as f:
                    self.fines_data = json.load(f)
            except (json.JSONDecodeError, FileNotFoundError):
                self.fines_data = {}
        else:
            self.fines_data = {}
    
    def save_fines_data(self):
        """Save fines data to file."""
        with open(app_config.DATABASE_FILE, 'w') as f:
            json.dump(self.fines_data, f, indent=2, default=str)
    
    def calculate_event_fines(self, event: Dict, members: List[Dict]) -> Dict[str, Dict]:
        """Calculate fines for a specific event."""
        event_id = event['id']
        event_heading = event.get('heading', 'Unknown Event')
        event_start = event.get('startTimestamp', '')
        event_created = event.get('createdTime', event_start)
        
        # Determine if it's a match or training based on event name
        is_match = any(keyword in event_heading.lower() 
                      for keyword in ['match', 'kamp', 'spill', 'game'])
        
        fine_amount = app_config.FINE_MISSING_MATCH if is_match else app_config.FINE_MISSING_TRAINING
        
        responses = event.get('responses', {})
        declined_ids = set(responses.get('declinedIds', []))
        unanswered_ids = set(responses.get('unansweredIds', []))
        accepted_ids = set(responses.get('acceptedIds', []))
        
        # Create member ID to name mapping
        member_map = {member['id']: f"{member.get('firstName', '')} {member.get('lastName', '')}" 
                     for member in members}
        
        event_fines = {}
        
        # Calculate fines for missing players (declined or unanswered)
        missing_players = declined_ids.union(unanswered_ids)
        
        for player_id in missing_players:
            player_name = member_map.get(player_id, f"Unknown ({player_id})")
            
            fine_info = {
                'player_id': player_id,
                'player_name': player_name,
                'event_id': event_id,
                'event_name': event_heading,
                'event_date': event_start,
                'fine_type': 'missing_event',
                'fine_amount': fine_amount,
                'paid': False,
                'created_date': datetime.now().isoformat()
            }
            
            event_fines[player_id] = fine_info
        
        # Check for no response within 24 hours of event
        self._check_no_response_fines(event, members, event_fines)
        
        return event_fines
    
    def _check_no_response_fines(self, event: Dict, members: List[Dict], event_fines: Dict):
        """Check for players with no response when less than 24 hours until event."""
        event_start = event.get('startTimestamp')
        if not event_start:
            return
            
        # Parse event start time
        event_time = datetime.fromisoformat(event_start.replace('Z', '+00:00'))
        current_time = datetime.now(event_time.tzinfo)
        
        # Calculate hours until event
        time_until_event = (event_time - current_time).total_seconds() / 3600
        
        # Only check if event is within 24 hours
        if time_until_event > 24 or time_until_event < 0:  # Future events or past events
            return
            
        event_id = event['id']
        event_heading = event.get('heading', 'Unknown Event')
        responses = event.get('responses', {})
        
        # Check each member for no response
        for member in members:
            member_id = member['id']
            member_name = f"{member.get('firstName', '')} {member.get('lastName', '')}".strip()
            
            # Skip if player already has a fine for this event
            if member_id in event_fines:
                continue
                
            # Check if player has responded
            player_response = responses.get('acceptedIds', []) + responses.get('declinedIds', []) + responses.get('unansweredIds', [])
            
            # If player hasn't responded and event is within 24 hours, add fine
            if member_id in responses.get('unansweredIds', []):
                fine_key = f"{event_id}_{member_id}_no_response"
                
                fine_info = {
                    'player_id': member_id,
                    'player_name': member_name,
                    'event_id': event_id,
                    'event_name': event_heading,
                    'event_date': event_start,
                    'fine_type': 'no_response_24h',
                    'fine_amount': app_config.LATE_RESPONSE_FINE,  # Use late response fine amount
                    'paid': False,
                    'created_date': datetime.now().isoformat()
                }
                
                event_fines[member_id] = fine_info
    
    def update_fines_for_events(self, events: List[Dict], members: List[Dict]):
        """Update fines data for all events."""
        # Parse cutoff date from config
        cutoff_date = datetime.strptime(app_config.FINES_CUTOFF_DATE, '%Y-%m-%d')
        
        for event in events:
            # Check if event is after cutoff date
            event_start = event.get('startTimestamp', '')
            if event_start:
                try:
                    event_date = datetime.fromisoformat(event_start.replace('Z', '+00:00'))
                    # Only process events on or after cutoff date
                    if event_date.date() < cutoff_date.date():
                        continue  # Skip this event - it's before our cutoff date
                except (ValueError, TypeError):
                    print(f"Warning: Could not parse event date '{event_start}' for event {event.get('id')}")
                    continue  # Skip events with invalid dates
            else:
                continue  # Skip events without start timestamp
            
            event_id = event['id']
            event_fines = self.calculate_event_fines(event, members)
            
            # Only add new fines (don't overwrite existing ones)
            for player_id, fine_info in event_fines.items():
                fine_key = f"{event_id}_{player_id}"
                if fine_key not in self.fines_data:
                    self.fines_data[fine_key] = fine_info
        
        self.save_fines_data()
    
    def get_player_fines(self, player_id: str = None) -> List[Dict]:
        """Get fines for a specific player or all players."""
        if player_id:
            return [fine for fine in self.fines_data.values() 
                   if fine['player_id'] == player_id]
        return list(self.fines_data.values())
    
    def get_fines_summary(self) -> Dict:
        """Get summary of all fines."""
        all_fines = list(self.fines_data.values())
        
        total_fines = len(all_fines)
        total_amount = sum(fine['fine_amount'] for fine in all_fines)
        paid_fines = sum(1 for fine in all_fines if fine['paid'])
        unpaid_amount = sum(fine['fine_amount'] for fine in all_fines if not fine['paid'])
        
        # Group by player
        player_totals = {}
        for fine in all_fines:
            player_name = fine['player_name']
            if player_name not in player_totals:
                player_totals[player_name] = {
                    'total_fines': 0,
                    'total_amount': 0,
                    'unpaid_amount': 0,
                    'paid_fines': 0
                }
            
            player_totals[player_name]['total_fines'] += 1
            player_totals[player_name]['total_amount'] += fine['fine_amount']
            
            if fine['paid']:
                player_totals[player_name]['paid_fines'] += 1
            else:
                player_totals[player_name]['unpaid_amount'] += fine['fine_amount']
        
        return {
            'total_fines': total_fines,
            'total_amount': total_amount,
            'paid_fines': paid_fines,
            'unpaid_amount': unpaid_amount,
            'player_totals': player_totals
        }
    
    def mark_fine_paid(self, fine_key: str):
        """Mark a fine as paid."""
        if fine_key in self.fines_data:
            self.fines_data[fine_key]['paid'] = True
            self.fines_data[fine_key]['paid_date'] = datetime.now().isoformat()
            self.save_fines_data()
    
    def remove_fine(self, fine_key: str):
        """Remove a fine."""
        if fine_key in self.fines_data:
            del self.fines_data[fine_key]
            self.save_fines_data()
    
    @property
    def processed_fines_data(self) -> Dict[str, Dict]:
        """Get fines data processed by player name with summary information."""
        processed = {}
        
        # Group raw fines by player name
        for fine in self.fines_data.values():
            player_name = fine['player_name']
            
            if player_name not in processed:
                processed[player_name] = {
                    'total_fine': 0,
                    'unpaid_amount': 0,
                    'no_show_count': 0,
                    'late_response_count': 0,
                    'training_loss_count': 0,
                    'events': []
                }
            
            # Add to totals
            processed[player_name]['total_fine'] += fine['fine_amount']
            
            # Track unpaid amount
            if not fine['paid']:
                processed[player_name]['unpaid_amount'] += fine['fine_amount']
            
            # Count fine types
            fine_type = fine.get('fine_type', 'missing_event')
            if fine_type == 'no_response_24h':
                processed[player_name]['late_response_count'] += 1
            elif fine_type == 'training_loss':
                if 'training_loss_count' not in processed[player_name]:
                    processed[player_name]['training_loss_count'] = 0
                processed[player_name]['training_loss_count'] += 1
            else:
                processed[player_name]['no_show_count'] += 1
            
            # Add event details
            processed[player_name]['events'].append({
                'startTimestamp': fine['event_date'],
                'heading': fine.get('event_name', 'Unknown Event'),
                'fine_reason': fine.get('fine_type', 'missing_event'),
                'fine_amount': fine['fine_amount']
            })
        
        return processed


async def sync_data():
    """Synchronize data with Spond API."""
    spond_integration = SpondIntegration()
    fines_calculator = FinesCalculator()
    
    try:
        # Fetch recent events and members
        events = await spond_integration.get_team_events(days_back=60)
        members = await spond_integration.get_team_members()
        
        # Store member data with profile pictures
        member_data = {}
        for member in members:
            member_id = member['id']
            profile_pic_url = None
            
            # Get profile picture URL - check both possible locations
            if 'profile' in member and 'imageUrl' in member['profile']:
                profile_pic_url = member['profile']['imageUrl']
            elif 'imageUrl' in member:
                profile_pic_url = member['imageUrl']
            
            # Remove URL parameters that might cause issues
            if profile_pic_url and '?' in profile_pic_url:
                profile_pic_url = profile_pic_url.split('?')[0]
            
            member_data[member_id] = {
                'id': member_id,
                'firstName': member.get('firstName', ''),
                'lastName': member.get('lastName', ''),
                'name': f"{member.get('firstName', '')} {member.get('lastName', '')}",
                'profilePicture': profile_pic_url
            }
        
        # Save member data
        with open('member_data.json', 'w') as f:
            json.dump(member_data, f, indent=2, default=str)
        
        # Update fines based on events
        fines_calculator.update_fines_for_events(events, members)
        
        return True, f"Synced {len(events)} events and {len(members)} members"
    
    except Exception as e:
        return False, f"Error syncing data: {str(e)}"
    
    finally:
        await spond_integration.close()


if __name__ == "__main__":
    # Test the integration
    async def test():
        success, message = await sync_data()
        print(f"Sync result: {success} - {message}")
    
    asyncio.run(test())