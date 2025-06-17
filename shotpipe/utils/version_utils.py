"""
Version Utility
Provides functions for getting application and Git version info.
"""
import subprocess
import logging

logger = logging.getLogger(__name__)

# 애플리케이션의 기본 버전
APP_VERSION = "1.3.0"

def get_version_info():
    """
    Get the application version string, including Git info if available.
    
    Returns:
        str: A formatted version string.
    """
    version = APP_VERSION
    commit_hash = ""

    try:
        # Get the latest git commit hash (short version)
        result = subprocess.run(
            ["git", "rev-parse", "--short", "HEAD"],
            capture_output=True,
            text=True,
            check=False
        )
        if result.returncode == 0:
            commit_hash = result.stdout.strip()
            
    except (FileNotFoundError, subprocess.SubprocessError) as e:
        logger.warning(f"Could not get git commit hash: {e}")

    if commit_hash:
        return f"v{version} (commit: {commit_hash})"
    else:
        return f"v{version}" 