"""
BK Skjolds Bødekasse - Main Application Entry Point

A modular Streamlit application for managing team fines and payments
using the Spond API integration.
"""

import streamlit as st
from utils.data_loader import initialize_fines_calculator
from views.dashboard import display_dashboard
from views.detailed_fines import display_detailed_fines  
from views.admin_panel import display_admin_panel
from views.team_selector import display_team_selector
from views.training_history import display_training_history
from views.tournament import display_tournament
from views.match_analysis import display_match_analysis

# Configure Streamlit page
st.set_page_config(
    page_title="BK Skjolds",
    page_icon="⚽",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Initialize the fines calculator
initialize_fines_calculator()


def main():
    """Main application entry point with navigation."""
    
    # Sidebar navigation
    st.sidebar.title("Navigation")
    page = st.sidebar.radio(
        "Vælg en side:",
        ["Dashboard", "Bødeoversigt", "Hold Udvælger", "Træningshistorik", "Turnering", "Kampanalyse", "Admin Panel"]
    )
    
    # Display selected page
    if page == "Dashboard":
        display_dashboard()
    elif page == "Bødeoversigt":
        display_detailed_fines()
    elif page == "Hold Udvælger":
        display_team_selector()
    elif page == "Træningshistorik":
        display_training_history()
    elif page == "Turnering":
        display_tournament()
    elif page == "Kampanalyse":
        display_match_analysis()
    elif page == "Admin Panel":
        display_admin_panel()
    
    # Footer
    st.sidebar.markdown("---")



if __name__ == "__main__":
    main()