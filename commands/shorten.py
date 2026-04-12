import discord
from discord.ext import commands
import aiohttp
import urllib.parse

# --- CONFIGURATION: ADD NEW SERVERS HERE ---
# Format: "key": ("API_URL", "Requires VPN?", "JSON_KEY_FOR_RESULT")
PROVIDERS = {
    "tinyurl": ("https://tinyurl.com/api-create.php?url={}", False, None),
    "is.gd": ("https://is.gd/create.php?format=json&url={}", True, "shorturl"),
}

class URLShortener(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(name="shorten", aliases=["urlshortener", "urlshortner"])
    async def shorten(self, ctx, url: str = None, server: str = "tinyurl"):
        """Shortens a URL. Shows a guide if no URL is provided."""
        
        # 1. USAGE GUIDE (Triggered if no URL is provided)
        if url is None:
            embed = discord.Embed(
                title="📖 URL Shortener Guide",
                description="Shorten long links using various free services.",
                color=discord.Color.blue()
            )
            embed.add_field(
                name="✅ Basic Usage", 
                value="`-shorten <url>`\n*Defaults to TinyURL (No VPN)*", 
                inline=False
            )
            embed.add_field(
                name="🌐 Choose a Server", 
                value="`-shorten <url> <server_name>`\n*Example: `-shorten google.com is.gd`*", 
                inline=False
            )
            embed.add_field(
                name="📋 List Servers", 
                value="Use `-shorteners` to see all available options.", 
                inline=False
            )
            embed.set_footer(text="Tip: You don't need to include http://, the bot adds it for you!")
            return await ctx.send(embed=embed)

        # 2. VALIDATE SERVER
        server = server.lower()
        if server not in PROVIDERS:
            return await ctx.send(f"❌ Invalid server! Use `-shorteners` to see valid options.")

        api_template, needs_vpn, json_key = PROVIDERS[server]
        
        if not url.startswith(("http://", "https://")):
            url = "https://" + url

        # URL encode to handle symbols in the original link
        safe_url = urllib.parse.quote(url, safe='')
        headers = {"User-Agent": "Mozilla/5.0"}
        msg = await ctx.send(f"🔗 Shortening via **{server}**...")

        try:
            async with aiohttp.ClientSession(headers=headers) as session:
                async with session.get(api_template.format(safe_url)) as resp:
                    if resp.status == 200:
                        if json_key: # Handle JSON (is.gd)
                            data = await resp.json(content_type=None)
                            short_link = data.get(json_key)
                            if not short_link:
                                err = data.get('errormessage', 'Unknown error')
                                return await msg.edit(content=f"❌ **{server} Error:** {err}")
                        else: # Handle Raw Text (tinyurl)
                            short_link = await resp.text()

                        vpn_note = "\n⚠️ *Note: This link may require a VPN in some regions.*" if needs_vpn else ""
                        await msg.edit(content=f"✅ **Link Shortened:**\n<{short_link}>{vpn_note}")
                    else:
                        await msg.edit(content=f"❌ API Error ({resp.status}). The server might be down.")
                        
        except Exception as e:
            await msg.edit(content=f"❌ Something went wrong: `{e}`")

    @commands.command(name="shorteners")
    async def shorteners(self, ctx):
        """Displays a list of all available shortening servers and their VPN status."""
        embed = discord.Embed(
            title="🔗 Available Shortening Servers",
            description="Use these names as the second argument in `-shorten`.",
            color=discord.Color.green()
        )
        
        for name, (_, vpn, _) in PROVIDERS.items():
            status = "🔴 Needs VPN" if vpn else "🟢 No VPN Needed"
            embed.add_field(name=name.capitalize(), value=status, inline=True)
            
        await ctx.send(embed=embed)

async def setup(bot):
    await bot.add_cog(URLShortener(bot))
