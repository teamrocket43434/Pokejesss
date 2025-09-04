import os
import asyncio
import asyncpg
import json
from contextlib import asynccontextmanager

# Replace your MongoDB variables with these
DATABASE_URL = os.getenv("DATABASE_URL")  # Railway provides this automatically

# Database connection pool
db_pool = None

async def initialize_database():
    """Initialize PostgreSQL connection"""
    global db_pool
    try:
        if not DATABASE_URL:
            print("Warning: DATABASE_URL not set, collection features disabled")
            return
        
        print("Connecting to PostgreSQL...")
        
        # Create connection pool
        db_pool = await asyncpg.create_pool(
            DATABASE_URL,
            min_size=1,
            max_size=3,
            command_timeout=60
        )
        
        # Create tables if they don't exist
        async with db_pool.acquire() as conn:
            await conn.execute('''
                CREATE TABLE IF NOT EXISTS pokemon_collections (
                    id SERIAL PRIMARY KEY,
                    user_id BIGINT NOT NULL,
                    guild_id BIGINT NOT NULL,
                    pokemon_list TEXT[] DEFAULT '{}',
                    created_at TIMESTAMP DEFAULT NOW(),
                    updated_at TIMESTAMP DEFAULT NOW(),
                    UNIQUE(user_id, guild_id)
                )
            ''')
            
            # Create index for faster lookups
            await conn.execute('''
                CREATE INDEX IF NOT EXISTS idx_collections_user_guild 
                ON pokemon_collections(user_id, guild_id)
            ''')
        
        print("✅ PostgreSQL database initialized successfully")
        
    except Exception as e:
        print(f"❌ Database initialization failed: {e}")
        db_pool = None

async def add_pokemon_to_collection(user_id, guild_id, pokemon_names):
    """Add Pokemon to user's collection"""
    if db_pool is None:
        return "Database not available"
    
    pokemon_data = load_pokemon_data()
    added_pokemon = []
    invalid_pokemon = []
    
    for name in pokemon_names:
        name = name.strip()
        pokemon = find_pokemon_by_name(name, pokemon_data)
        
        if pokemon:
            added_pokemon.append(pokemon['name'])
        else:
            invalid_pokemon.append(name)
    
    if not added_pokemon:
        return f"Invalid Pokemon names: {', '.join(invalid_pokemon)}"
    
    try:
        async with db_pool.acquire() as conn:
            # Insert or update the collection
            await conn.execute('''
                INSERT INTO pokemon_collections (user_id, guild_id, pokemon_list, updated_at)
                VALUES ($1, $2, $3, NOW())
                ON CONFLICT (user_id, guild_id)
                DO UPDATE SET 
                    pokemon_list = array(SELECT DISTINCT unnest(pokemon_collections.pokemon_list || $3)),
                    updated_at = NOW()
            ''', user_id, guild_id, added_pokemon)
        
        result = f"Added to collection: {', '.join(added_pokemon)}"
        if invalid_pokemon:
            result += f"\nInvalid names: {', '.join(invalid_pokemon)}"
        
        return result
    
    except Exception as e:
        return f"Database error: {e}"

async def remove_pokemon_from_collection(user_id, guild_id, pokemon_names):
    """Remove Pokemon from user's collection"""
    if db_pool is None:
        return "Database not available"
    
    pokemon_data = load_pokemon_data()
    removed_pokemon = []
    not_found_pokemon = []
    
    for name in pokemon_names:
        name = name.strip()
        pokemon = find_pokemon_by_name(name, pokemon_data)
        
        if pokemon:
            removed_pokemon.append(pokemon['name'])
        else:
            not_found_pokemon.append(name)
    
    if not removed_pokemon:
        return f"Invalid Pokemon names: {', '.join(not_found_pokemon)}"
    
    try:
        async with db_pool.acquire() as conn:
            result = await conn.execute('''
                UPDATE pokemon_collections 
                SET pokemon_list = array(SELECT unnest(pokemon_list) EXCEPT SELECT unnest($3::text[])),
                    updated_at = NOW()
                WHERE user_id = $1 AND guild_id = $2
            ''', user_id, guild_id, removed_pokemon)
        
        if result.split()[-1] != '0':  # Check if rows were affected
            response = f"Removed from collection: {', '.join(removed_pokemon)}"
            if not_found_pokemon:
                response += f"\nInvalid names: {', '.join(not_found_pokemon)}"
            return response
        else:
            return "No Pokemon were removed (they might not be in your collection)"
    
    except Exception as e:
        return f"Database error: {e}"

async def clear_user_collection(user_id, guild_id):
    """Clear user's entire collection for the guild"""
    if db_pool is None:
        return "Database not available"
    
    try:
        async with db_pool.acquire() as conn:
            result = await conn.execute('''
                DELETE FROM pokemon_collections 
                WHERE user_id = $1 AND guild_id = $2
            ''', user_id, guild_id)
        
        if result.split()[-1] != '0':
            return "Collection cleared successfully"
        else:
            return "Your collection is already empty"
    
    except Exception as e:
        return f"Database error: {e}"

async def list_user_collection(user_id, guild_id):
    """List user's Pokemon collection for the guild"""
    if db_pool is None:
        return "Database not available"
    
    try:
        async with db_pool.acquire() as conn:
            row = await conn.fetchrow('''
                SELECT pokemon_list FROM pokemon_collections 
                WHERE user_id = $1 AND guild_id = $2
            ''', user_id, guild_id)
        
        if not row or not row['pokemon_list']:
            return "Your collection is empty"
        
        pokemon_list = sorted(row['pokemon_list'])
        
        # Split into chunks if too long
        if len(pokemon_list) <= 20:
            return f"Your collection ({len(pokemon_list)} Pokemon):\n{', '.join(pokemon_list)}"
        else:
            chunks = [pokemon_list[i:i+20] for i in range(0, len(pokemon_list), 20)]
            response = f"Your collection ({len(pokemon_list)} Pokemon):\n"
            for i, chunk in enumerate(chunks, 1):
                response += f"Page {i}: {', '.join(chunk)}\n"
            return response
    
    except Exception as e:
        return f"Database error: {e}"

async def get_collectors_for_pokemon(pokemon_name, guild_id):
    """Get all users who have collected this Pokemon in the given guild"""
    if db_pool is None:
        return []
    
    pokemon_data = load_pokemon_data()
    collectors = []
    
    try:
        async with db_pool.acquire() as conn:
            # Find all collections in this guild that contain this Pokemon
            rows = await conn.fetch('''
                SELECT user_id FROM pokemon_collections 
                WHERE guild_id = $1 AND $2 = ANY(pokemon_list)
            ''', guild_id, pokemon_name)
            
            collectors = [row['user_id'] for row in rows]
            
            # Check if this is a variant and also look for base form collectors
            target_pokemon = find_pokemon_by_name(pokemon_name, pokemon_data)
            if target_pokemon and target_pokemon.get('is_variant'):
                base_form = target_pokemon.get('variant_of')
                if base_form:
                    base_rows = await conn.fetch('''
                        SELECT user_id FROM pokemon_collections 
                        WHERE guild_id = $1 AND $2 = ANY(pokemon_list)
                    ''', guild_id, base_form)
                    
                    base_collectors = [row['user_id'] for row in base_rows]
                    collectors.extend(base_collectors)
                    collectors = list(set(collectors))  # Remove duplicates
    
    except Exception as e:
        print(f"Error getting collectors: {e}")
    
    return collectors
