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
        return "Database not available"

    try:
        result = await db.guild_settings.update_one(
            {"guild_id": guild_id},
            {"$set": {"regional_role_id": role_id}},
            upsert=True
        )
        return "Regional role set successfully!"
    except Exception as e:
        print(f"Error setting regional role: {e}")
        return f"Database error: {str(e)[:100]}"

async def get_pokemon_ping_info(pokemon_name, guild_id):
    """Get ping information for a Pokemon based on its rarity"""
    from main import db
    
    if db is None:
        return None

    pokemon_data = load_pokemon_data()
    pokemon = find_pokemon_by_name(pokemon_name, pokemon_data)

    if not pokemon:
        return None

    rarity = pokemon.get('rarity')
    if not rarity:
        return None

    rare_role_id, regional_role_id = await get_guild_ping_roles(guild_id)

    if rarity == "rare" and rare_role_id:
        return f"Rare Ping: <@&{rare_role_id}>"
    elif rarity == "regional" and regional_role_id:
        return f"Regional Ping: <@&{regional_role_id}>"

    return None

async def get_image_url_from_message(message):
    """Extract image URL from message attachments or embeds"""
    image_url = None

    # Check attachments first
    if message.attachments:
        for attachment in message.attachments:
            if any(attachment.url.lower().endswith(ext) for ext in [".png", ".jpg", ".jpeg", ".webp", ".gif"]):
                image_url = attachment.url
                break

    # Check embeds if no attachment found
    if not image_url and message.embeds:
        embed = message.embeds[0]
        if embed.image and embed.image.url:
            image_url = embed.image.url
        elif embed.thumbnail and embed.thumbnail.url:
            image_url = embed.thumbnail.url

    return image_url

class Commands(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(name='help')
    async def help_command(self, ctx):
        """Show help information"""
        embed = discord.Embed(
            title="🤖 Pokemon Helper Bot Commands",
            description="Here are all the available commands organized by category:",
            color=0x3498db
        )

        embed.add_field(
            name="🔧 Basic Commands",
            value=(
                "`m!ping` - Check bot latency and response time\n"
                "`m!help` - Show this help message"
            ),
            inline=False
        )

        embed.add_field(
            name="🔍 Prediction Commands", 
            value=(
                "`m!predict <image_url>` - Predict Pokemon from image URL\n"
                "`m!predict` (reply to image) - Predict Pokemon from replied image\n"
                "🤖 Auto-detection works on Poketwo spawns!"
            ),
            inline=False
        )

        embed.add_field(
            name="📚 Collection Management",
            value=(
                "`m!cl add <pokemon1, pokemon2, ...>` - Add Pokemons to your collection\n"
                "`m!cl remove <pokemon1, pokemon2, ...>` - Remove Pokemons from collection\n"
                "`m!cl list` - View your collection (with pagination)\n"
                "`m!cl clear` - Clear your entire collection"
            ),
            inline=False
        )

        embed.add_field(
            name="😴 AFK System",
            value=(
                "`m!afk` - Toggle your AFK status (with interactive button)\n"
                "AFK users won't be pinged when their Pokemon spawn"
            ),
            inline=False
        )

        embed.add_field(
            name="👑 Admin Commands",
            value=(
                "`m!rare-role @role` - Set role to ping for rare Pokemon\n"
                "`m!regional-role @role` - Set role to ping for regional Pokemon\n"
                "*Requires Administrator permission*"
            ),
            inline=False
        )

        embed.add_field(
            name="✨ Features",
            value=(
                "• Automatic Pokemon detection on Poketwo spawns\n"
                "• Collector pinging (mentions users who have that Pokemon)\n"
                "• Rare/Regional Pokemon role pinging\n"
                "• Gender variant support\n"
                "• Multi-language Pokemon name support\n"
                "• Commands work with message edits!"
            ),
            inline=False
        )

        embed.set_footer(text="Bot created for Pokemon collection management | Use commands with 'm!' prefix")

        await ctx.send(embed=embed)

    @commands.command(name='ping')
    async def ping(self, ctx):
        """Check bot latency"""
        start_time = time.time()

        # Send initial message
        sent_message = await ctx.send("🏓 Pinging...")

        # Calculate latency
        end_time = time.time()
        message_latency = round((end_time - start_time) * 1000, 2)  # Convert to milliseconds
        websocket_latency = round(self.bot.latency * 1000, 2)  # Bot's websocket latency in ms

        # Edit message with actual ping info
        embed = discord.Embed(title="🏓 Pong!", color=0x00ff00)
        embed.add_field(name="Message Latency", value=f"{message_latency}ms", inline=True)
        embed.add_field(name="WebSocket Latency", value=f"{websocket_latency}ms", inline=True)

        # Add status indicator based on latency
        if websocket_latency < 100:
            embed.add_field(name="Status", value="🟢 Excellent", inline=True)
        elif websocket_latency < 200:
            embed.add_field(name="Status", value="🟡 Good", inline=True)
        elif websocket_latency < 500:
            embed.add_field(name="Status", value="🟠 Fair", inline=True)
        else:
            embed.add_field(name="Status", value="🔴 Poor", inline=True)

        await sent_message.edit(content="", embed=embed)

    @commands.command(name='predict')
    async def predict(self, ctx, image_url: str = None):
        """Predict Pokemon from image URL or replied message"""
        from main import predictor
        
        if predictor is None:
            await ctx.send("Predictor is not available. Please try again later.")
            return

        # If no URL provided, check if replying to a message with image
        if not image_url and ctx.message.reference:
            try:
                replied_message = await ctx.channel.fetch_message(ctx.message.reference.message_id)
                image_url = await get_image_url_from_message(replied_message)
            except discord.NotFound:
                await ctx.send("Could not find the replied message.")
                return
            except discord.Forbidden:
                await ctx.send("I don't have permission to access that message.")
                return
            except Exception as e:
                await ctx.send(f"Error fetching replied message: {str(e)[:100]}")
                return

        # If still no image URL found
        if not image_url:
            await ctx.send("Please provide an image URL after `m!predict` or reply to a message with an image.")
            return

        try:
            name, confidence = predictor.predict(image_url)
            if name and confidence:
                formatted_output = format_pokemon_prediction(name, confidence)

                # Get collectors for this Pokemon
                collectors = await get_collectors_for_pokemon(name, ctx.guild.id)

                if collectors:
                    collector_mentions = " ".join([f"<@{user_id}>" for user_id in collectors])
                    formatted_output += f"\nCollectors: {collector_mentions}"

                # Get ping info for rare/regional Pokemon
                ping_info = await get_pokemon_ping_info(name, ctx.guild.id)
                if ping_info:
                    formatted_output += f"\n{ping_info}"

                await ctx.send(formatted_output)
            else:
                await ctx.send("Could not predict Pokemon from the provided image.")
        except Exception as e:
            print(f"Prediction error: {e}")
            await ctx.send(f"Error: {str(e)[:100]}")

    @commands.command(name='rare-role')
    @commands.has_permissions(administrator=True)
    async def set_rare_role_command(self, ctx, role: discord.Role):
        """Set the role to ping for rare Pokemon spawns"""
        result = await set_rare_role(ctx.guild.id, role.id)
        await ctx.send(result)

    @set_rare_role_command.error
    async def rare_role_error(self, ctx, error):
        if isinstance(error, commands.MissingPermissions):
            await ctx.send("You need administrator permissions to use this command.")
        elif isinstance(error, commands.BadArgument):
            await ctx.send("Please mention a valid role or provide a role ID.\nUsage: `m!rare-role @role`")

    @commands.command(name='regional-role')
    @commands.has_permissions(administrator=True)
    async def set_regional_role_command(self, ctx, role: discord.Role):
        """Set the role to ping for regional Pokemon spawns"""
        result = await set_regional_role(ctx.guild.id, role.id)
        await ctx.send(result)

    @set_regional_role_command.error
    async def regional_role_error(self, ctx, error):
        if isinstance(error, commands.MissingPermissions):
            await ctx.send("You need administrator permissions to use this command.")
        elif isinstance(error, commands.BadArgument):
            await ctx.send("Please mention a valid role or provide a role ID.\nUsage: `m!regional-role @role`")

async def setup(bot):
    await bot.add_cog(Commands(bot))
