import discord
from discord.ext import commands
import json
import os

AR_FILE = "autoroles.json"

# --- Database Helper Functions ---
def get_ar_data():
    if not os.path.exists(AR_FILE):
        return {}
    try:
        with open(AR_FILE, "r") as f:
            return json.load(f)
    except:
        return {}

def save_ar_data(data):
    with open(AR_FILE, "w") as f:
        json.dump(data, f, indent=4)

class AutoRole(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    # --- 1. The Event Listener (Triggers when someone joins) ---
    @commands.Cog.listener()
    async def on_member_join(self, member):
        # Ignore bots joining
        if member.bot: return

        data = get_ar_data()
        guild_id = str(member.guild.id)

        # If this server has autoroles set up
        if guild_id in data and data[guild_id]:
            roles_to_add = []
            
            # Convert saved IDs back into actual Discord Role objects
            for role_id in data[guild_id]:
                role = member.guild.get_role(role_id)
                if role:
                    roles_to_add.append(role)

            if roles_to_add:
                try:
                    await member.add_roles(*roles_to_add, reason="Autorole")
                except discord.Forbidden:
                    print(f"Missing permissions to assign roles in {member.guild.name}")
                except Exception as e:
                    print(f"Autorole Error in {member.guild.name}: {e}")

    # --- 2. The Command Group ---
    @commands.group(name="autorole", aliases=["ar"], invoke_without_command=True)
    @commands.has_permissions(manage_roles=True)
    async def autorole(self, ctx):
        """Base command. Shows usage if no subcommand is given."""
        embed = discord.Embed(title="⚙️ Autorole Settings", color=discord.Color.blue())
        embed.add_field(name="Add a role", value="`-ar add @role`", inline=False)
        embed.add_field(name="Remove a role", value="`-ar remove @role`", inline=False)
        embed.add_field(name="List roles", value="`-ar list`", inline=False)
        await ctx.send(embed=embed)

    @autorole.command(name="add")
    @commands.has_permissions(manage_roles=True)
    async def ar_add(self, ctx, role: discord.Role):
        """Adds a role to the autorole list."""
        # Safety check: Can the bot actually assign this role?
        if role.position >= ctx.guild.me.top_role.position:
            return await ctx.send(f"❌ I cannot assign {role.mention} because it is higher than or equal to my highest role.")
        
        # Safety check: Is it the @everyone role?
        if role.is_default():
            return await ctx.send("❌ You cannot add the @everyone role to autorole.")

        data = get_ar_data()
        guild_id = str(ctx.guild.id)

        if guild_id not in data:
            data[guild_id] = []

        if role.id in data[guild_id]:
            return await ctx.send(f"⚠️ {role.mention} is already in the autorole list.")

        data[guild_id].append(role.id)
        save_ar_data(data)
        
        await ctx.send(f"✅ {role.mention} will now be given to new members.")

    @autorole.command(name="remove")
    @commands.has_permissions(manage_roles=True)
    async def ar_remove(self, ctx, role: discord.Role):
        """Removes a role from the autorole list."""
        data = get_ar_data()
        guild_id = str(ctx.guild.id)

        if guild_id in data and role.id in data[guild_id]:
            data[guild_id].remove(role.id)
            save_ar_data(data)
            await ctx.send(f"❌ {role.mention} has been removed from the autorole list.")
        else:
            await ctx.send(f"⚠️ {role.mention} is not in the autorole list.")

    @autorole.command(name="list")
    @commands.has_permissions(manage_roles=True)
    async def ar_list(self, ctx):
        """Lists all active autoroles for this server."""
        data = get_ar_data()
        guild_id = str(ctx.guild.id)

        if guild_id not in data or not data[guild_id]:
            return await ctx.send("📋 There are currently no autoroles set up for this server.")

        role_mentions = []
        clean_up_needed = False

        for role_id in data[guild_id]:
            role = ctx.guild.get_role(role_id)
            if role:
                role_mentions.append(role.mention)
            else:
                # If a role was deleted from the server but is still in JSON
                role_mentions.append(f"`Deleted Role (ID: {role_id})`")
                clean_up_needed = True

        embed = discord.Embed(
            title=f"📋 Autoroles for {ctx.guild.name}",
            description="\n".join(role_mentions),
            color=discord.Color.green()
        )
        
        if clean_up_needed:
            embed.set_footer(text="Tip: You have deleted roles in your list. Use -ar remove on their IDs to clean this up.")

        await ctx.send(embed=embed)

async def setup(bot):
    await bot.add_cog(AutoRole(bot))
