import discord
import os
import asyncio
from discord.ext import commands

intents = discord.Intents.default()
intents.message_content = True 
intents.members = True

bot = commands.Bot(command_prefix="-", intents=intents)

async def load_extensions():
    # Only try to load if folder exists
    if os.path.exists('./commands'):
        for filename in os.listdir('./commands'):
            if filename.endswith('.py'):
                try:
                    await bot.load_extension(f'commands.{filename[:-3]}')
                    print(f"✅ Loaded extension: {filename}")
                except Exception as e:
                    print(f"❌ Failed to load {filename}: {e}")
    else:
        print("📁 'commands' folder not found!")

@bot.event
async def on_ready():
    print(f'🤖 Bot Online: {bot.user}')

async def main():
    async with bot:
        await load_extensions()
        # Railway uses Variables instead of Secrets, but os.environ works for both
        token = os.getenv('TOKEN')
        if token is None:
            print("❌ Error: No TOKEN found in environment variables!")
            return
        await bot.start(token)

if __name__ == '__main__':
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        pass
