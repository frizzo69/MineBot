import discord
from discord.ext import commands
import json
import os

RR_FILE = "reaction_roles.json"

def get_rr_data():
    if not os.path.exists(RR_FILE): return {}
    try:
        with open(RR_FILE, "r") as f:
            return json.load(f)
    except: return {}

def save_rr_data(data):
    with open(RR_FILE, "w") as f:
        json.dump(data, f, indent=4)

class ReactionRoles(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    # --- EVENT LISTENERS (Core Logic) ---
    @commands.Cog.listener()
    async def on_raw_reaction_add(self, payload):
        if payload.user_id == self.bot.user.id: return
        data = get_rr_data()
        guild_id, msg_id = str(payload.guild_id), str(payload.message_id)

        if guild_id not in data or msg_id not in data[guild_id]: return
        rr_config = data[guild_id][msg_id]
        mode = rr_config.get("mode", "normal")
        if mode == "lock": return

        emoji_str = str(payload.emoji)
        if emoji_str not in rr_config["roles"]: return

        guild = self.bot.get_guild(payload.guild_id)
        member = guild.get_member(payload.user_id)
        role = guild.get_role(rr_config["roles"][emoji_str])
        if not member or not role: return

        try:
            if mode == "normal":
                await member.add_roles(role, reason="RR (Normal)")
            elif mode == "verify":
                await member.add_roles(role, reason="RR (Verify)")
                channel = guild.get_channel(payload.channel_id)
                msg = await channel.fetch_message(payload.message_id)
                await msg.remove_reaction(payload.emoji, member)
            elif mode == "drop":
                await member.remove_roles(role, reason="RR (Drop)")
                channel = guild.get_channel(payload.channel_id)
                msg = await channel.fetch_message(payload.message_id)
                await msg.remove_reaction(payload.emoji, member)
            elif mode == "reversed":
                await member.remove_roles(role, reason="RR (Reversed)")
            elif mode == "unique":
                roles_to_remove = [guild.get_role(r_id) for e_str, r_id in rr_config["roles"].items() if r_id != role.id and guild.get_role(r_id) in member.roles]
                if roles_to_remove:
                    await member.remove_roles(*roles_to_remove, reason="RR (Unique Enforce)")
                    channel = guild.get_channel(payload.channel_id)
                    msg = await channel.fetch_message(payload.message_id)
                    for r in msg.reactions:
                        if str(r.emoji) != emoji_str:
                            await msg.remove_reaction(r.emoji, member)
                await member.add_roles(role, reason="RR (Unique)")
        except discord.Forbidden:
            pass

    @commands.Cog.listener()
    async def on_raw_reaction_remove(self, payload):
        if payload.user_id == self.bot.user.id: return
        data = get_rr_data()
        guild_id, msg_id = str(payload.guild_id), str(payload.message_id)

        if guild_id not in data or msg_id not in data[guild_id]: return
        rr_config = data[guild_id][msg_id]
        mode = rr_config.get("mode", "normal")
        if mode in ["lock", "verify", "drop"]: return

        emoji_str = str(payload.emoji)
        if emoji_str not in rr_config["roles"]: return

        guild = self.bot.get_guild(payload.guild_id)
        member = guild.get_member(payload.user_id)
        role = guild.get_role(rr_config["roles"][emoji_str])
        if not member or not role: return

        try:
            if mode in ["normal", "unique"]: await member.remove_roles(role, reason="RR Removed")
            elif mode == "reversed": await member.add_roles(role, reason="RR Reversed Removed")
        except discord.Forbidden: pass

    # --- SETUP COMMANDS ---

    @commands.group(name="rr", invoke_without_command=True)
    @commands.has_permissions(manage_roles=True)
    async def rr(self, ctx):
        await ctx.send("⚙️ **Reaction Roles:** Use `-rr make`, `-rr add`, `-rr list`, or `-rr remove <id>`.")

    @rr.command(name="make")
    @commands.has_permissions(manage_roles=True)
    async def rr_make(self, ctx, *, description: str):
        embed = discord.Embed(description=description, color=discord.Color.blue())
        msg = await ctx.send(embed=embed)
        await ctx.send(f"✅ Created! Message ID: `{msg.id}`. Use `-rr add {msg.id} <emoji> @role` to add roles.")

    @rr.command(name="add")
    @commands.has_permissions(manage_roles=True)
    async def rr_add(self, ctx, msg_id: str, emoji: str, role: discord.Role):
        try: msg = await ctx.channel.fetch_message(int(msg_id))
        except discord.NotFound: return await ctx.send("❌ Message not found in this channel.")

        data = get_rr_data()
        guild_id = str(ctx.guild.id)

        if guild_id not in data: data[guild_id] = {}
        if msg_id not in data[guild_id]:
            data[guild_id][msg_id] = {"channel_id": ctx.channel.id, "mode": "normal", "roles": {}}
        elif "channel_id" not in data[guild_id][msg_id]:
            data[guild_id][msg_id]["channel_id"] = ctx.channel.id # Retroactively update older setups

        try: await msg.add_reaction(emoji)
        except discord.HTTPException: return await ctx.send("❌ Invalid emoji.")

        data[guild_id][msg_id]["roles"][emoji] = role.id
        save_rr_data(data)
        await ctx.send(f"✅ Added {emoji} for **{role.name}** to message `{msg_id}`.")

    @rr.command(name="list")
    @commands.has_permissions(manage_roles=True)
    async def rr_list(self, ctx):
        """Lists all active reaction roles with a unique ID and channel name."""
        data = get_rr_data()
        guild_id = str(ctx.guild.id)

        if guild_id not in data or not data[guild_id]:
            return await ctx.send("📋 There are no reaction roles currently set up in this server.")

        embed = discord.Embed(title=f"📋 Reaction Roles for {ctx.guild.name}", color=discord.Color.green())
        
        current_id = 1
        for msg_id, config in data[guild_id].items():
            mode = config.get("mode", "normal")
            
            # Fetch the channel mention safely
            channel_id = config.get("channel_id")
            channel = ctx.guild.get_channel(channel_id) if channel_id else None
            ch_mention = channel.mention if channel else "`Unknown Channel`"

            roles_text = []
            for emoji, role_id in config["roles"].items():
                role = ctx.guild.get_role(role_id)
                role_name = f"**{role.name}**" if role else "`Deleted Role`"
                # Add the unique ID badge like [1], [2], etc.
                roles_text.append(f"`[{current_id}]` {emoji} ➡️ {role_name}")
                current_id += 1

            embed.add_field(
                name=f"📍 {ch_mention} | Msg: {msg_id} | Mode: {mode.title()}",
                value="\n".join(roles_text) or "No roles bound.",
                inline=False
            )

        embed.set_footer(text="Use -rr remove <id> to delete a specific reaction role.")
        await ctx.send(embed=embed)

    @rr.command(name="remove")
    @commands.has_permissions(manage_roles=True)
    async def rr_remove(self, ctx, bind_id: int):
        """Removes a reaction role using the unique ID from -rr list."""
        data = get_rr_data()
        guild_id = str(ctx.guild.id)

        if guild_id not in data or not data[guild_id]:
            return await ctx.send("❌ No reaction roles set up.")

        current_id = 1
        found = False

        # Iterate through exactly like the list command does
        for msg_id, config in list(data[guild_id].items()):
            for emoji, role_id in list(config["roles"].items()):
                if current_id == bind_id:
                    found = True
                    # Delete the bind
                    del data[guild_id][msg_id]["roles"][emoji]
                    
                    # Cleanup the message entirely if it has no roles left
                    if not data[guild_id][msg_id]["roles"]:
                        del data[guild_id][msg_id]
                    
                    save_rr_data(data)

                    # Try to physically remove the bot's reaction from the message
                    channel_id = config.get("channel_id")
                    channel = ctx.guild.get_channel(channel_id) if channel_id else ctx.channel
                    try:
                        if channel:
                            msg = await channel.fetch_message(int(msg_id))
                            await msg.clear_reaction(emoji)
                    except Exception:
                        pass # Fails quietly if message is deleted or in a hidden channel
                    
                    return await ctx.send(f"✅ Successfully removed Reaction Role **ID {bind_id}** ({emoji}).")
                current_id += 1

        if not found:
            await ctx.send(f"❌ Could not find a Reaction Role with ID `{bind_id}`. Check `-rr list`.")

    # --- MODIFIERS (Unique, Verify, Drop, etc.) ---
    async def set_mode(self, ctx, msg_id: str, mode: str):
        data = get_rr_data()
        guild_id = str(ctx.guild.id)
        if guild_id not in data or msg_id not in data[guild_id]:
            return await ctx.send("❌ No reaction roles are set up on that message yet.")
        data[guild_id][msg_id]["mode"] = mode
        save_rr_data(data)
        await ctx.send(f"✅ Message `{msg_id}` is now set to **{mode.capitalize()}** mode.")

    @rr.command(name="unique")
    @commands.has_permissions(manage_roles=True)
    async def rr_unique(self, ctx, msg_id: str): await self.set_mode(ctx, msg_id, "unique")

    @rr.command(name="verify")
    @commands.has_permissions(manage_roles=True)
    async def rr_verify(self, ctx, msg_id: str): await self.set_mode(ctx, msg_id, "verify")

    @rr.command(name="drop")
    @commands.has_permissions(manage_roles=True)
    async def rr_drop(self, ctx, msg_id: str): await self.set_mode(ctx, msg_id, "drop")

    @rr.command(name="reversed")
    @commands.has_permissions(manage_roles=True)
    async def rr_reversed(self, ctx, msg_id: str): await self.set_mode(ctx, msg_id, "reversed")

    @rr.command(name="lock")
    @commands.has_permissions(manage_roles=True)
    async def rr_lock(self, ctx, msg_id: str): await self.set_mode(ctx, msg_id, "lock")

    @rr.command(name="normal")
    @commands.has_permissions(manage_roles=True)
    async def rr_normal(self, ctx, msg_id: str): await self.set_mode(ctx, msg_id, "normal")

async def setup(bot):
    await bot.add_cog(ReactionRoles(bot))
