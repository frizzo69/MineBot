import discord
from discord.ext import commands
import asyncio

class Purge(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(name="purge", aliases=["clear"])
    @commands.has_permissions(manage_messages=True)
    async def purge(self, ctx, amount: str):
        """Purges messages in the current channel. Use '-purge 10' or '-purge all'."""
        
        if amount.lower() == "all":
            # Direct nuke, no confirmation
            deleted = await ctx.channel.purge(limit=None)
            await ctx.send(f"💥 **Nuked!** Deleted **{len(deleted)}** messages.", delete_after=5)
        
        else:
            try:
                num = int(amount)
                # Purge 'num' messages plus the command itself (+1)
                deleted = await ctx.channel.purge(limit=num + 1)
                
                # We subtract 1 so the user sees the number they actually requested
                await ctx.send(f"🧹 Deleted **{len(deleted) - 1}** messages.", delete_after=5)
            except ValueError:
                await ctx.send("❌ Invalid input. Use a number (e.g., `-purge 20`) or `-purge all`.")

async def setup(bot):
    await bot.add_cog(Purge(bot))
