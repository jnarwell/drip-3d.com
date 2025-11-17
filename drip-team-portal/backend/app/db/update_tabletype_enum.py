"""Update tabletype enum to match new values"""
import psycopg2
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT
from app.core.config import settings

def update_tabletype_enum():
    # Parse the database URL
    import urllib.parse
    result = urllib.parse.urlparse(settings.DATABASE_URL)
    
    conn = psycopg2.connect(
        database=result.path[1:],
        user=result.username,
        password=result.password,
        host=result.hostname,
        port=result.port
    )
    
    conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
    cur = conn.cursor()
    
    try:
        # First, check if property_table_templates table exists and has data
        cur.execute("SELECT COUNT(*) FROM information_schema.tables WHERE table_name = 'property_table_templates'")
        table_exists = cur.fetchone()[0] > 0
        
        if table_exists:
            cur.execute("SELECT COUNT(*) FROM property_table_templates")
            has_data = cur.fetchone()[0] > 0
            
            if has_data:
                print("Warning: property_table_templates table has data. Manual migration required.")
                return
        
        # Drop the old enum type and recreate with new values
        print("Updating tabletype enum...")
        
        # If table exists, drop it first (since it's empty)
        if table_exists:
            cur.execute("DROP TABLE IF EXISTS property_table_templates CASCADE")
        
        # Drop and recreate the enum
        cur.execute("DROP TYPE IF EXISTS tabletype CASCADE")
        cur.execute("""
            CREATE TYPE tabletype AS ENUM (
                'single_var_lookup',
                'range_based_lookup', 
                'multi_var_lookup',
                'reference_only'
            )
        """)
        
        # Also create/update interpolationtype enum
        cur.execute("DROP TYPE IF EXISTS interpolationtype CASCADE")
        cur.execute("""
            CREATE TYPE interpolationtype AS ENUM (
                'linear',
                'logarithmic',
                'polynomial',
                'range_lookup',
                'none'
            )
        """)
        
        print("Enums updated successfully!")
        
    except Exception as e:
        print(f"Error updating enums: {e}")
    finally:
        cur.close()
        conn.close()

if __name__ == "__main__":
    update_tabletype_enum()