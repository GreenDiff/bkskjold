"""Admin panel page for Spond application."""

import streamlit as st
import app_config
from components.auth import check_admin_login, admin_login, admin_logout
from utils.data_loader import sync_data_wrapper, FinesCalculator


def display_admin_panel():
    """Display admin panel for configuration."""
    # Check if admin is logged in
    if not check_admin_login():
        admin_login()
        return
    
    # Show logout button in sidebar
    admin_logout()
    
    st.title("⚙️ Admin Panel")
    
    # Create tabs for different admin functions
    tab1, tab2, tab3 = st.tabs(["⚙️ Konfiguration", "💰 Bødestyring", "🔧 Datastyring"])
    
    with tab1:
        display_configuration_tab()
    
    with tab2:
        display_fine_management_tab()
    
    with tab3:
        display_data_management_tab()


def display_configuration_tab():
    """Display the configuration tab."""
    st.subheader("Systemkonfiguration")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.info(f"**Gruppe ID:** {app_config.GROUP_ID}")
        st.info(f"**Brugernavn:** {app_config.SPOND_USERNAME}")
        st.info(f"**Sent Svar Timer:** {app_config.LATE_RESPONSE_HOURS}t")
    
    with col2:
        st.subheader("Bødebeløb")
        
        # Editable fine amounts
        with st.form("fine_config_form"):
            new_training_fine = st.number_input(
                "Trænings/Udeblivelses Bøde (kr)", 
                value=app_config.FINE_MISSING_TRAINING,
                min_value=0,
                step=25
            )
            new_match_fine = st.number_input(
                "Kamp Bøde (kr)", 
                value=app_config.FINE_MISSING_MATCH,
                min_value=0,
                step=25
            )
            new_late_fine = st.number_input(
                "Sent Svar Bøde (kr)", 
                value=app_config.FINE_LATE_RESPONSE,
                min_value=0,
                step=5
            )
            
            if st.form_submit_button("💾 Opdater Bødebeløb"):
                update_fine_amounts(new_training_fine, new_match_fine, new_late_fine)


def update_fine_amounts(new_training_fine, new_match_fine, new_late_fine):
    """Update fine amounts in config file."""
    try:
        # Read current config
        with open('app_config.py', 'r') as f:
            config_content = f.read()
        
        # Update values
        config_content = config_content.replace(
            f"FINE_MISSING_TRAINING = {app_config.FINE_MISSING_TRAINING}",
            f"FINE_MISSING_TRAINING = {new_training_fine}"
        )
        config_content = config_content.replace(
            f"FINE_MISSING_MATCH = {app_config.FINE_MISSING_MATCH}",
            f"FINE_MISSING_MATCH = {new_match_fine}"
        )
        config_content = config_content.replace(
            f"FINE_LATE_RESPONSE = {app_config.FINE_LATE_RESPONSE}",
            f"FINE_LATE_RESPONSE = {new_late_fine}"
        )
        
        # Write back to file
        with open('app_config.py', 'w') as f:
            f.write(config_content)
        
        st.success("Bødebeløb opdateret! Genstart appen for at anvende ændringer.")
    except Exception as e:
        st.error(f"Fejl ved opdatering af konfiguration: {e}")


def display_fine_management_tab():
    """Display the fine management tab."""
    st.subheader("Individuel Bødestyring")
    
    # Get all fines from the calculator
    fines_calculator = st.session_state.fines_calculator
    all_fines = fines_calculator.get_player_fines()
    
    if all_fines:
        # Group fines by player for easier management
        fines_by_player = {}
        for fine in all_fines:
            player_name = fine['player_name']
            if player_name not in fines_by_player:
                fines_by_player[player_name] = []
            fines_by_player[player_name].append(fine)
        
        # Management mode selection
        management_mode = st.radio(
            "Styringsmåde:",
            ["👤 Individuel Spiller", "📋 Alle Spillere Oversigt"],
            horizontal=True
        )
        
        if management_mode == "👤 Individuel Spiller":
            display_individual_player_management(fines_by_player, fines_calculator)
        else:
            display_all_players_overview(all_fines, fines_by_player, fines_calculator)
    else:
        st.info("Ingen bøder fundet. Synkronisér data først for at se bøder.")


def display_individual_player_management(fines_by_player, fines_calculator):
    """Display individual player management interface."""
    # Player selection
    selected_player = st.selectbox(
        "Vælg Spiller:", 
        options=list(fines_by_player.keys()),
        help="Vælg en spiller for at administrere deres bøder"
    )
    
    if selected_player:
        player_fines = fines_by_player[selected_player]
        
        st.subheader(f"Bøder for {selected_player}")
        
        # Show player summary
        total_amount = sum(fine['fine_amount'] for fine in player_fines)
        paid_amount = sum(fine['fine_amount'] for fine in player_fines if fine.get('paid', False))
        unpaid_amount = total_amount - paid_amount
        
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Samlet Bøder", f"{total_amount} kr")
        with col2:
            st.metric("Betalt", f"{paid_amount} kr", delta=None if paid_amount == 0 else "✅")
        with col3:
            st.metric("Ubetalt", f"{unpaid_amount} kr", delta=None if unpaid_amount == 0 else "❌")
    
        # Create a table with all fines for easy management
        st.subheader("Hurtige Handlinger")
        
        # Bulk actions
        display_bulk_actions(player_fines, fines_calculator)
        
        st.subheader("Individuelle Bøder")
        
        # Table format with immediate checkboxes
        display_individual_fines_table(player_fines, fines_calculator)


def display_bulk_actions(player_fines, fines_calculator):
    """Display bulk action buttons for a player."""
    col1, col2, col3 = st.columns(3)
    with col1:
        if st.button("💳 Markér Alle som Betalt", use_container_width=True):
            for fine in player_fines:
                fine_key = list(fines_calculator.fines_data.keys())[
                    list(fines_calculator.fines_data.values()).index(fine)
                ]
                if not fine.get('paid', False):
                    fines_calculator.mark_fine_paid(fine_key)
            st.success("Alle bøder markeret som betalt!")
            st.rerun()
    
    with col2:
        if st.button("🔄 Markér Alle som Ubetalt", use_container_width=True):
            for fine in player_fines:
                fine_key = list(fines_calculator.fines_data.keys())[
                    list(fines_calculator.fines_data.values()).index(fine)
                ]
                if fine.get('paid', False):
                    fines_calculator.fines_data[fine_key]['paid'] = False
                    if 'paid_date' in fines_calculator.fines_data[fine_key]:
                        del fines_calculator.fines_data[fine_key]['paid_date']
            fines_calculator.save_fines_data()
            st.success("Alle bøder markeret som ubetalt!")
            st.rerun()
    
    with col3:
        if st.button("💾 Gem Ændringer", use_container_width=True):
            fines_calculator.save_fines_data()
            st.success("Ændringer gemt!")


def display_individual_fines_table(player_fines, fines_calculator):
    """Display individual fines in a table format."""
    for i, fine in enumerate(player_fines):
        fine_key = list(fines_calculator.fines_data.keys())[
            list(fines_calculator.fines_data.values()).index(fine)
        ]
        
        # Create a container for each fine row
        with st.container():
            col1, col2, col3, col4, col5 = st.columns([3, 2, 1, 1, 1])
            
            with col1:
                st.write(f"**{fine['event_name']}**")
                st.caption(f"{fine['event_date'][:10]} • {fine['fine_type']}")
            
            with col2:
                # Editable amount
                new_amount = st.number_input(
                    "Beløb (kr)",
                    value=fine['fine_amount'],
                    min_value=0,
                    step=25,
                    key=f"amount_{fine_key}",
                    label_visibility="collapsed"
                )
                
                # Auto-update amount when changed
                if new_amount != fine['fine_amount']:
                    fines_calculator.fines_data[fine_key]['fine_amount'] = new_amount
                    fines_calculator.save_fines_data()
            
            with col3:
                # Paid checkbox - immediate toggle
                is_paid = fine.get('paid', False)
                paid_checkbox = st.checkbox(
                    "Betalt",
                    value=is_paid,
                    key=f"paid_{fine_key}"
                )
                
                # Auto-update payment status when changed
                if paid_checkbox != is_paid:
                    if paid_checkbox:
                        fines_calculator.mark_fine_paid(fine_key)
                    else:
                        fines_calculator.fines_data[fine_key]['paid'] = False
                        if 'paid_date' in fines_calculator.fines_data[fine_key]:
                            del fines_calculator.fines_data[fine_key]['paid_date']
                        fines_calculator.save_fines_data()
                    st.rerun()
            
            with col4:
                # Payment status indicator
                if fine.get('paid', False):
                    st.success("✅")
                else:
                    st.error("❌")
            
            with col5:
                # Delete fine option
                if st.button("🗑️", key=f"delete_{fine_key}", help="Slet denne bøde"):
                    fines_calculator.remove_fine(fine_key)
                    st.success("Bøde slettet!")
                    st.rerun()
            
            # Show payment date if paid
            if fine.get('paid', False) and fine.get('paid_date'):
                st.caption(f"💳 Betalt: {fine.get('paid_date')[:19].replace('T', ' ')}")
            
            st.divider()


def display_all_players_overview(all_fines, fines_by_player, fines_calculator):
    """Display all players overview mode."""
    st.subheader("Alle Spillere - Hurtig Betalingsstyring")
    
    # Global actions
    display_global_actions(all_fines, fines_calculator)
    
    # Filter options
    col1, col2 = st.columns(2)
    with col1:
        show_filter = st.selectbox(
            "Vis:",
            ["Alle Bøder", "Kun Ubetalte", "Kun Betalte"]
        )
    
    with col2:
        player_filter = st.selectbox(
            "Filtrér efter Spiller:",
            ["Alle Spillere"] + list(fines_by_player.keys())
        )
    
    # Filter fines based on selection
    filtered_fines = all_fines.copy()
    
    if show_filter == "Kun Ubetalte":
        filtered_fines = [f for f in filtered_fines if not f.get('paid', False)]
    elif show_filter == "Kun Betalte":
        filtered_fines = [f for f in filtered_fines if f.get('paid', False)]
    
    if player_filter != "Alle Spillere":
        filtered_fines = [f for f in filtered_fines if f['player_name'] == player_filter]
    
    # Display filtered fines in a compact format
    display_filtered_fines(filtered_fines, fines_calculator)


def display_global_actions(all_fines, fines_calculator):
    """Display global action buttons."""
    col1, col2, col3 = st.columns(3)
    with col1:
        if st.button("💳 Markér ALLE Bøder som Betalt", use_container_width=True):
            for fine in all_fines:
                fine_key = list(fines_calculator.fines_data.keys())[
                    list(fines_calculator.fines_data.values()).index(fine)
                ]
                if not fine.get('paid', False):
                    fines_calculator.mark_fine_paid(fine_key)
            st.success("Alle bøder markeret som betalt!")
            st.rerun()
    
    with col2:
        if st.button("🔄 Markér ALLE Bøder som Ubetalt", use_container_width=True):
            for fine in all_fines:
                fine_key = list(fines_calculator.fines_data.keys())[
                    list(fines_calculator.fines_data.values()).index(fine)
                ]
                if fine.get('paid', False):
                    fines_calculator.fines_data[fine_key]['paid'] = False
                    if 'paid_date' in fines_calculator.fines_data[fine_key]:
                        del fines_calculator.fines_data[fine_key]['paid_date']
            fines_calculator.save_fines_data()
            st.success("Alle bøder markeret som ubetalt!")
            st.rerun()
    
    with col3:
        unpaid_count = sum(1 for fine in all_fines if not fine.get('paid', False))
        st.metric("Ubetalte Bøder", unpaid_count)


def display_filtered_fines(filtered_fines, fines_calculator):
    """Display filtered fines in compact format."""
    if filtered_fines:
        st.write(f"**Viser {len(filtered_fines)} bøder:**")
        
        for fine in filtered_fines:
            fine_key = list(fines_calculator.fines_data.keys())[
                list(fines_calculator.fines_data.values()).index(fine)
            ]
            
            col1, col2, col3, col4, col5 = st.columns([2, 2, 1, 1, 1])
            
            with col1:
                st.write(f"**{fine['player_name']}**")
            
            with col2:
                st.caption(f"{fine['event_name']} • {fine['event_date'][:10]}")
            
            with col3:
                st.write(f"{fine['fine_amount']} kr")
            
            with col4:
                # Quick payment toggle
                is_paid = fine.get('paid', False)
                paid_checkbox = st.checkbox(
                    "Betalt",
                    value=is_paid,
                    key=f"quick_paid_{fine_key}",
                    label_visibility="collapsed"
                )
                
                if paid_checkbox != is_paid:
                    if paid_checkbox:
                        fines_calculator.mark_fine_paid(fine_key)
                    else:
                        fines_calculator.fines_data[fine_key]['paid'] = False
                        if 'paid_date' in fines_calculator.fines_data[fine_key]:
                            del fines_calculator.fines_data[fine_key]['paid_date']
                        fines_calculator.save_fines_data()
                    st.rerun()
            
            with col5:
                if fine.get('paid', False):
                    st.success("✅")
                else:
                    st.error("❌")
            
            st.divider()
    else:
        st.info("Ingen bøder matcher det nuværende filter.")


def display_data_management_tab():
    """Display the data management tab."""
    st.subheader("Datastyring")
    
    col1, col2 = st.columns(2)
    
    with col1:
        if st.button("🔄 Gennemtving Datasynkronisering", use_container_width=True):
            with st.spinner("Synkroniserer data fra Spond..."):
                sync_data_wrapper()
            st.rerun()
    
    with col2:
        if st.button("🗑️ Ryd Lokale Data", use_container_width=True):
            if st.session_state.get('confirm_clear_data', False):
                st.session_state.fines_calculator = FinesCalculator()
                st.success("Lokale data ryddet!")
                st.session_state.confirm_clear_data = False
            else:
                st.session_state.confirm_clear_data = True
                st.warning("⚠️ Klik igen for at bekræfte datasletning!")
    
    # Reset confirmation if user navigates away
    if st.session_state.get('confirm_clear_data', False):
        if st.button("❌ Annuller Rydning af Data"):
            st.session_state.confirm_clear_data = False
    
    st.subheader("Statistikoversigt")
    
    # Show summary statistics
    fines_calculator = st.session_state.fines_calculator
    summary = fines_calculator.get_fines_summary()
    if summary:
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric("Samlet Bøder", summary['total_fines'])
        with col2:
            st.metric("Samlet Beløb", f"{summary['total_amount']:,} kr")
        with col3:
            st.metric("Betalte Bøder", summary['paid_fines'])
        with col4:
            st.metric("Ubetalt Beløb", f"{summary['unpaid_amount']:,} kr")
    
    # Display raw data (for debugging)
    with st.expander("🔍 Vis Rådata"):
        fines_data = st.session_state.fines_calculator.processed_fines_data
        if fines_data:
            st.json(fines_data)  # Display as JSON for debugging
        else:
            st.info("Ingen data tilgængelige.")