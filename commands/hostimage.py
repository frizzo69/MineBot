import discord
from discord.ext import commands
import aiohttp

class ImageHost(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(name="hostimage", aliases=["uploadimg", "hostimg", "imgurl"])
    async def hostimage(self, ctx):
        """
        Uploads an image to Catbox.moe and returns a direct link.
        Works by attaching an image or replying to an image.
        """
        target_attachment = None

        # 1. Check if an image was attached to the command message
        if ctx.message.attachments:
            target_attachment = ctx.message.attachments[0]
            
        # 2. Check if the user replied to a message with an attachment
        elif ctx.message.reference:
            ref_msg = await ctx.channel.fetch_message(ctx.message.reference.message_id)
            if ref_msg.attachments:
                target_attachment = ref_msg.attachments[0]

        # Failsafe 1: Did we find any attachment at all?
        if not target_attachment:
            return await ctx.send("❌ Please attach an image or reply to a message containing an image.")

        # Failsafe 2: Is the attachment actually an image?
        # We check the content_type (e.g., 'image/png', 'image/jpeg')
        if not target_attachment.content_type or not target_attachment.content_type.startswith('image/'):
            return await ctx.send("❌ That file doesn't look like an image. Please provide a PNG, JPG, GIF, etc.")

        status_msg = await ctx.send("☁️ Uploading your image to the cloud...")

        try:
            # Download the image bytes directly from Discord
            image_bytes = await target_attachment.read()
            
            # Prepare the upload for Catbox.moe API
            async with aiohttp.ClientSession() as session:
                data = aiohttp.FormData()
                data.add_field('reqtype', 'fileupload')
                data.add_field('fileToUpload', image_bytes, filename=target_attachment.filename)

                # Send the POST request
                async with session.post('https://catbox.moe/user/api.php', data=data) as resp:
                    if resp.status == 200:
                        # The API returns the raw text URL if successful
                        hosted_url = await resp.text()
                        await status_msg.edit(content=f"✅ **Image successfully hosted!**\n🔗 {hosted_url}")
                    else:
                        await status_msg.edit(content="❌ Failed to host the image. The hosting API might be down.")
                        
        except Exception as e:
            await status_msg.edit(content=f"❌ Something went wrong: {e}")

async def setup(bot):
    await bot.add_cog(ImageHost(bot))
