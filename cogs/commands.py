import discord
import time
import json
from discord.ext import commands
from cogs.collections import load_pokemon_data, find_pokemon_by_name, format_pokemon_prediction, get_collectors_for_pokemon

async def get_guild_ping_roles(guild_id):
    """Get the rare and regional ping roles for a guild"""
    from main import db
    
    if db is None:
        return None, None

    try:
        guild_settings = await db.guild_settings.find_one({"guild_id": guild_id})
        if guild_settings:
            return guild_settings.get('rare_role_id'), guild_settings.get('regional_role_id')
    except Exception as e:
        print(f"Error getting guild ping roles: {e}")

    return None, None

async def set_rare_role(guild_id, role_id):
    """Set the rare Pokemon ping role for a guild"""
    from main import db
    
    if db is None:
        return "Database not available"

    try:
        result = await db.guild_settings.update_one(
            {"guild_id": guild_id},
            {"$set": {"rare_role_id": role_id}},
            upsert=True
        )
        return "Rare role set successfully!"
    except Exception as e:
        print(f"Error setting rare role: {e}")
        return f"Database error: {str(e)[:100]}"

async def set_regional_role(guild_id, role_id):
    """Set the regional Pokemon ping role for a guild"""
    from main import db
    
    if db is None:
        return "Database not available
