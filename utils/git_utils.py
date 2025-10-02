"""Git utilities for automatic data backup to GitHub."""

import subprocess
import os
from datetime import datetime
import json
from typing import List, Optional


class GitAutoCommit:
    """Handles automatic git commits and pushes for data files."""
    
    def __init__(self, repo_path: str = "."):
        self.repo_path = repo_path
        
    def is_git_repo(self) -> bool:
        """Check if current directory is a git repository."""
        try:
            subprocess.run(['git', 'rev-parse', '--git-dir'], 
                         cwd=self.repo_path, 
                         capture_output=True, 
                         check=True)
            return True
        except subprocess.CalledProcessError:
            return False
    
    def has_changes(self, files: List[str] = None) -> bool:
        """Check if there are any uncommitted changes."""
        try:
            cmd = ['git', 'diff', '--quiet', '--exit-code']
            if files:
                cmd.extend(files)
            
            result = subprocess.run(cmd, 
                                  cwd=self.repo_path, 
                                  capture_output=True)
            return result.returncode != 0  # Non-zero means there are changes
        except subprocess.CalledProcessError:
            return False
    
    def auto_commit_data(self, 
                        files: List[str] = None, 
                        message: str = None,
                        push: bool = True) -> tuple[bool, str]:
        """
        Automatically commit and push data files to GitHub.
        
        Args:
            files: List of files to commit (if None, commits all data files)
            message: Custom commit message
            push: Whether to push to remote after commit
            
        Returns:
            (success, message) tuple
        """
        if not self.is_git_repo():
            return False, "Not a git repository"
        
        # Default data files to commit
        if files is None:
            files = [
                "member_data.json",
                "fines_data.json", 
                "training_matches.json",
                "manual_fine_types.json"
            ]
        
        # Filter to only existing files
        existing_files = [f for f in files if os.path.exists(os.path.join(self.repo_path, f))]
        
        if not existing_files:
            return False, "No data files to commit"
        
        # Check if there are actually changes
        if not self.has_changes(existing_files):
            return True, "No changes to commit"
        
        try:
            # Add files to staging
            subprocess.run(['git', 'add'] + existing_files, 
                         cwd=self.repo_path, 
                         check=True,
                         capture_output=True)
            
            # Create commit message
            if message is None:
                timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                message = f"Auto-update data files - {timestamp}"
            
            # Commit changes
            subprocess.run(['git', 'commit', '-m', message], 
                         cwd=self.repo_path, 
                         check=True,
                         capture_output=True)
            
            commit_msg = f"Committed changes to: {', '.join(existing_files)}"
            
            # Push to remote if requested
            if push:
                try:
                    subprocess.run(['git', 'push', 'origin', 'main'], 
                                 cwd=self.repo_path, 
                                 check=True,
                                 capture_output=True,
                                 timeout=30)  # 30 second timeout
                    return True, f"{commit_msg} and pushed to GitHub"
                except subprocess.TimeoutExpired:
                    return True, f"{commit_msg} but push timed out"
                except subprocess.CalledProcessError as e:
                    return True, f"{commit_msg} but push failed: {e}"
            else:
                return True, commit_msg
                
        except subprocess.CalledProcessError as e:
            return False, f"Git operation failed: {e}"
        except Exception as e:
            return False, f"Unexpected error: {e}"
    
    def auto_backup_on_data_change(self, 
                                  data_type: str,
                                  filename: str,
                                  operation: str = "update") -> tuple[bool, str]:
        """
        Automatically backup when specific data changes.
        
        Args:
            data_type: Type of data (e.g., 'member_data', 'fines', 'matches')
            filename: The file that was changed
            operation: Description of operation (e.g., 'sync', 'update', 'create')
        """
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        message = f"Auto-backup: {operation} {data_type} - {timestamp}"
        
        return self.auto_commit_data(
            files=[filename], 
            message=message, 
            push=True
        )


# Global instance for easy import
git_backup = GitAutoCommit()


def backup_data_file(filename: str, data_type: str, operation: str = "update") -> None:
    """
    Convenience function to backup a single data file.
    
    Args:
        filename: Name of the file to backup
        data_type: Type of data for commit message
        operation: Description of what was done
    """
    try:
        success, message = git_backup.auto_backup_on_data_change(
            data_type=data_type,
            filename=filename, 
            operation=operation
        )
        
        if success:
            print(f"✅ Auto-backup successful: {message}")
        else:
            print(f"⚠️ Auto-backup failed: {message}")
            
    except Exception as e:
        print(f"❌ Auto-backup error: {e}")


def backup_all_data(operation: str = "batch update") -> None:
    """
    Backup all data files at once.
    
    Args:
        operation: Description for commit message
    """
    try:
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S") 
        message = f"Auto-backup: {operation} - {timestamp}"
        
        success, result = git_backup.auto_commit_data(message=message, push=True)
        
        if success:
            print(f"✅ Batch backup successful: {result}")
        else:
            print(f"⚠️ Batch backup failed: {result}")
            
    except Exception as e:
        print(f"❌ Batch backup error: {e}")