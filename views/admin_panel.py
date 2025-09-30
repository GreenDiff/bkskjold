"""Admin panel page for Spond application."""

import streamlit as st
import json
import app_config
from components.auth import check_admin_login, admin_login, admin_logout
from utils.data_loader import sync_data_wrapper, FinesCalculator


def load_manual_fine_types():
    """Load manual fine types from file."""
    try:
        with open('manual_fine_types.json', 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        return {}
    except json.JSONDecodeError:
        return {}


def save_manual_fine_types(manual_fine_types):
    """Save manual fine types to file."""
    try:
        with open('manual_fine_types.json', 'w') as f:
            json.dump(manual_fine_types, f, indent=2, ensure_ascii=False)
    except Exception as e:
        st.error(f"Fejl ved gemning af manuel bøde typer: {e}")


def ensure_manual_fine_types_loaded():
    """Ensure manual fine types are loaded in session state."""
    if 'manual_fine_types' not in st.session_state:
        st.session_state.manual_fine_types = load_manual_fine_types()


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
    
    # Show basic system info
    st.info(f"**Gruppe ID:** {app_config.GROUP_ID} | **Brugernavn:** {app_config.SPOND_USERNAME} | **Sent Svar Timer:** {app_config.LATE_RESPONSE_HOURS}t")
    
    st.markdown("---")
    
    # Only show manual fine configuration
    display_manual_fine_configuration()


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


def update_fine_amounts(training_fine, training_loss_fine, late_fine):
    """Update the fine amounts in app_config.py"""
    try:
        # Read current config
        config_file = "/Users/linus/Downloads/Spond-main/app_config.py"
        with open(config_file, 'r', encoding='utf-8') as f:
            lines = f.readlines()
        
        # Update the values
        new_lines = []
        training_loss_found = False
        
        for line in lines:
            if line.startswith('FINE_MISSING_TRAINING'):
                new_lines.append(f'FINE_MISSING_TRAINING = {training_fine}\n')
            elif line.startswith('FINE_TRAINING_LOSS'):
                new_lines.append(f'FINE_TRAINING_LOSS = {training_loss_fine}\n')
                training_loss_found = True
            elif line.startswith('FINE_LATE_RESPONSE'):
                new_lines.append(f'FINE_LATE_RESPONSE = {late_fine}\n')
            else:
                new_lines.append(line)
        
        # Add FINE_TRAINING_LOSS if it doesn't exist
        if not training_loss_found:
            # Insert after FINE_MISSING_TRAINING
            for i, line in enumerate(new_lines):
                if line.startswith('FINE_MISSING_TRAINING'):
                    new_lines.insert(i + 1, f'FINE_TRAINING_LOSS = {training_loss_fine}\n')
                    break
        
        # Write back to file
        with open(config_file, 'w', encoding='utf-8') as f:
            f.writelines(new_lines)
        
        # Update the imported config
        import importlib
        import app_config
        importlib.reload(app_config)
        
        st.success(f"✅ Bødebeløb opdateret! Træning/Udeblivelse: {training_fine} kr, Tab af træningskamp: {training_loss_fine} kr, Sent svar: {late_fine} kr")
        
    except Exception as e:
        st.error(f"❌ Fejl ved opdatering: {str(e)}")
        st.error("Prøv at genstarte appen for at se ændringerne.")


def display_manual_fine_configuration():
    """Display manual fine type configuration in the config tab."""
    st.subheader("📝 Manuel Bøde Typer")
    
    # Create two columns: Create new and Edit existing
    col1, col2 = st.columns([1, 1])
    
    with col1:
        st.markdown("##### ➕ Opret Ny Bøde")
        
        with st.form("config_manual_fine_form"):
            fine_name = st.text_input(
                "Bøde Navn",
                placeholder="f.eks. Forsinket til træning, Mobil i omklædning, etc."
            )
            
            fine_amount = st.number_input(
                "Bøde Beløb (kr)",
                min_value=0,
                value=50,
                step=25
            )
            
            fine_description = st.text_area(
                "Beskrivelse (valgfri)",
                placeholder="Detaljeret beskrivelse af hvornår denne bøde anvendes..."
            )
            
            submitted = st.form_submit_button("💾 Opret Bøde Type", use_container_width=True)
            
            if submitted and fine_name and fine_amount > 0:
                # Store manual fine type in session state
                if 'manual_fine_types' not in st.session_state:
                    st.session_state.manual_fine_types = {}
                
                fine_id = fine_name.replace(" ", "_").lower().replace(",", "").replace(".", "")
                
                # Load existing manual fine types from file
                manual_fine_types = load_manual_fine_types()
                
                # Check if fine type already exists
                if fine_id in manual_fine_types:
                    st.error(f"Bøde type '{fine_name}' eksisterer allerede!")
                else:
                    from datetime import datetime
                    manual_fine_types[fine_id] = {
                        'name': fine_name,
                        'amount': fine_amount,
                        'description': fine_description,
                        'created_date': datetime.now().strftime('%Y-%m-%d %H:%M')
                    }
                    
                    # Save to both file and session state
                    save_manual_fine_types(manual_fine_types)
                    st.session_state.manual_fine_types = manual_fine_types
                    
                    st.success(f"✅ Manuel bøde type '{fine_name}' oprettet!")
                    st.rerun()
    
    with col2:
        st.markdown("##### ✏️ Rediger Nuværende Bøder")
        
        # First show standard automated fines
        st.markdown("###### 🤖 Standard Automatiserede Bøder")
        
        # Standard fines with editable amounts
        with st.form("standard_fine_config_form"):
            st.markdown("*Disse bøder tildeles automatisk baseret på Spond data:*")
            
            col_a, col_b = st.columns(2)
            with col_a:
                new_training_fine = st.number_input(
                    "Trænings/Udeblivelses Bøde (kr)", 
                    value=app_config.FINE_MISSING_TRAINING,
                    min_value=0,
                    step=25
                )
                new_training_loss_fine = st.number_input(
                    "Tab af Træningskamp Bøde (kr)", 
                    value=getattr(app_config, 'FINE_TRAINING_LOSS', 25),
                    min_value=0,
                    step=25,
                    help="Bøde for at tabe en træningskamp"
                )
                new_late_fine = st.number_input(
                    "Sent Svar Bøde (kr)", 
                    value=app_config.FINE_LATE_RESPONSE,
                    min_value=0,
                    step=5
                )
            
            with col_b:
                # Add some info about automation
                st.caption("⚡ Automatisk tildeling baseret på:")
                st.caption("• Manglende deltagelse i træning")
                st.caption("• Tab af træningskamp (fra Hold Udvælger)")
                st.caption(f"• Svar senere end {app_config.LATE_RESPONSE_HOURS} timer")
            
            if st.form_submit_button("💾 Opdater Standard Bødebeløb"):
                update_fine_amounts(new_training_fine, new_training_loss_fine, new_late_fine)
        
        st.markdown("---")
        
        # Then show manual fine types
        st.markdown("###### 📝 Manuel Bøde Typer")
        
        # Ensure manual fine types are loaded
        ensure_manual_fine_types_loaded()
        manual_fine_types = st.session_state.manual_fine_types
        
        if not manual_fine_types:
            st.info("Ingen manuel bøde typer oprettet endnu.")
        else:
            # Show count and summary
            st.metric("Antal Manuel Bøde Typer", len(manual_fine_types))
            
            # Filter and search
            search_term = st.text_input("🔍 Søg bøde typer", placeholder="Indtast navn...")
            
            filtered_types = manual_fine_types
            if search_term:
                filtered_types = {k: v for k, v in manual_fine_types.items() 
                                if search_term.lower() in v['name'].lower()}
            
            # Display fine types
            for fine_id, fine_data in filtered_types.items():
                with st.container():
                    st.markdown(f"**🎯 {fine_data['name']}**")
                    
                    col_amount, col_edit, col_delete = st.columns([2, 1, 1])
                    
                    with col_amount:
                        # Editable amount
                        new_amount = st.number_input(
                            "Beløb (kr)",
                            value=fine_data['amount'],
                            min_value=0,
                            step=25,
                            key=f"config_amount_{fine_id}",
                            label_visibility="collapsed"
                        )
                        
                        if new_amount != fine_data['amount']:
                            st.session_state.manual_fine_types[fine_id]['amount'] = new_amount
                            save_manual_fine_types(st.session_state.manual_fine_types)
                            st.success("💾 Beløb opdateret!")
                            st.rerun()
                    
                    with col_edit:
                        if st.button("✏️", key=f"edit_{fine_id}", help="Rediger beskrivelse"):
                            st.session_state[f'editing_{fine_id}'] = True
                    
                    with col_delete:
                        if st.button("🗑️", key=f"config_delete_{fine_id}", help="Slet denne bøde type"):
                            if st.session_state.get(f'confirm_config_delete_{fine_id}', False):
                                del st.session_state.manual_fine_types[fine_id]
                                save_manual_fine_types(st.session_state.manual_fine_types)
                                st.session_state[f'confirm_config_delete_{fine_id}'] = False
                                st.success("Bøde type slettet!")
                                st.rerun()
                            else:
                                st.session_state[f'confirm_config_delete_{fine_id}'] = True
                                st.warning("⚠️ Klik igen for at bekræfte sletning!")
                    
                    # Show description
                    if fine_data.get('description'):
                        st.caption(f"📝 {fine_data['description']}")
                    
                    # Edit description if in edit mode
                    if st.session_state.get(f'editing_{fine_id}', False):
                        with st.form(f"edit_desc_{fine_id}"):
                            new_desc = st.text_area(
                                "Ny beskrivelse",
                                value=fine_data.get('description', ''),
                                key=f"new_desc_{fine_id}"
                            )
                            
                            col_save, col_cancel = st.columns(2)
                            with col_save:
                                if st.form_submit_button("💾 Gem"):
                                    st.session_state.manual_fine_types[fine_id]['description'] = new_desc
                                    save_manual_fine_types(st.session_state.manual_fine_types)
                                    st.session_state[f'editing_{fine_id}'] = False
                                    st.success("Beskrivelse opdateret!")
                                    st.rerun()
                            
                            with col_cancel:
                                if st.form_submit_button("❌ Annuller"):
                                    st.session_state[f'editing_{fine_id}'] = False
                                    st.rerun()
                    
                    st.caption(f"🕐 Oprettet: {fine_data.get('created_date', 'Ukendt')}")
                    st.markdown("---")


def display_manual_fine_creation():
    """Display bulk assignment interface for existing fine types."""
    st.subheader("⚡ Tildel Bøder til Spillere")
    
    # Load member data for player selection
    from utils.data_loader import load_member_data
    member_data = load_member_data()
    
    if not member_data:
        st.warning("Ingen medlemsdata tilgængelig. Synkroniser data først.")
        return
    
    # Check if there are any manual fine types created
    ensure_manual_fine_types_loaded()
    manual_fine_types = st.session_state.manual_fine_types
    
    if not manual_fine_types:
        st.warning("⚠️ Ingen bødetyper tilgængelige! Opret først bødetyper under **Konfiguration** tabben.")
        return
    
    with st.form("bulk_assign_form"):
        # Select fine type
        fine_type_options = {f"{data['name']} ({data['amount']} kr)": fine_id 
                           for fine_id, data in manual_fine_types.items()}
        
        selected_fine_display = st.selectbox(
            "Vælg Bøde Type",
            options=list(fine_type_options.keys())
        )
        
        selected_fine_id = fine_type_options.get(selected_fine_display) if selected_fine_display else None
        
        # Multi-select players
        player_names = [member['name'] for member in member_data.values()]
        selected_players = st.multiselect(
            "Vælg Spillere",
            options=player_names,
            help="Vælg en eller flere spillere til at tildele bøden"
        )
        
        # Custom reason (optional)
        custom_reason = st.text_input(
            "Tilpasset Begrundelse (valgfri)",
            placeholder="f.eks. 'Fra kamp d. 30/09 mod ABC'"
        )
        
        bulk_submitted = st.form_submit_button("⚡ Tildel Bøder", use_container_width=True)
        
        if bulk_submitted and selected_fine_id and selected_players:
            assign_bulk_manual_fines(selected_fine_id, selected_players, custom_reason, member_data)
        
    # Add recent assignments summary
    st.markdown("---")
    st.markdown("##### 📊 Seneste Tildelinger")
    
    # Load fines data to show recent manual fines
    try:
        import json
        with open('fines_data.json', 'r') as f:
            fines_data = json.load(f)
        
        # Filter manual fines and show recent ones
        manual_fines = [fine for fine in fines_data.values() if fine.get('manual_fine', False)]
        recent_fines = sorted(manual_fines, key=lambda x: x.get('created_date', ''), reverse=True)[:5]
        
        if recent_fines:
            for fine in recent_fines:
                st.info(f"🎯 **{fine['player_name']}** - {fine['event_name']} ({fine['fine_amount']} kr) - {fine.get('created_date', '')[:10]}")
        else:
            st.info("Ingen manuelle bøder tildelt endnu.")
    
    except (FileNotFoundError, json.JSONDecodeError):
        st.info("Ingen bødedata tilgængelig endnu.")


def assign_bulk_manual_fines(fine_type_id, selected_players, custom_reason, member_data):
    """Assign manual fines to multiple players."""
    import json
    from datetime import datetime
    
    # Get fine type details
    manual_fine_types = st.session_state.get('manual_fine_types', {})
    fine_type = manual_fine_types.get(fine_type_id)
    
    if not fine_type:
        st.error("Bøde type ikke fundet!")
        return
    
    # Load existing fines
    try:
        with open('fines_data.json', 'r') as f:
            fines_data = json.load(f)
    except FileNotFoundError:
        fines_data = {}
    
    current_time = datetime.now().isoformat()
    assigned_count = 0
    
    # Create fines for each selected player
    for player_name in selected_players:
        # Find player ID from member_data
        player_id = None
        for member_id, member in member_data.items():
            if member['name'] == player_name:
                player_id = member_id
                break
        
        if not player_id:
            # Create a normalized player_id from name
            player_id = player_name.replace(" ", "_")
        
        # Create unique fine ID
        fine_id = f"MANUAL_{fine_type_id.upper()}_{current_time[:10].replace('-', '')}_{player_id}"
        
        # Event name with custom reason if provided
        event_name = fine_type['name']
        if custom_reason:
            event_name += f" - {custom_reason}"
        
        # Create fine entry
        fines_data[fine_id] = {
            'player_id': player_id,
            'player_name': player_name,
            'event_id': f"MANUAL_{fine_type_id}_{current_time}",
            'event_name': event_name,
            'event_date': current_time,
            'fine_type': 'manual',
            'fine_subtype': fine_type_id,
            'fine_amount': fine_type['amount'],
            'paid': False,
            'created_date': current_time,
            'manual_fine': True,
            'description': fine_type.get('description', '')
        }
        
        assigned_count += 1
    
    # Save updated fines
    try:
        with open('fines_data.json', 'w') as f:
            json.dump(fines_data, f, indent=2, ensure_ascii=False)
        
        st.success(f"✅ {assigned_count} bøder tildelt successfully!")
        
        # Show summary
        total_amount = assigned_count * fine_type['amount']
        st.info(f"📊 **Sammendrag:**\n"
                f"- Bøde: {fine_type['name']}\n"
                f"- Spillere: {', '.join(selected_players)}\n" 
                f"- Beløb pr. spiller: {fine_type['amount']} kr\n"
                f"- Samlet beløb: {total_amount} kr")
        
        # Refresh the fines calculator
        st.session_state.fines_calculator = FinesCalculator()
        
    except Exception as e:
        st.error(f"Fejl ved oprettelse af bøder: {e}")


def display_fine_management_tab():
    """Display the fine management tab."""
    # Add manual fine creation section first
    display_manual_fine_creation()
    
    st.markdown("---")
    
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
    col1, col2, col3 = st.columns(3)
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
    
    with col3:
        # Get unique fine types for filter
        fine_types = set()
        ensure_manual_fine_types_loaded()
        manual_fine_types = st.session_state.manual_fine_types
        
        for fine in all_fines:
            if fine['fine_type'] == 'manual':
                # For manual fines, get the display name
                fine_subtype = fine.get('fine_subtype', 'unknown_manual')
                if fine_subtype in manual_fine_types:
                    display_name = manual_fine_types[fine_subtype]['name']
                else:
                    display_name = fine_subtype.replace('_', ' ').title()
                fine_types.add(display_name)
            else:
                # For automatic fines, use mapped names
                type_name_map = {
                    'training_loss': 'Tab af Træningskamp',
                    'no_show': 'Udeblivelser',
                    'late_response': 'Sene Svar'
                }
                display_name = type_name_map.get(fine['fine_type'], fine['fine_type'])
                fine_types.add(display_name)
        
        fine_type_filter = st.selectbox(
            "Filtrér efter Bødetype:",
            ["Alle Typer"] + sorted(list(fine_types))
        )
    
    # Filter fines based on selection
    filtered_fines = all_fines.copy()
    
    if show_filter == "Kun Ubetalte":
        filtered_fines = [f for f in filtered_fines if not f.get('paid', False)]
    elif show_filter == "Kun Betalte":
        filtered_fines = [f for f in filtered_fines if f.get('paid', False)]
    
    if player_filter != "Alle Spillere":
        filtered_fines = [f for f in filtered_fines if f['player_name'] == player_filter]
    
    if fine_type_filter != "Alle Typer":
        # Filter by fine type
        type_filtered_fines = []
        for fine in filtered_fines:
            if fine['fine_type'] == 'manual':
                # For manual fines, get the display name
                fine_subtype = fine.get('fine_subtype', 'unknown_manual')
                if fine_subtype in manual_fine_types:
                    display_name = manual_fine_types[fine_subtype]['name']
                else:
                    display_name = fine_subtype.replace('_', ' ').title()
            else:
                # For automatic fines, use mapped names
                type_name_map = {
                    'training_loss': 'Tab af Træningskamp',
                    'no_show': 'Udeblivelser',
                    'late_response': 'Sene Svar'
                }
                display_name = type_name_map.get(fine['fine_type'], fine['fine_type'])
            
            if display_name == fine_type_filter:
                type_filtered_fines.append(fine)
        
        filtered_fines = type_filtered_fines
    
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
            
            col1, col2, col3, col4, col5, col6, col7 = st.columns([2, 2, 1.5, 1, 1, 1, 0.7])
            
            with col1:
                st.write(f"**{fine['player_name']}**")
            
            with col2:
                st.caption(f"{fine['event_name']} • {fine['event_date'][:10]}")
            
            with col3:
                # Show fine type
                if fine['fine_type'] == 'manual':
                    fine_subtype = fine.get('fine_subtype', 'unknown_manual')
                    ensure_manual_fine_types_loaded()
                    manual_fine_types = st.session_state.manual_fine_types
                    if fine_subtype in manual_fine_types:
                        display_name = manual_fine_types[fine_subtype]['name']
                    else:
                        display_name = fine_subtype.replace('_', ' ').title()
                else:
                    type_name_map = {
                        'training_loss': 'Tab af Træningskamp',
                        'no_show': 'Udeblivelser',
                        'late_response': 'Sene Svar'
                    }
                    display_name = type_name_map.get(fine['fine_type'], fine['fine_type'])
                
                st.caption(f"🎯 {display_name}")
            
            with col4:
                st.write(f"{fine['fine_amount']} kr")
            
            with col5:
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
            
            with col6:
                if fine.get('paid', False):
                    st.success("✅")
                else:
                    st.error("❌")
            
            with col7:
                # Delete fine button
                if st.button("🗑️", key=f"delete_fine_{fine_key}", help=f"Slet denne bøde for {fine['player_name']}"):
                    if st.session_state.get(f'confirm_delete_fine_{fine_key}', False):
                        fines_calculator.remove_fine(fine_key)
                        st.success(f"Bøde slettet for {fine['player_name']}!")
                        st.session_state[f'confirm_delete_fine_{fine_key}'] = False
                        st.rerun()
                    else:
                        st.session_state[f'confirm_delete_fine_{fine_key}'] = True
                        st.warning("⚠️ Klik igen for at bekræfte sletning!")
            
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