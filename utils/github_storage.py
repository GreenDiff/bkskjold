"""
GitHub Storage Module
====================

Automatisk gem data til GitHub repository for permanent lagring.
"""

import json
import subprocess
import os
from datetime import datetime
import streamlit as st


def commit_and_push_data(file_path: str, commit_message: str = None):
    """
    Commit og push en datafil til GitHub.
    
    Args:
        file_path: Sti til filen der skal committes
        commit_message: Custom commit besked (optional)
    """
    try:
        if not os.path.exists(file_path):
            print(f"File {file_path} does not exist")
            return False
            
        # Default commit message
        if not commit_message:
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            filename = os.path.basename(file_path)
            commit_message = f"Auto-update {filename} - {timestamp}"
        
        # Git commands
        subprocess.run(['git', 'add', file_path], check=True, capture_output=True)
        subprocess.run(['git', 'commit', '-m', commit_message], check=True, capture_output=True)
        subprocess.run(['git', 'push', 'origin', 'main'], check=True, capture_output=True)
        
        print(f"✅ Successfully committed and pushed {file_path}")
        return True
        
    except subprocess.CalledProcessError as e:
        print(f"❌ Git error for {file_path}: {e}")
        return False
    except Exception as e:
        print(f"❌ Unexpected error for {file_path}: {e}")
        return False


def save_json_to_github(data, file_path: str, commit_message: str = None):
    """
    Gem JSON data til fil og push til GitHub.
    
    Args:
        data: Data der skal gemmes
        file_path: Sti til filen
        commit_message: Custom commit besked (optional)
    """
    try:
        # Gem til lokal fil først
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        
        # Commit og push til GitHub
        return commit_and_push_data(file_path, commit_message)
        
    except Exception as e:
        print(f"❌ Error saving {file_path}: {e}")
        return False


def auto_backup_on_change(data, file_path: str, backup_message: str = None):
    """
    Automatisk backup når data ændres.
    Bruger session state til at tracke ændringer.
    """
    # Create a unique key for this file's hash
    file_key = f"backup_hash_{os.path.basename(file_path)}"
    
    # Calculate hash of current data
    import hashlib
    data_str = json.dumps(data, sort_keys=True)
    current_hash = hashlib.md5(data_str.encode()).hexdigest()
    
    # Check if data has changed
    if file_key not in st.session_state or st.session_state[file_key] != current_hash:
        # Data has changed, save and backup
        success = save_json_to_github(data, file_path, backup_message)
        if success:
            st.session_state[file_key] = current_hash
            st.success(f"📂 Data gemt til GitHub: {os.path.basename(file_path)}")
        else:
            st.warning(f"⚠️ Kunne ikke gemme til GitHub: {os.path.basename(file_path)}")
        
        return success
    
    return True  # No changes, no backup needed


# Convenience functions for specific data types
def save_training_matches(matches_data):
    """Gem træningskampe til GitHub."""
    return save_json_to_github(
        matches_data, 
        'training_matches.json', 
        'Opdater træningskampe data'
    )


def save_fines_data(fines_data):
    """Gem bøder til GitHub."""
    return save_json_to_github(
        fines_data, 
        'fines_data.json', 
        'Opdater bøder data'
    )


def save_member_data(member_data):
    """Gem medlem data til GitHub."""
    return save_json_to_github(
        member_data, 
        'member_data.json', 
        'Opdater medlem data'
    )