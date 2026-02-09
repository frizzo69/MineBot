import discord
from discord.ext import commands

class Utility(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(name="ping")
    async def ping(self, ctx):
        """Shows the bot's current latency."""
        # Rounds the latency to the nearest whole number
        latency = round(self.bot.latency * 1000)
        await ctx.send(f"Ping: {latency}ms")

async def setup(bot):
    await bot.add_cog(Utility(bot))
