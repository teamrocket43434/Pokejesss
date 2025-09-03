import os
import discord
from predict import Prediction  # uses your predict.py file

TOKEN = os.getenv("DISCORD_TOKEN")

intents = discord.Intents.all()
bot = discord.Client(intents=intents)

predictor = Prediction()

@bot.event
async def on_ready():
    print(f"✅ Logged in as {bot.user}")

@bot.event
async def on_message(message):
    print(f"📩 Saw message from {message.author}: {message.content}")

    if message.author == bot.user:
        return

    # 1) Test command
    if message.content.lower() == "!ping":
        await message.channel.send("🏓 Pong!")

    # 2) Manual predict command
    if message.content.startswith("!identify "):
        url = message.content.split(" ", 1)[1]
        await message.channel.send("🔍 Identifying Pokémon...")
        try:
            name, confidence = predictor.predict(url)
            name = name.replace("_", " ")  # ✅ Replace underscores with spaces
            await message.channel.send(
                f"{name}: {confidence}"
            )
        except Exception as e:
            await message.channel.send(f"❌ Error: {e}")

    # 3) Auto-detect Pokétwo spawns
    if message.author.id == 716390085896962058:  # Pokétwo user ID
        image_url = None

        if message.attachments:
            for attachment in message.attachments:
                if attachment.url.lower().endswith((".png", ".jpg", ".jpeg", ".webp")):
                    image_url = attachment.url

        if not image_url and message.embeds:
            embed = message.embeds[0]
            if embed.image and embed.image.url:
                image_url = embed.image.url

        if image_url:
            try:
                name, confidence = predictor.predict(image_url)
                name = name.replace("_", " ")  # ✅ Replace underscores with spaces
                await message.channel.send(
                    f"{name}: {confidence}"
                )
            except Exception as e:
                await message.channel.send(f"❌ Error: {e}")

bot.run(TOKEN)import os
import discord
from predict import Prediction  # uses your predict.py file

TOKEN = os.getenv("DISCORD_TOKEN")

intents = discord.Intents.all()
bot = discord.Client(intents=intents)

predictor = Prediction()

@bot.event
async def on_ready():
    print(f"✅ Logged in as {bot.user}")

@bot.event
async def on_message(message):
    print(f"📩 Saw message from {message.author}: {message.content}")

    if message.author == bot.user:
        return

    # 1) Test command
    if message.content.lower() == "!ping":
        await message.channel.send("🏓 Pong!")

    # 2) Manual predict command
    if message.content.startswith("!identify "):
        url = message.content.split(" ", 1)[1]
        await message.channel.send("🔍 Identifying Pokémon...")
        try:
            name, confidence = predictor.predict(url)
            name = name.replace("_", " ")  # ✅ Replace underscores with spaces
            await message.channel.send(
                f"{name}: {confidence}"
            )
        except Exception as e:
            await message.channel.send(f"❌ Error: {e}")

    # 3) Auto-detect Pokétwo spawns
    if message.author.id == 716390085896962058:  # Pokétwo user ID
        image_url = None

        if message.attachments:
            for attachment in message.attachments:
                if attachment.url.lower().endswith((".png", ".jpg", ".jpeg", ".webp")):
                    image_url = attachment.url

        if not image_url and message.embeds:
            embed = message.embeds[0]
            if embed.image and embed.image.url:
                image_url = embed.image.url

        if image_url:
            try:
                name, confidence = predictor.predict(image_url)
                name = name.replace("_", " ")  # ✅ Replace underscores with spaces
                await message.channel.send(
                    f"{name}: {confidence}"
                )
            except Exception as e:
                await message.channel.send(f"❌ Error: {e}")

bot.run(TOKEN)
