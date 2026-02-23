import discord
from discord.ext import commands

class ClearUser(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(name="clearuser")
    @commands.has_permissions(manage_messages=True)
    async def clearuser(self, ctx, user: discord.User):
        """Removes all messages from a specific user across the entire server."""
        status_msg = await ctx.send(f"🧹 Scanning the server for messages from **{user}**... this may take a moment.")
        
        deleted_count = 0
        for channel in ctx.guild.text_channels:
            try:
                # Purge with a check for the user's ID
                deleted = await channel.purge(limit=None, check=lambda m: m.author.id == user.id)
                deleted_count += len(deleted)
            except discord.Forbidden:
                continue # Skip channels where the bot lacks 'Manage Messages'
            except Exception as e:
                print(f"Error in {channel.name}: {e}")

        await status_msg.edit(content=f"✅ Success! Deleted **{deleted_count}** messages from **{user}** server-wide.")

async def setup(bot):
    await bot.add_cog(ClearUser(bot))
