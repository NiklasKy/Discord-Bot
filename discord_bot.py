import discord
from discord import app_commands
from discord.ext import commands
import asyncio
import aiohttp
import json
from config import TOKEN

def clean_name(name):
    return name.replace(" ", "").lower()

class MemberBot(commands.Bot):
    def __init__(self):
        intents = discord.Intents.default()
        intents.members = True
        intents.message_content = True
        super().__init__(command_prefix='!', intents=intents)

    async def setup_hook(self):
        print(f'Bot is logged in as {self.user}')
        try:
            synced = await self.tree.sync()
            print(f"Synced {len(synced)} command(s)")
        except Exception as e:
            print(f"Error syncing commands: {e}")

    async def on_ready(self):
        print(f'Bot is ready! Logged in as {self.user}')
        print(f'Bot is in the following servers:')
        for guild in self.guilds:
            print(f'- {guild.name} (id: {guild.id})')
            try:
                await self.tree.sync(guild=guild)
                print(f"  Commands synced for {guild.name}")
            except Exception as e:
                print(f"  Error syncing commands for {guild.name}: {e}")

bot = MemberBot()

@bot.tree.command(name="getmembers", description="Lists all members with a specific role")
@app_commands.describe(
    role="The role to check members for"
)
async def get_members(interaction: discord.Interaction, role: discord.Role):
    try:
        await interaction.response.defer()

        # Create lists for different name types
        members_info = []
        for member in role.members:
            display_name = member.nick if member.nick else (member.global_name if member.global_name else None)
            
            members_info.append({
                'username': member.name,
                'display_name': display_name
            })
        
        # Sort by username
        members_info.sort(key=lambda x: x['username'].lower())

        # Save all discord members
        with open('discord_usernames.txt', 'w', encoding='utf-8') as f:
            for member in members_info:
                f.write(f"{member['username']}\n")

        with open('current_players.txt', 'w', encoding='utf-8') as f:
            for member in members_info:
                if member['display_name']:
                    f.write(f"{member['display_name']}\n")

        # Create message
        message = f"**Members with role {role.name} ({len(members_info)}):**\n\n"
        for member in members_info:
            if member['display_name']:
                message += f"{member['display_name']} ({member['username']})\n"

        # Send message (split if too long)
        if len(message) > 2000:
            chunks = [message[i:i+1900] for i in range(0, len(message), 1900)]
            for chunk in chunks:
                await interaction.followup.send(chunk)
        else:
            await interaction.followup.send(message)

    except Exception as e:
        if not interaction.response.is_done():
            await interaction.response.send_message(f"An error occurred: {str(e)}")
        else:
            await interaction.followup.send(f"An error occurred: {str(e)}")

@bot.tree.command(name="checksignups", description="Compares role members with Raid-Helper signups")
@app_commands.describe(
    role="The role to check members for",
    event_id="The Raid-Helper event ID"
)
async def checksignups(interaction: discord.Interaction, role: discord.Role, event_id: str):
    try:
        await interaction.response.defer()

        # Get all members with their IDs from the role
        role_members = {}
        for member in role.members:
            display_name = member.nick if member.nick else (member.global_name if member.global_name else member.name)
            role_members[str(member.id)] = display_name

        # Construct Raid-Helper API URL
        api_url = f"https://raid-helper.dev/api/v2/events/{event_id}"

        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(api_url) as response:
                    if response.status == 200:
                        event_data = await response.json()
                        
                        # Get signed up player IDs from Raid-Helper
                        signed_up_ids = set()
                        if 'signUps' in event_data:
                            for signup in event_data['signUps']:
                                if 'userId' in signup:
                                    signed_up_ids.add(str(signup['userId']))

                        # Find members who haven't signed up by comparing IDs
                        not_signed_up = []
                        for user_id, display_name in role_members.items():
                            if user_id not in signed_up_ids:
                                not_signed_up.append(display_name)

                        # Sort names alphabetically
                        not_signed_up.sort()

                        # Create message
                        message = f"**Raid-Helper Comparison Results for '{role.name}':**\n"
                        message += f"Event ID: {event_id}\n\n"
                        
                        if not_signed_up:
                            message += "**Not Signed Up Players:**\n"
                            for name in not_signed_up:
                                message += f"{name}\n"
                        else:
                            message += "All players are signed up! 🎉\n"

                        message += f"\n**Statistics:**\n"
                        message += f"Signed up: {len(signed_up_ids)}\n"
                        message += f"Not signed up: {len(not_signed_up)}\n"
                        message += f"Total Discord members: {len(role_members)}\n"

                    else:
                        message = f"Error loading Raid-Helper data: HTTP {response.status}"
        except Exception as e:
            message = f"Error processing Raid-Helper data: {str(e)}"

        # Send message (split if too long)
        if len(message) > 2000:
            chunks = [message[i:i+1900] for i in range(0, len(message), 1900)]
            for chunk in chunks:
                await interaction.followup.send(chunk)
        else:
            await interaction.followup.send(message)

    except Exception as e:
        if not interaction.response.is_done():
            await interaction.response.send_message(f"An error occurred: {str(e)}")
        else:
            await interaction.followup.send(f"An error occurred: {str(e)}")

@bot.tree.command(name="listroles", description="Shows all available roles on the server")
async def list_roles(interaction: discord.Interaction):
    try:
        await interaction.response.defer()

        # Get all roles except @everyone
        roles = [role for role in interaction.guild.roles if role.name != "@everyone"]
        
        # Sort roles by position
        roles.sort(reverse=True, key=lambda x: x.position)

        # Create formatted message
        message = "**Available Roles on this Server:**\n\n"
        for role in roles:
            member_count = len(role.members)
            color_hex = hex(role.color.value)[2:].zfill(6)
            
            message += f"• **{role.name}**\n"
            message += f"  - Members: {member_count}\n"
            message += f"  - Color: #{color_hex}\n"
            message += f"  - Position: {role.position}\n"
            message += f"  - Mentionable: {role.mentionable}\n"
            message += f"  - Hoisted: {role.hoist}\n\n"

        # Send message (split if too long)
        if len(message) > 2000:
            chunks = [message[i:i+1900] for i in range(0, len(message), 1900)]
            for chunk in chunks:
                await interaction.followup.send(chunk)
        else:
            await interaction.followup.send(message)

    except Exception as e:
        if not interaction.response.is_done():
            await interaction.response.send_message(f"An error occurred: {str(e)}")
        else:
            await interaction.followup.send(f"An error occurred: {str(e)}")

def run_bot():
    bot.run(TOKEN)

if __name__ == "__main__":
    run_bot() 