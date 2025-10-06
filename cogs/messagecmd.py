import discord
from discord import app_commands
from discord.ext import commands
import re
from typing import Optional

class MessageCommands(commands.Cog):
    """Message context menu commands for Pokemon identification"""

    def __init__(self, bot):
        self.bot = bot
        self.url_pattern = re.compile(
            r'http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\\(\\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+'
        )

        # Define context menu
        self.ctx_menu_identify = app_commands.ContextMenu(
            name="Identify Pokemon",
            callback=self.identify_pokemon_callback
        )

        # Add context menu to the bot's tree
        self.bot.tree.add_command(self.ctx_menu_identify)

    async def cog_unload(self):
        """Remove context menu when cog is unloaded"""
        self.bot.tree.remove_command(self.ctx_menu_identify.name, type=self.ctx_menu_identify.type)

    def extract_image_url(self, message: discord.Message) -> Optional[str]:
        """Extract image URL from message content or attachments"""
        # Check attachments first
        if message.attachments:
            for attachment in message.attachments:
                if any(attachment.filename.lower().endswith(ext) 
                       for ext in ['.png', '.jpg', '.jpeg', '.gif', '.webp']):
                    return attachment.url

        # Check embeds
        if message.embeds:
            for embed in message.embeds:
                if embed.image:
                    return embed.image.url
                if embed.thumbnail:
                    return embed.thumbnail.url

        # Check for URLs in message content
        urls = self.url_pattern.findall(message.content)
        for url in urls:
            if any(ext in url.lower() for ext in ['.png', '.jpg', '.jpeg', '.gif', '.webp']):
                return url

        return None

    async def identify_pokemon_callback(self, interaction: discord.Interaction, message: discord.Message):
        """Identify Pokemon from a message image (Right-click -> Apps -> Identify Pokemon)"""

        await interaction.response.defer(ephemeral=True)

        try:
            # Extract image URL from the message
            image_url = self.extract_image_url(message)

            if not image_url:
                await interaction.followup.send(
                    "❌ No Image Found - This message doesn't contain any images or supported image URLs.",
                    ephemeral=True
                )
                return

            # Check if predictor is available
            if not hasattr(self.bot, 'predictor') or self.bot.predictor is None:
                await interaction.followup.send(
                    "❌ Predictor Unavailable - The Pokemon predictor is not initialized. Please try again later.",
                    ephemeral=True
                )
                return

            # Check if HTTP session is available
            if not hasattr(self.bot, 'http_session') or self.bot.http_session is None:
                await interaction.followup.send(
                    "❌ Service Unavailable - HTTP session is not available. Please try again later.",
                    ephemeral=True
                )
                return

            # Make prediction
            try:
                pokemon_name, confidence = await self.bot.predictor.predict(
                    image_url, 
                    self.bot.http_session
                )

                # Format pokemon name (capitalize each word)
                formatted_name = pokemon_name.replace('_', ' ').title()

                # Send simple text response
                response = f"{formatted_name}: {confidence}"
                await interaction.followup.send(response, ephemeral=True)

            except ValueError as e:
                await interaction.followup.send(
                    f"❌ Image Error - Failed to process the image: {str(e)}",
                    ephemeral=True
                )

            except Exception as e:
                await interaction.followup.send(
                    f"❌ Prediction Error - An error occurred during prediction: {str(e)}",
                    ephemeral=True
                )

        except Exception as e:
            await interaction.followup.send(f"❌ An error occurred: {str(e)}", ephemeral=True)
            import traceback
            traceback.print_exc()


async def setup(bot):
    """Load the cog"""
    cog = MessageCommands(bot)
    await bot.add_cog(cog)

    # Sync commands globally
    try:
        synced = await bot.tree.sync()
        print(f"Message Commands: Synced {len(synced)} command(s)")
    except Exception as e:
        print(f"Message Commands: Failed to sync commands: {e}")
