import discord
from discord.ext import commands
import os

class Donate(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(name="donate", aliases=["support", "tip"])
    async def donate(self, ctx):
        """Displays donation information including Crypto, UPI, and a QR code."""
        
        # --- CONFIGURATION: REPLACE THESE WITH YOUR ACTUAL DETAILS ---
        upi_id = "your_upi_id@bank"
        btc_address = "bc1qzm774vruyrgggqv2wwgs0pr3qdwc5e03r88hts"
        eth_address = "0xA7C049eCaCC7df183b01ab5653B11C599aBE27ae"
        ltc_address = "ltc1qczgu6hl7xksc7ga62r222urvad6lek89jtj99l"
        
        # The exact name of your QR code file on your server (e.g., "qr.png", "donate.jpeg")
        # If it's in a specific folder, use "folder_name/qr.png"
        qr_image_path = "src/qr.png" 
        # -----------------------------------------------------------

        embed = discord.Embed(
            title="💖 Support the Project",
            description="If you'd like to support the bot and its development, you can donate using the methods below. Thank you!",
            color=discord.Color.gold() # A nice gold/yellow color
        )

        # Using backticks (`) makes the text copyable on mobile and stand out on desktop
        embed.add_field(name="🏦 UPI", value=f"`{upi_id}`", inline=False)
        embed.add_field(name="🪙 Bitcoin (BTC)", value=f"`{btc_address}`", inline=False)
        embed.add_field(name="🔷 Ethereum (ETH)", value=f"`{eth_address}`", inline=False)
        embed.add_field(name="🪨 Litecoin (LTC)", value=f"`{ltc_address}`", inline=False)

        # Check if the QR code file actually exists on the server
        if os.path.exists(qr_image_path):
            # Create a discord.File object
            file = discord.File(qr_image_path, filename="qr.png")
            # Attach it to the embed using the attachment:// protocol
            embed.set_image(url="attachment://src/qr.png")
            embed.set_footer(text="Scan the QR code above or copy an address.")
            
            # Send both the file and the embed
            await ctx.send(file=file, embed=embed)
        else:
            # Fallback if the image is missing (prevents the bot from crashing)
            embed.set_footer(text="⚠️ Note: QR Code image file not found on the server.")
            await ctx.send(embed=embed)

async def setup(bot):
    await bot.add_cog(Donate(bot))
