"""
Gold tier integrations module for external system clients.

This module contains client implementations for:
- Odoo accounting system (odoo_client.py)
- Facebook social media (facebook_client.py)
- Instagram social media (instagram_client.py)
- Twitter social media (twitter_client.py)
"""

from .odoo_client import OdooClient, create_odoo_client

__all__ = [
    'odoo_client',
    'facebook_client',
    'instagram_client',
    'twitter_client',
    'OdooClient',
    'create_odoo_client',
]
