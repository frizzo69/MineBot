import discord
from discord.ext import commands
import re

class EmojiURL(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(name="eurl", aliases=["emojiurl", "getemoji"])
    async def eurl(self, ctx, emoji: str = None):
        """Extracts the direct CDN URL of a custom emoji."""

        if not emoji:
            return await ctx.send("❌ **Usage:** `-eurl <custom_emoji>`")

        # Regex to find the ID and check if it's animated
        # Group 1: 'a' if animated, empty if static
        # Group 2: Emoji Name
        # Group 3: Emoji ID
        match = re.search(r'<(a?):(.+?):(\d+)>', emoji)

        if not match:
            return await ctx.send("❌ That doesn't look like a custom emoji! (Standard emojis like 👑 don't have URLs).")

        is_animated = match.group(1) == 'a'
        emoji_id = match.group(3)
        extension = "gif" if is_animated else "png"

        # Construct the high-resolution URL
        url = f"https://cdn.discordapp.com/emojis/{emoji_id}.{extension}?size=4096"

        # Create the embed
        embed = discord.Embed(
            title="Emoji URL Extracted",
            description=f"**Copy Link:**\n`{url}`",
            color=discord.Color.blue()
        )
        embed.set_image(url=url)
        embed.set_footer(text=f"Requested by {ctx.author.display_name}")

        await ctx.send(embed=embed)

    @eurl.error
    async def eurl_error(self, ctx, error):
        # Basic error handling for the command
        await ctx.send(f"⚠️ **An error occurred:** {str(error)}")

async def setup(bot):
    await bot.add_cog(EmojiURL(bot))
