import discord
import time
from discord.ext import commands


class HelpDropdownSelect(discord.ui.Select):
    def __init__(self, embeds):
        self.embeds = embeds

        # Define dropdown options
        options = [
            discord.SelectOption(
                label=" Overview & Basic Commands",
                description="Basic commands, ping, and Pokemon prediction",
                emoji="🏠",
                value="overview"
            ),
            discord.SelectOption(
                label=" Collection Management",
                description="Manage your Pokemon collection and get notified",
                emoji="📚",
                value="collection"
            ),
            discord.SelectOption(
                label=" Shiny Hunt System", 
                description="Hunt for specific shiny Pokemon",
                emoji="✨",
                value="shiny"
            ),
            discord.SelectOption(
                label=" AFK & Notifications",
                description="Control when you receive pings",
                emoji="😴", 
                value="afk"
            ),
            discord.SelectOption(
                label=" Starboard System",
                description="Showcase rare catches automatically",
                emoji="⭐",
                value="starboard"
            ),
            discord.SelectOption(
                label=" Admin Commands",
                description="Server management for administrators",
                emoji="👑",
                value="admin"
            ),
            discord.SelectOption(
                label=" Features Overview",
                description="All bot features and capabilities",
                emoji="🎯",
                value="features"
            )
        ]

        super().__init__(
            placeholder="📋 Choose a help category...",
            min_values=1,
            max_values=1,
            options=options
        )

    async def callback(self, interaction: discord.Interaction):
        # Map selection values to embed indices
        embed_map = {
            "overview": 0,
            "collection": 1, 
            "shiny": 2,
            "afk": 3,
            "starboard": 4,
            "admin": 5,
            "features": 6
        }

        selected_page = embed_map.get(self.values[0], 0)
        embed = self.embeds[selected_page]

        # Update footer with current selection
        category_names = {
            "overview": "Overview & Basic Commands",
            "collection": "Collection Management", 
            "shiny": "Shiny Hunt System",
            "afk": "AFK & Notifications",
            "starboard": "Starboard System",
            "admin": "Admin Commands", 
            "features": "Features Overview"
        }

        category_name = category_names.get(self.values[0], "Overview")
        embed.set_footer(text=f"Showing: {category_name} | Bot created for Pokemon collection management")

        await interaction.response.edit_message(embed=embed, view=self.view)


class HelpView(discord.ui.View):
    def __init__(self, embeds):
        super().__init__(timeout=300)  # 5 minutes timeout
        self.embeds = embeds

        # Add the dropdown select menu
        self.dropdown = HelpDropdownSelect(embeds)
        self.add_item(self.dropdown)

    @discord.ui.button(label='🏠 Home', style=discord.ButtonStyle.green, row=1)
    async def home_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        embed = self.embeds[0]  # First embed (overview)
        embed.set_footer(text="Showing: Overview & Basic Commands | Bot created for Pokemon collection management")

        # Reset dropdown to placeholder
        self.dropdown.placeholder = "📋 Choose a help category..."

        await interaction.response.edit_message(embed=embed, view=self)


class HelpCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(name="help")
    async def help_command(self, ctx):
        """Show help message with all bot commands organized with dropdown menu"""

        # Page 1: Overview and Basic Commands
        embed1 = discord.Embed(
            title="🤖 Pokemon Helper Bot - Command Guide",
            description="Welcome to the Pokemon Helper Bot! This bot helps you manage Pokemon collections, hunt for shinies, and provides automatic Pokemon detection.\n\n**Navigation:** Use the dropdown menu below to browse through different command categories.",
            color=0xf4e5ba
        )

        embed1.add_field(
            name="🔧 Basic Commands",
            value=(
                "`m!ping` - Check bot latency and response time\n"
                "`m!help` - Show this help message\n"
                "`m!serverpage` - View server settings (roles, starboard channel)"
            ),
            inline=False
        )

        embed1.add_field(
            name="🔍 Pokemon Prediction",
            value=(
                "`m!predict <image_url>` - Predict Pokemon from image URL\n"
                "`m!predict` (reply to image) - Predict Pokemon from replied image\n"
                "🤖 **Auto-detection:** Automatically identifies Poketwo spawns!"
            ),
            inline=False
        )

        # Page 2: Collection Management
        embed2 = discord.Embed(
            title="📚 Collection Management Commands",
            description="Manage your Pokemon collection and get notified when your Pokemon spawn!",
            color=0xf4e5ba
        )

        embed2.add_field(
            name="📚 Collection Commands",
            value=(
                "`m!cl add <pokemon1, pokemon2, ...>` - Add Pokemon to your collection\n"
                "`m!cl remove <pokemon1, pokemon2, ...>` - Remove Pokemon from collection\n"
                "`m!cl list` - View your collection (with pagination)\n"
                "`m!cl clear` - Clear your entire collection"
            ),
            inline=False
        )

        embed2.add_field(
            name="📚 How Collection Works",
            value=(
                "• Add Pokemon you want to be notified about\n"
                "• When those Pokemon spawn, you'll be mentioned\n"
                "• Perfect for completing your Pokedex\n"
                "• Works with Pokemon name variations and forms"
            ),
            inline=False
        )

        # Page 3: Shiny Hunt System
        embed3 = discord.Embed(
            title="✨ Shiny Hunt System",
            description="Hunt for specific shiny Pokemon and get notified when they spawn!",
            color=0xf4e5ba
        )

        embed3.add_field(
            name="✨ Shiny Hunt Commands",
            value=(
                "`m!sh <pokemon>` - Set Pokemon to hunt (only one at a time)\n"
                "`m!sh` - Check what Pokemon you're currently hunting\n"
                "`m!sh clear` or `m!sh none` - Stop hunting"
            ),
            inline=False
        )

        embed3.add_field(
            name="✨ How Shiny Hunting Works",
            value=(
                "• Set one Pokemon to actively hunt for\n"
                "• Get pinged when that Pokemon spawns\n"
                "• Other hunters will see your name when the Pokemon spawns\n"
                "• Great for coordinated shiny hunting with friends"
            ),
            inline=False
        )

        # Page 4: AFK System
        embed4 = discord.Embed(
            title="😴 AFK & Notification System",
            description="Control when you receive pings and notifications from the bot.",
            color=0xf4e5ba
        )

        embed4.add_field(
            name="😴 AFK Commands",
            value=(
                "`m!afk` - Toggle AFK status with interactive buttons\n"
                "`m!rareping` - Toggle rare Pokemon pings (if available)"
            ),
            inline=False
        )

        embed4.add_field(
            name="😴 AFK Types Explained",
            value=(
                "**Collection AFK:** Won't be pinged when your collected Pokemon spawn\n"
                "**Shiny Hunt AFK:** Your ID shows but won't be pinged when hunting Pokemon spawn\n"
                "• Use buttons in `m!afk` to toggle each individually\n"
                "• Perfect for when you're away but want others to see you're hunting"
            ),
            inline=False
        )

        # Page 5: Starboard System
        embed5 = discord.Embed(
            title="⭐ Starboard System",
            description="Automatically showcase rare catches, shinies, and high IV Pokemon Including Eggs!",
            color=0xf4e5ba
        )

        embed5.add_field(
            name="⭐ Starboard Commands (Admin Only)",
            value=(
                "`m!starboard-channel <#channel>` - Set server starboard channel\n"
                "`m!globalstarboard-channel <#channel>` - Set global starboard (Owner only)\n"
                "`m!manualcheck` (reply to catch or id) - Manually check a catch message\n"
                "`m!eggcheck` (reply to catch or id) - Manually check a catch message for egg related"
            ),
            inline=False
        )

        embed5.add_field(
            name="⭐ What Gets Posted to Starboard",
            value=(
                "✨ **Shiny Pokemon** - All shiny catches including eggs\n"
                "🎯 **Gigantamax Pokemon** - All Gigantamax catches including eggs\n"
                "📈 **High IV Pokemon** - 90% IV or higher including eggs\n"
                "📉 **Low IV Pokemon** - 10% IV or lower including eggs\n"
                "• Automatic detection from Poketwo catch messages\n"
                "• Includes Pokemon images, stats, and jump-to-message links"
            ),
            inline=False
        )

        # Page 6: Admin Commands
        embed6 = discord.Embed(
            title="👑 Admin Commands",
            description="Server management commands for administrators.",
            color=0xf4e5ba
        )

        embed6.add_field(
            name="👑 Role Management",
            value=(
                "`m!rare-role @role` - Set role to ping for rare Pokemon\n"
                "`m!regional-role @role` - Set role to ping for regional Pokemon\n"
                "`m!starboard-channel <#channel>` - Set starboard channel\n"
                "*Requires Administrator permission*"
            ),
            inline=False
        )

        embed6.add_field(
            name="👑 Server Settings",
            value=(
                "`m!serverpage` - View all server settings\n"
                "• Shows rare role, regional role, and starboard channel\n"
                "• Displays guild ID for reference\n"
                "• Available to all users"
            ),
            inline=False
        )

        # Page 7: Features Overview
        embed7 = discord.Embed(
            title="🎯 Bot Features & Capabilities",
            description="Comprehensive overview of all bot features and how they work together.",
            color=0xf4e5ba
        )

        embed7.add_field(
            name="🎯 Automatic Features",
            value=(
                "• **Auto Pokemon Detection** - Identifies Poketwo spawns automatically\n"
                "• **Shiny Hunter Pinging** - Mentions users hunting that Pokemon\n"
                "• **Collector Pinging** - Mentions users who have that Pokemon in collection\n"
                "• **Starboard Auto-posting** - Rare catches posted automatically\n"
                "• **Command Edit Support** - Commands work even with message edits"
            ),
            inline=False
        )

        embed7.add_field(
            name="🎯 Advanced Support",
            value=(
                "• **Gender Variants** - Supports male/female Pokemon forms\n"
                "• **Regional Forms** - Handles Alolan, Galarian, etc.\n"
                "• **Gigantamax Support** - Special handling for G-Max Pokemon\n"
                "• **Multi-language** - Works with various Pokemon name formats\n"
                "• **High Performance** - Optimized database queries and caching"
            ),
            inline=False
        )

        # Create list of all embeds
        embeds = [embed1, embed2, embed3, embed4, embed5, embed6, embed7]

        # Set footer for first embed
        embeds[0].set_footer(text="Showing: Overview & Basic Commands | Bot created for Pokemon collection management")

        # Create view with dropdown menu
        view = HelpView(embeds)

        await ctx.reply(embed=embeds[0], view=view, mention_author=False)

    @commands.command(name="ping")
    async def ping_command(self, ctx):
        """Check bot latency and response time"""
        start_time = time.time()

        # Send initial message
        sent_message = await ctx.reply("🏓 Pinging...", mention_author=False)

        # Calculate latency
        end_time = time.time()
        message_latency = round((end_time - start_time) * 1000, 2)  # Convert to milliseconds
        websocket_latency = round(self.bot.latency * 1000, 2)  # Bot's websocket latency in ms

        # Edit message with actual ping info
        embed = discord.Embed(title="🏓 Pong!", color=0xf4e5ba)
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


async def setup(bot):
    await bot.add_cog(HelpCog(bot))
