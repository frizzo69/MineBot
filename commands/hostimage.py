import discord
from discord.ext import commands
import aiohttp
import io

# --- CONFIGURATION ---
# Format: "key": (API_URL, Field_Name, Info_Text)
HOST_PROVIDERS = {
    "catbox": ("https://catbox.moe/user/api.php", "fileToUpload", "✅ Permanent (unless deleted)"),
    "0x0": ("https://0x0.st", "file", "🕒 Temporary (depends on file size)"),
    "litterbox": ("https://litterbox.catbox.moe/resources/internals/api.php", "fileToUpload", "⌛ Temporary (24h default)"),
    "pomf2": ("https://pomf2.sh/api/upload", "files[]", "✅ Permanent")
}

class ImageHost(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(name="hostimage", aliases=["uploadimg", "hostimg", "imgurl"])
    async def hostimage(self, ctx, provider: str = "catbox"):
        """
        Hosts an image.
        Usage: -hostimg [provider] (Reply to or attach an image)
        """
        provider = provider.lower()
        if provider not in HOST_PROVIDERS:
            return await ctx.send(f"❌ Invalid provider. Use `-imgservers` to see the list.")

        target = None
        # Check attachments in the current message
        if ctx.message.attachments:
            target = ctx.message.attachments[0]
        # Check attachments in the replied-to message
        elif ctx.message.reference:
            ref = await ctx.channel.fetch_message(ctx.message.reference.message_id)
            if ref.attachments:
                target = ref.attachments[0]

        # Failsafe: check if it exists and is an image
        if not target or not target.content_type or not target.content_type.startswith('image/'):
            return await ctx.send("❌ Please attach or reply to a valid **image** file.")

        msg = await ctx.send(f"☁️ Uploading to **{provider}**...")

        api_url, field_name, _ = HOST_PROVIDERS[provider]
        headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}

        try:
            img_bytes = await target.read()
            async with aiohttp.ClientSession(headers=headers) as session:
                data = aiohttp.FormData()
                
                # Special handling for different API formats
                if provider in ["catbox", "litterbox"]:
                    data.add_field('reqtype', 'fileupload')
                    if provider == "litterbox":
                        data.add_field('time', '24h') # Options: 1h, 12h, 24h, 72h
                
                data.add_field(field_name, img_bytes, filename=target.filename)

                async with session.post(api_url, data=data) as resp:
                    result = await resp.text()
                    
                    if resp.status == 200:
                        # Pomf2 returns JSON, others return raw text
                        if provider == "pomf2":
                            import json
                            resp_json = json.loads(result)
                            url = resp_json['files'][0]['url']
                        else:
                            url = result.strip()
                        
                        await msg.edit(content=f"✅ **Hosted via {provider}:**\n{url}")
                    else:
                        await msg.edit(content=f"❌ **{provider}** failed (Status: {resp.status}).\nTry `-hostimg 0x0` or `-hostimg pomf2`.")

        except Exception as e:
            await msg.edit(content=f"❌ Error during upload: `{e}`")

    @commands.command(name="imgservers", aliases=["hostingservers", "imgproviders"])
    async def imgservers(self, ctx):
        """Lists all available image hosting servers."""
        embed = discord.Embed(
            title="🖼️ Image Hosting Providers",
            description="Use these names with `-hostimg <name>`",
            color=discord.Color.purple()
        )
        
        for name, (_, _, info) in HOST_PROVIDERS.items():
            embed.add_field(name=name.capitalize(), value=info, inline=False)
        
        embed.set_footer(text="Catbox is recommended for permanent links.")
        await ctx.send(embed=embed)

async def setup(bot):
    await bot.add_cog(ImageHost(bot))
