"""Multi-machine synchronization for Claude Code Conductor."""

import os
import subprocess
import shutil
from pathlib import Path
from typing import Optional, Dict, List
import hashlib
import json


class Sync:
    """Handles synchronization of conductor state across machines."""

    def __init__(self, db_path: str = None, config_dir: str = None):
        """Initialize sync manager.

        Args:
            db_path: Path to database file
            config_dir: Path to config directory
        """
        if config_dir is None:
            self.config_dir = Path.home() / ".conductor"
        else:
            self.config_dir = Path(config_dir)

        if db_path is None:
            self.db_path = self.config_dir / "conductor.db"
        else:
            self.db_path = Path(db_path)

        self.sync_method = self.detect_sync_method()
        self.sync_state_file = self.config_dir / "sync_state.json"

    def detect_sync_method(self) -> str:
        """Detect available sync method.

        Returns:
            Sync method name (git, dropbox, or file)
        """
        # Check if we're in a git repository
        if self._is_git_repo(self.config_dir):
            return 'git'

        # Check for Dropbox
        dropbox_path = Path.home() / "Dropbox"
        if dropbox_path.exists():
            return 'dropbox'

        # Fall back to file-based sync
        return 'file'

    def _is_git_repo(self, path: Path) -> bool:
        """Check if path is in a git repository."""
        try:
            result = subprocess.run(
                ['git', 'rev-parse', '--git-dir'],
                cwd=str(path),
                capture_output=True,
                text=True
            )
            return result.returncode == 0
        except FileNotFoundError:
            return False

    def push_state(self) -> Dict[str, any]:
        """Push local state to remote.

        Returns:
            Dict with sync result
        """
        if self.sync_method == 'git':
            return self._push_git()
        elif self.sync_method == 'dropbox':
            return self._push_dropbox()
        else:
            return self._push_file()

    def pull_state(self) -> Dict[str, any]:
        """Pull remote state to local.

        Returns:
            Dict with sync result
        """
        if self.sync_method == 'git':
            return self._pull_git()
        elif self.sync_method == 'dropbox':
            return self._pull_dropbox()
        else:
            return self._pull_file()

    def _push_git(self) -> Dict[str, any]:
        """Push state using git."""
        try:
            # Initialize git repo if needed
            if not self._is_git_repo(self.config_dir):
                self._init_git_repo()

            # Add files
            files_to_sync = [
                'conductor.db',
                'registry.yaml',
                'config.yaml',
                'sync_state.json'
            ]

            for file in files_to_sync:
                file_path = self.config_dir / file
                if file_path.exists():
                    subprocess.run(
                        ['git', 'add', file],
                        cwd=str(self.config_dir),
                        check=True
                    )

            # Commit
            subprocess.run(
                ['git', 'commit', '-m', 'Sync conductor state'],
                cwd=str(self.config_dir),
                capture_output=True
            )

            # Push
            result = subprocess.run(
                ['git', 'push', 'origin', 'conductor-state'],
                cwd=str(self.config_dir),
                capture_output=True,
                text=True
            )

            success = result.returncode == 0

            return {
                'success': success,
                'method': 'git',
                'message': result.stdout if success else result.stderr
            }

        except subprocess.CalledProcessError as e:
            return {
                'success': False,
                'method': 'git',
                'error': str(e)
            }

    def _pull_git(self) -> Dict[str, any]:
        """Pull state using git."""
        try:
            if not self._is_git_repo(self.config_dir):
                return {
                    'success': False,
                    'method': 'git',
                    'error': 'Not a git repository'
                }

            # Pull changes
            result = subprocess.run(
                ['git', 'pull', 'origin', 'conductor-state'],
                cwd=str(self.config_dir),
                capture_output=True,
                text=True
            )

            success = result.returncode == 0

            return {
                'success': success,
                'method': 'git',
                'message': result.stdout if success else result.stderr
            }

        except subprocess.CalledProcessError as e:
            return {
                'success': False,
                'method': 'git',
                'error': str(e)
            }

    def _init_git_repo(self):
        """Initialize git repository for conductor config."""
        subprocess.run(['git', 'init'], cwd=str(self.config_dir), check=True)

        # Create branch
        subprocess.run(
            ['git', 'checkout', '-b', 'conductor-state'],
            cwd=str(self.config_dir),
            check=True
        )

        # Add .gitignore
        gitignore = self.config_dir / ".gitignore"
        gitignore.write_text("*.log\n*.tmp\n")

    def _push_dropbox(self) -> Dict[str, any]:
        """Push state using Dropbox."""
        try:
            dropbox_dir = Path.home() / "Dropbox" / ".conductor"
            dropbox_dir.mkdir(parents=True, exist_ok=True)

            # Copy files to Dropbox
            files_to_sync = [
                'conductor.db',
                'registry.yaml',
                'config.yaml',
                'sync_state.json'
            ]

            for file in files_to_sync:
                src = self.config_dir / file
                dst = dropbox_dir / file

                if src.exists():
                    shutil.copy2(src, dst)

            return {
                'success': True,
                'method': 'dropbox',
                'message': f'Synced {len(files_to_sync)} files to Dropbox'
            }

        except Exception as e:
            return {
                'success': False,
                'method': 'dropbox',
                'error': str(e)
            }

    def _pull_dropbox(self) -> Dict[str, any]:
        """Pull state using Dropbox."""
        try:
            dropbox_dir = Path.home() / "Dropbox" / ".conductor"

            if not dropbox_dir.exists():
                return {
                    'success': False,
                    'method': 'dropbox',
                    'error': 'Dropbox sync directory not found'
                }

            # Copy files from Dropbox
            files_to_sync = [
                'conductor.db',
                'registry.yaml',
                'config.yaml',
                'sync_state.json'
            ]

            synced = 0
            for file in files_to_sync:
                src = dropbox_dir / file
                dst = self.config_dir / file

                if src.exists():
                    # Check if remote is newer
                    if self._should_pull_file(src, dst):
                        shutil.copy2(src, dst)
                        synced += 1

            return {
                'success': True,
                'method': 'dropbox',
                'message': f'Synced {synced} files from Dropbox'
            }

        except Exception as e:
            return {
                'success': False,
                'method': 'dropbox',
                'error': str(e)
            }

    def _push_file(self) -> Dict[str, any]:
        """Push state using file-based sync."""
        # File-based sync requires manual setup
        sync_dir = Path.home() / ".conductor-sync"

        if not sync_dir.exists():
            return {
                'success': False,
                'method': 'file',
                'error': 'Sync directory not configured. Set up shared folder at ~/.conductor-sync'
            }

        try:
            files_to_sync = [
                'conductor.db',
                'registry.yaml',
                'config.yaml',
                'sync_state.json'
            ]

            for file in files_to_sync:
                src = self.config_dir / file
                dst = sync_dir / file

                if src.exists():
                    shutil.copy2(src, dst)

            return {
                'success': True,
                'method': 'file',
                'message': f'Synced to {sync_dir}'
            }

        except Exception as e:
            return {
                'success': False,
                'method': 'file',
                'error': str(e)
            }

    def _pull_file(self) -> Dict[str, any]:
        """Pull state using file-based sync."""
        sync_dir = Path.home() / ".conductor-sync"

        if not sync_dir.exists():
            return {
                'success': False,
                'method': 'file',
                'error': 'Sync directory not configured'
            }

        try:
            files_to_sync = [
                'conductor.db',
                'registry.yaml',
                'config.yaml',
                'sync_state.json'
            ]

            synced = 0
            for file in files_to_sync:
                src = sync_dir / file
                dst = self.config_dir / file

                if src.exists():
                    if self._should_pull_file(src, dst):
                        shutil.copy2(src, dst)
                        synced += 1

            return {
                'success': True,
                'method': 'file',
                'message': f'Synced {synced} files from {sync_dir}'
            }

        except Exception as e:
            return {
                'success': False,
                'method': 'file',
                'error': str(e)
            }

    def _should_pull_file(self, src: Path, dst: Path) -> bool:
        """Check if remote file should be pulled.

        Args:
            src: Source (remote) file
            dst: Destination (local) file

        Returns:
            True if should pull
        """
        if not dst.exists():
            return True

        # Compare modification times
        src_mtime = src.stat().st_mtime
        dst_mtime = dst.stat().st_mtime

        return src_mtime > dst_mtime

    def get_sync_status(self) -> Dict[str, any]:
        """Get current sync status.

        Returns:
            Dict with sync information
        """
        # Load sync state
        state = self._load_sync_state()

        # Check for local changes
        local_hash = self._calculate_db_hash()

        has_changes = (
            'last_hash' not in state or
            state['last_hash'] != local_hash
        )

        return {
            'method': self.sync_method,
            'has_local_changes': has_changes,
            'last_sync': state.get('last_sync'),
            'sync_count': state.get('sync_count', 0)
        }

    def _load_sync_state(self) -> Dict:
        """Load sync state from file."""
        if not self.sync_state_file.exists():
            return {}

        try:
            with open(self.sync_state_file, 'r') as f:
                return json.load(f)
        except Exception:
            return {}

    def _save_sync_state(self, state: Dict):
        """Save sync state to file."""
        self.config_dir.mkdir(parents=True, exist_ok=True)

        with open(self.sync_state_file, 'w') as f:
            json.dump(state, f, indent=2)

    def _calculate_db_hash(self) -> str:
        """Calculate hash of database file.

        Returns:
            SHA256 hash
        """
        if not self.db_path.exists():
            return ""

        sha256 = hashlib.sha256()

        with open(self.db_path, 'rb') as f:
            for chunk in iter(lambda: f.read(4096), b""):
                sha256.update(chunk)

        return sha256.hexdigest()

    def mark_synced(self):
        """Mark current state as synced."""
        state = self._load_sync_state()

        state['last_sync'] = str(os.times())
        state['last_hash'] = self._calculate_db_hash()
        state['sync_count'] = state.get('sync_count', 0) + 1

        self._save_sync_state(state)

    def auto_sync(self) -> Optional[Dict]:
        """Perform automatic sync if needed.

        Returns:
            Sync result or None if no sync needed
        """
        status = self.get_sync_status()

        if status['has_local_changes']:
            result = self.push_state()

            if result['success']:
                self.mark_synced()

            return result

        return None
