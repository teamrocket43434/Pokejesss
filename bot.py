import os
import discord
import asyncio
from discord.ext import commands
from motor.motor_asyncio import AsyncIOMotorClient
from predict import Prediction

TOKEN = os.getenv("DISCORD_TOKEN")
MONGODB_URI = os.getenv("MONGODB_URI")

intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix="m!", intents=intents)

# Remove default help command to use custom one
bot.remove_command('help')

# Global variables
predictor = None
db_client = None
db = None

async def initialize_predictor():
    """Initialize the predictor asynchronously"""
    global predictor
    try:
        predictor = Prediction()
        print("Predictor initialized successfully")
    except Exception as e:
        print(f"Failed to initialize predictor: {e}")

async def initialize_database():
    """Initialize MongoDB connection"""
    global db_client, db
    try:
        if not MONGODB_URI:
            print("Warning: MONGODB_URI not set, collection features disabled")
            return

        print(f"Attempting to connect to MongoDB...")
        print(f"URI starts with: {MONGODB_URI[:30]}...")

        # Try different TLS configurations for Railway compatibility
        tls_configs = [
            # Config 1: Standard connection (let MongoDB handle TLS automatically)
            {
                "serverSelectionTimeoutMS": 5000,
                "connectTimeoutMS": 10000,
                "socketTimeoutMS": 20000,
                "maxPoolSize": 1
            },
            # Config 2: Explicit TLS with invalid certificates allowed
            {
                "tls": True,
                "tlsAllowInvalidCertificates": True,
                "serverSelectionTimeoutMS": 5000,
                "connectTimeoutMS": 10000,
                "socketTimeoutMS": 20000,
                "maxPoolSize": 1
            },
            # Config 3: TLS insecure mode
            {
                "tls": True,
                "tlsInsecure": True,
                "serverSelectionTimeoutMS": 5000,
                "connectTimeoutMS": 10000,
                "socketTimeoutMS": 20000,
                "maxPoolSize": 1
            }
        ]

        for i, config in enumerate(tls_configs, 1):
            try:
                print(f"Trying TLS configuration {i}: {list(config.keys())}")
                db_client = AsyncIOMotorClient(MONGODB_URI, **config)

                # Test the connection with shorter timeout
                print("Testing connection with ping...")
                await asyncio.wait_for(db_client.admin.command('ping'), timeout=5)

                db = db_client.pokemon_collector
                print(f"✅ Database initialized successfully with configuration {i}")
                print(f"Database object created: {db is not None}")
                return

            except asyncio.TimeoutError:
                print(f"❌ Config {i} failed: Connection timeout")
            except Exception as e:
                print(f"❌ Config {i} failed: {str(e)[:100]}...")

            # Clean up failed connection
            if 'db_client' in locals() and db_client:
                db_client.close()
            db_client = None
            db = None

        print("❌ All TLS configurations failed - database features will be disabled")

    except Exception as e:
        print(f"❌ Critical error in database initialization: {e}")
        db_client = None
        db = None

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

@bot.event
async def on_ready():
    print(f"Logged in as {bot.user}")
    if predictor is None:
        await initialize_predictor()
    if db is None:
        await initialize_database()

@bot.event
async def on_message(message):
    # Auto-detect Poketwo spawns
    if message.author.id == 716390085896962058:  # Poketwo user ID
        if message.embeds:
            embed = message.embeds[0]
            if embed.title:
                # Check for spawn embed titles
                if (embed.title == "A wild pokémon has appeared!" or 
                    (embed.title.endswith("A new wild pokémon has appeared!") and 
                     "fled." in embed.title)):

                    image_url = await get_image_url_from_message(message)

                    if image_url and predictor:
                        try:
                            name, confidence = predictor.predict(image_url)

                            if name and confidence:
                                # Add confidence threshold to avoid low-confidence predictions
                                confidence_str = str(confidence).rstrip('%')
                                try:
                                    confidence_value = float(confidence_str)
                                    if confidence_value >= 70.0:  # Only show if confidence >= 70%
                                        # Import here to avoid circular imports
                                        from cogs.collections import format_pokemon_prediction, get_collectors_for_pokemon
                                        from cogs.commands import get_pokemon_ping_info
                                        
                                        formatted_output = format_pokemon_prediction(name, confidence)

                                        # Get collectors for this Pokemon
                                        collectors = await get_collectors_for_pokemon(name, message.guild.id)

                                        if collectors:
                                            collector_mentions = " ".join([f"<@{user_id}>" for user_id in collectors])
                                            formatted_output += f"\nCollectors: {collector_mentions}"

                                        # Get ping info for rare/regional Pokemon
                                        ping_info = await get_pokemon_ping_info(name, message.guild.id)
                                        if ping_info:
                                            formatted_output += f"\n{ping_info}"

                                        await message.reply(formatted_output)
                                    else:
                                        print(f"Low confidence prediction skipped: {name} ({confidence})")
                                except ValueError:
                                    print(f"Could not parse confidence value: {confidence}")
                        except Exception as e:
                            print(f"Auto-detection error: {e}")

    await bot.process_commands(message)

@bot.event
async def on_message_edit(before, after):
    """Handle message edits - process commands on edited messages too"""
    if before.content != after.content:
        print(f"Message edited by {after.author}: '{before.content}' -> '{after.content}'")
        await bot.process_commands(after)

async def load_cogs():
    """Load all cogs"""
    try:
        await bot.load_extension('cogs.commands')
        await bot.load_extension('cogs.collections')
        print("All cogs loaded successfully")
    except Exception as e:
        print(f"Error loading cogs: {e}")

async def main():
    if not TOKEN:
        print("Error: DISCORD_TOKEN environment variable not set")
        return

    async with bot:
        await load_cogs()
        try:
            await bot.start(TOKEN)
        except discord.LoginFailure:
            print("Error: Invalid Discord token")
        except Exception as e:
            print(f"Error starting bot: {e}")

if __name__ == "__main__":
    asyncio.run(main())
