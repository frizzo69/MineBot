import discord
from discord.ext import commands

class Lockdown(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(name="lock")
    @commands.has_permissions(manage_channels=True)
    async def lock(self, ctx, channel: discord.TextChannel = None):
        """
        Locks a channel by removing send_messages and add_reactions perms for everyone.
        Usage: -lock OR -lock #channel
        """
        # If no channel is mentioned, use the current one
        channel = channel or ctx.channel
        
        # Get the @everyone role
        overwrite = channel.overwrites_for(ctx.guild.default_role)
        
        # Check if already locked to avoid redundant API calls
        if overwrite.send_messages == False and overwrite.add_reactions == False:
            return await ctx.send(f"⚠️ {channel.mention} is already locked.")

        # Set permissions to False (None would reset to neutral, False is a hard block)
        overwrite.send_messages = False
        overwrite.add_reactions = False
        
        await channel.set_permissions(ctx.guild.default_role, overwrite=overwrite)
        await ctx.send(f"🔒 **{channel.mention} has been locked.** Everyone's send and reaction permissions removed.")

    @commands.command(name="unlock")
    @commands.has_permissions(manage_channels=True)
    async def unlock(self, ctx, channel: discord.TextChannel = None):
        """
        Unlocks a channel by resetting perms for everyone.
        Usage: -unlock OR -unlock #channel
        """
        channel = channel or ctx.channel
        
        overwrite = channel.overwrites_for(ctx.guild.default_role)
        
        # Resetting to None allows the role's base permissions to take over again
        overwrite.send_messages = None
        overwrite.add_reactions = None
        
        await channel.set_permissions(ctx.guild.default_role, overwrite=overwrite)
        await ctx.send(f"🔓 **{channel.mention} has been unlocked.** Permissions restored.")

async def setup(bot):
    await bot.add_cog(Lockdown(bot))
