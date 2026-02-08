import discord
import os
import asyncio
from discord.ext import commands

# 1. Setup Intents (Must be enabled in Developer Portal)
intents = discord.Intents.default()
intents.message_content = True 
intents.members = True

bot = commands.Bot(command_prefix="-", intents=intents)

# 3. Load Commands
async def load_extensions():
    # Create folder if it doesn't exist
    if not os.path.exists('./commands'):
        os.makedirs('./commands')

    # Load all .py files in the commands folder
    for filename in os.listdir('./commands'):
        if filename.endswith('.py'):
            try:
                await bot.load_extension(f'commands.{filename[:-3]}')
                print(f"✅ Loaded extension: {filename}")
            except Exception as e:
                print(f"❌ Failed to load {filename}: {e}")

@bot.event
async def on_ready():
    print(f'🤖 Bot Online: {bot.user} (ID: {bot.user.id})')
    print('------')

async def main():
    async with bot:
        await load_extensions()
        # Get token from Replit Secrets
        await bot.start(os.environ['TOKEN'])

if __name__ == '__main__':
    asyncio.run(main())
