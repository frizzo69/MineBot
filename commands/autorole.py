import discord
from discord.ext import commands
import json
import os

AR_FILE = "autoroles.json"

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

    @commands.Cog.listener()
    async def on_member_join(self, member):
        if member.bot: return
        data = get_ar_data()
        guild_id = str(member.guild.id)

        if guild_id in data and data[guild_id]:
            roles_to_add = []
            for role_id in data[guild_id]:
                role = member.guild.get_role(role_id)
                if role:
                    roles_to_add.append(role)

            if roles_to_add:
                try:
                    await member.add_roles(*roles_to_add, reason="Autorole")
                except Exception as e:
                    print(f"Autorole Error in {member.guild.name}: {e}")

    @commands.group(name="autorole", aliases=["ar"], invoke_without_command=True)
    @commands.has_permissions(manage_roles=True)
    async def autorole(self, ctx):
        embed = discord.Embed(title="⚙️ Autorole Settings", color=discord.Color.blue())
        embed.add_field(name="Add a role", value="`-ar add @role`", inline=False)
        embed.add_field(name="Remove a role", value="`-ar remove @role`", inline=False)
        embed.add_field(name="List roles", value="`-ar list`", inline=False)
        await ctx.send(embed=embed)

    @autorole.command(name="add")
    @commands.has_permissions(manage_roles=True)
    async def ar_add(self, ctx, role: discord.Role):
        if role.position >= ctx.guild.me.top_role.position:
            return await ctx.send(f"❌ I cannot assign **{role.name}** because it is higher than my own role.")
        
        if role.is_default():
            return await ctx.send("❌ You cannot add the @everyone role.")

        data = get_ar_data()
        guild_id = str(ctx.guild.id)

        if guild_id not in data:
            data[guild_id] = []

        if role.id in data[guild_id]:
            return await ctx.send(f"⚠️ **{role.name}** is already in the list.")

        data[guild_id].append(role.id)
        save_ar_data(data)
        await ctx.send(f"✅ **{role.name}** will now be given to new members.")

    @autorole.command(name="remove")
    @commands.has_permissions(manage_roles=True)
    async def ar_remove(self, ctx, role: discord.Role):
        data = get_ar_data()
        guild_id = str(ctx.guild.id)

        if guild_id in data and role.id in data[guild_id]:
            data[guild_id].remove(role.id)
            save_ar_data(data)
            await ctx.send(f"❌ **{role.name}** removed from autorole.")
        else:
            await ctx.send(f"⚠️ **{role.name}** is not in the list.")

    @autorole.command(name="list")
    @commands.has_permissions(manage_roles=True)
    async def ar_list(self, ctx):
        data = get_ar_data()
        guild_id = str(ctx.guild.id)

        if guild_id not in data or not data[guild_id]:
            return await ctx.send("📋 No autoroles set up.")

        role_names = []
        for role_id in data[guild_id]:
            role = ctx.guild.get_role(role_id)
            if role:
                # Using role.name instead of mention
                role_names.append(f"• **{role.name}**")
            else:
                role_names.append(f"• `Deleted Role (ID: {role_id})`")

        embed = discord.Embed(
            title=f"📋 Autoroles for {ctx.guild.name}",
            description="\n".join(role_names),
            color=discord.Color.green()
        )
        await ctx.send(embed=embed)

async def setup(bot):
    await bot.add_cog(AutoRole(bot))
