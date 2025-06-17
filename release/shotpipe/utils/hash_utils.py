"""
File Hashing Utility
Provides functions for calculating file hashes.
"""
import hashlib
import logging

logger = logging.getLogger(__name__)

def get_file_hash(file_path, block_size=65536):
    """
    Calculate the SHA-256 hash of a file.

    Args:
        file_path (str): The path to the file.
        block_size (int): The block size to read the file in chunks.

    Returns:
        str: The hex digest of the file's SHA-256 hash, or None if an error occurs.
    """
    if not file_path:
        logger.warning("File path is empty, cannot calculate hash.")
        return None
        
    try:
        sha256 = hashlib.sha256()
        with open(file_path, 'rb') as f:
            for block in iter(lambda: f.read(block_size), b''):
                sha256.update(block)
        return sha256.hexdigest()
    except FileNotFoundError:
        logger.error(f"Hash calculation error: File not found at {file_path}")
        return None
    except IOError as e:
        logger.error(f"Hash calculation error: Could not read file {file_path}. Error: {e}")
        return None
    except Exception as e:
        logger.error(f"An unexpected error occurred during hash calculation for {file_path}: {e}")
        return None 