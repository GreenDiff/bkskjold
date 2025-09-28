"""Data loading utilities for Spond application."""

import json
import asyncio
from datetime import datetime
import streamlit as st
from spond_integration import sync_data, FinesCalculator, SpondIntegration


def sync_data_wrapper():
    """Sync data from Spond API."""
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        success, message = loop.run_until_complete(sync_data())
        if success:
            st.success(message)
            st.session_state.fines_calculator = FinesCalculator()  # Genindlæs data
        else:
            st.error(message)
    finally:
        loop.close()


def load_member_data():
    """Load member data from JSON file."""
    try:
        with open('member_data.json', 'r', encoding='utf-8') as f:
            return json.load(f)
    except FileNotFoundError:
        return {}


def initialize_fines_calculator():
    """Initialize the fines calculator in session state."""
    if 'fines_calculator' not in st.session_state:
        st.session_state.fines_calculator = FinesCalculator()


def get_training_accepted_players():
    """Get list of players who accepted the next training session."""
    @st.cache_data(ttl=300, show_spinner="Henter spillere der har accepteret næste træning...")  # Cache for 5 minutes
    def _fetch_accepted_players():
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            spond_integration = SpondIntegration()
            accepted_players = loop.run_until_complete(spond_integration.get_next_training_accepted_players())
            loop.run_until_complete(spond_integration.close())
            return accepted_players
        except Exception as e:
            print(f"Error fetching accepted players: {e}")
            return []
        finally:
            loop.close()
    
    return _fetch_accepted_players()