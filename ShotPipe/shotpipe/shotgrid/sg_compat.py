"""
Shotgrid API3 compatibility module for Python 3.12+
This patches shotgun_api3 to work with modern Python versions
"""
import sys
import importlib
import logging
import types

logger = logging.getLogger(__name__)

def patch_shotgun_api3():
    """Patch shotgun_api3 to work with Python 3.12+"""
    try:
        # Check if six is installed
        import six
        logger.info("six module is available")
        
        # Create patches for missing modules
        if 'shotgun_api3.lib.six' not in sys.modules:
            sys.modules['shotgun_api3.lib.six'] = six
            logger.info("Patched shotgun_api3.lib.six")
        
        if 'shotgun_api3.lib.six.moves' not in sys.modules:
            sys.modules['shotgun_api3.lib.six.moves'] = six.moves
            logger.info("Patched shotgun_api3.lib.six.moves")
        
        # Add PY38 attribute if missing
        if not hasattr(six, 'PY38'):
            six.PY38 = sys.version_info >= (3, 8)
            logger.info("Added PY38 attribute to six module")
        
        # Handle specific xmlrpc client imports
        import xmlrpc.client
        sys.modules['shotgun_api3.lib.six.moves.xmlrpc_client'] = xmlrpc.client
        logger.info("Patched shotgun_api3.lib.six.moves.xmlrpc_client")
        
        # Handle http client imports
        import http.client
        sys.modules['shotgun_api3.lib.six.moves.http_client'] = http.client
        logger.info("Patched shotgun_api3.lib.six.moves.http_client")
        
        # Handle urllib imports
        import urllib.parse
        import urllib.request
        import urllib.error
        
        # Create moves.urllib module structure
        class UrllibModule(types.ModuleType):
            parse = urllib.parse
            request = urllib.request
            error = urllib.error
        
        urllib_module = UrllibModule('shotgun_api3.lib.six.moves.urllib')
        sys.modules['shotgun_api3.lib.six.moves.urllib'] = urllib_module
        sys.modules['shotgun_api3.lib.six.moves.urllib.parse'] = urllib.parse
        sys.modules['shotgun_api3.lib.six.moves.urllib.request'] = urllib.request
        sys.modules['shotgun_api3.lib.six.moves.urllib.error'] = urllib.error
        logger.info("Patched shotgun_api3.lib.six.moves.urllib modules")
        
        return True
    except ImportError as e:
        logger.error(f"Failed to patch shotgun_api3: {e}")
        return False

# Apply patches
is_patched = patch_shotgun_api3()