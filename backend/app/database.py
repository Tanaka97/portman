"""
Database connection and client setup.
Provides a Supabase client for the application.
"""

from supabase import create_client, Client
from functools import lru_cache
from .config import get_settings


@lru_cache()
def get_supabase_client() -> Client:
    """
    Create and return a Supabase client.
    Uses lru_cache to create only one client instance.
    
    Returns:
        Supabase Client object connected to your project
    
    Raises:
        Exception: If connection fails
    """
    settings = get_settings()
    
    try:
        # Create Supabase client with your credentials
        supabase: Client = create_client(
            supabase_url=settings.supabase_url,
            supabase_key=settings.supabase_key
        )
        
        print("✅ Successfully connected to Supabase!")
        return supabase
        
    except Exception as e:
        print(f"❌ Failed to connect to Supabase: {e}")
        raise


# Test function (we'll use this to verify connection)
def test_connection():
    """
    Test the Supabase connection.
    """
    try:
        client = get_supabase_client()
        print(f"✅ Connection successful!")
        print(f"✅ Client type: {type(client)}")
        return True
    except Exception as e:
        print(f"❌ Connection failed: {e}")
        return False


if __name__ == "__main__":
    # Run this file directly to test connection
    print("Testing Supabase connection...")
    test_connection()