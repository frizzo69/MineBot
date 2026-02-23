import discord
from discord.ext import commands
import aiohttp
import re
import io

class EmojiManager(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    async def fetch_image(self, url):
        """Downloads image bytes from a URL."""
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(url) as resp:
                    if resp.status == 200:
                        return await resp.read()
        except:
            return None
        return None

    @commands.command(name="upload_emoji", aliases=["stealemoji", "addemoji"])
    @commands.has_permissions(manage_emojis=True)
    async def upload_emoji(self, ctx, *, content: str):
        """
        Uploads emojis.
        - For Discord Emojis: Just paste them with spaces (e.g. :emoji1: :emoji2:)
        - For Links: Separate with semicolons (;)
        """
        if not ctx.guild:
            return await ctx.send("This command can only be used in a server.")

        # 1. FIND ALL DISCORD CUSTOM EMOJIS (Pattern: <a:name:id> or <:name:id>)
        # We extract them first so spaces don't break them.
        custom_emojis = re.findall(r'<a?:\w+:\d+>', content)

        # 2. REMOVE THE FOUND EMOJIS FROM CONTENT TO FIND LINKS
        # We replace them with empty string so we are left with just text/links
        content_without_emojis = re.sub(r'<a?:\w+:\d+>', '', content)

        # 3. SPLIT THE REST BY SEMICOLON (for links)
        potential_links = content_without_emojis.split(';')

        # Combine both lists (clean up empty strings/spaces)
        master_list = custom_emojis + [link.strip() for link in potential_links if link.strip()]
        
        if not master_list:
            return await ctx.send("❌ No emojis or links found!")

        count = 0
        msg = await ctx.send(f"🔄 Processing {len(master_list)} potential emoji(s)...")

        for item in master_list:
            name = None
            image_bytes = None

            # --- CASE A: Discord Custom Emoji ---
            # Regex match again to pull out ID and Name
            match = re.match(r"<(a?):(\w+):(\d+)>", item)
            if match:
                is_animated = bool(match.group(1))
                name = match.group(2)
                emoji_id = match.group(3)
                ext = "gif" if is_animated else "png"
                url = f"https://cdn.discordapp.com/emojis/{emoji_id}.{ext}"
                image_bytes = await self.fetch_image(url)

            # --- CASE B: URL Link ---
            elif item.startswith("http"):
                try:
                    # Guess name from file path
                    name = item.split("/")[-1].split(".")[0]
                    name = re.sub(r'\W+', '', name) or "emoji"
                    image_bytes = await self.fetch_image(item)
                except:
                    pass

            # --- UPLOAD LOGIC ---
            if image_bytes and name:
                try:
                    await ctx.guild.create_custom_emoji(name=name, image=image_bytes)
                    count += 1
                except discord.HTTPException as e:
                    # Often errors: "Maximum number of emojis reached" (30001) or "File too big" (50035)
                    if e.code == 30001:
                        return await ctx.send("❌ **Server Emoji Limit Reached!** Cannot add more.")
                    print(f"Failed {name}: {e}")
                except Exception as e:
                    print(f"Error {name}: {e}")

        await msg.edit(content=f"✅ Successfully uploaded **{count}** emoji(s)!")

    @commands.command(name="upload_sticker", aliases=["stealsticker","sticker"])
    @commands.has_permissions(manage_emojis=True)
    async def upload_sticker(self, ctx):
        """Steals a sticker from a reply or message attachment."""
        target_sticker = None

        if ctx.message.reference:
            ref_msg = await ctx.channel.fetch_message(ctx.message.reference.message_id)
            if ref_msg.stickers: target_sticker = ref_msg.stickers[0]
        elif ctx.message.stickers:
            target_sticker = ctx.message.stickers[0]

        if not target_sticker:
            return await ctx.send("❌ Reply to a sticker or send one with the command.")

        if target_sticker.format == discord.StickerFormatType.lottie:
            return await ctx.send("❌ Cannot steal Lottie (JSON) stickers.")

        image_bytes = await self.fetch_image(target_sticker.url)
        if image_bytes:
            try:
                file = discord.File(fp=io.BytesIO(image_bytes), filename="sticker.png")
                await ctx.guild.create_sticker(
                    name=target_sticker.name,
                    description="Steal",
                    emoji="🤖", 
                    file=file
                )
                await ctx.send(f"✅ Added sticker: **{target_sticker.name}**")
            except Exception as e:
                await ctx.send(f"❌ Error: {e}")

async def setup(bot):
    await bot.add_cog(EmojiManager(bot))
