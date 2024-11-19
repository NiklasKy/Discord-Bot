import discord
from discord import app_commands
from discord.ext import commands
import asyncio
import aiohttp
import json
from datetime import datetime
from config import TOKEN, ADMIN_ROLE_ID, OFFICER_ROLE_ID, DATABASE_FILE
from database import Database

def clean_name(name):
    return name.replace(" ", "").lower()

class MemberBot(commands.Bot):
    def __init__(self):
        intents = discord.Intents.default()
        intents.members = True
        intents.message_content = True
        super().__init__(command_prefix='!', intents=intents)
        self.db = Database(DATABASE_FILE)

    async def setup_hook(self):
        print(f'Bot is logged in as {self.user}')
        try:
            synced = await self.tree.sync()
            print(f"Synced {len(synced)} command(s)")
        except Exception as e:
            print(f"Error syncing commands: {e}")

# Create bot instance
bot = MemberBot()

# Check if user has required role
def has_required_role():
    async def predicate(interaction: discord.Interaction):
        return any(role.id in [ADMIN_ROLE_ID, OFFICER_ROLE_ID] for role in interaction.user.roles)
    return app_commands.check(predicate)

@bot.tree.command(name="getmembers", description="Lists all members with a specific role")
@app_commands.describe(role="The role to check members for")
@has_required_role()
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
@has_required_role()
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

@bot.tree.command(name="afk", description="Set your AFK status (Time in UTC+1/CET)")
@app_commands.describe(
    date="Date until you're AFK (format: DD.MM.YYYY)",
    reason="Reason for being AFK",
    time="Time until you're AFK in UTC+1/CET (format: HH:MM, default: 23:59)"
)
async def afk(interaction: discord.Interaction, date: str, reason: str, time: str = "23:59"):
    try:
        # Parse date and time
        try:
            until_datetime = datetime.strptime(f"{date} {time}", "%d.%m.%Y %H:%M")
        except ValueError:
            await interaction.response.send_message(
                "❌ Invalid date/time format!\n"
                "Please use:\n"
                "Date: DD.MM.YYYY\n"
                "Time: HH:MM (optional, defaults to 23:59)\n"
                "Note: Time must be in UTC+1/CET timezone!",
                ephemeral=True
            )
            return

        # Check if date is in the future
        current_time = datetime.now()
        if until_datetime <= current_time:
            await interaction.response.send_message(
                "❌ The AFK date must be in the future!",
                ephemeral=True
            )
            return
        
        # Store AFK info in database
        bot.db.set_afk(
            user_id=interaction.user.id,
            display_name=interaction.user.display_name,
            until_date=until_datetime,
            reason=reason
        )
        
        # Format response message
        formatted_date = until_datetime.strftime("%d.%m.%Y")
        formatted_time = until_datetime.strftime("%H:%M")
        
        await interaction.response.send_message(
            f"✅ Set AFK status for {interaction.user.display_name}\n"
            f"Until: {formatted_date} {formatted_time} (UTC+1/CET)\n"
            f"Reason: {reason}"
        )
    except Exception as e:
        await interaction.response.send_message(
            f"❌ An error occurred: {str(e)}",
            ephemeral=True
        )

@bot.tree.command(name="unafk", description="Remove your AFK status")
async def unafk(interaction: discord.Interaction):
    if bot.db.remove_afk(interaction.user.id):
        await interaction.response.send_message(
            f"✅ Removed AFK status for {interaction.user.display_name}"
        )
    else:
        await interaction.response.send_message(
            "❌ You're not marked as AFK!",
            ephemeral=True
        )

@bot.tree.command(name="listafk", description="List all AFK users")
async def listafk(interaction: discord.Interaction):
    # Get all active AFK users from database
    afk_users = bot.db.get_all_active_afk()
    
    if not afk_users:
        await interaction.response.send_message("No users are currently AFK!")
        return

    # Create message
    message = "**Currently AFK Users:**\n\n"
    current_time = datetime.now()

    for user in afk_users:
        user_id, display_name, until_date_str, reason, created_at = user
        until_date = datetime.strptime(until_date_str, "%Y-%m-%d %H:%M:%S")
        days_left = (until_date - current_time).days
        status = "🔴" if days_left < 0 else "🟢"
        
        message += f"{status} **{display_name}**\n"
        message += f"Until: {until_date.strftime('%d.%m.%Y')}\n"
        message += f"Reason: {reason}\n\n"

    # Send message (split if too long)
    if len(message) > 2000:
        chunks = [message[i:i+1900] for i in range(0, len(message), 1900)]
        for chunk in chunks:
            await interaction.followup.send(chunk)
    else:
        await interaction.response.send_message(message)

@bot.tree.command(name="afkstats", description="Show AFK statistics")
@has_required_role()
async def afkstats(interaction: discord.Interaction):
    stats = bot.db.get_afk_statistics()
    total_afk, unique_users, currently_active, avg_duration = stats
    
    message = "**AFK Statistics:**\n\n"
    message += f"Total AFK entries: {total_afk}\n"
    message += f"Unique users: {unique_users}\n"
    message += f"Currently AFK: {currently_active}\n"
    message += f"Average AFK duration: {avg_duration:.1f} days\n"

    await interaction.response.send_message(message)

@bot.tree.command(name="afkhistory", description="Show AFK history for a user")
@app_commands.describe(user="The user to check history for")
@has_required_role()
async def afkhistory(interaction: discord.Interaction, user: discord.Member):
    history = bot.db.get_user_afk_history(user.id)
    
    if not history:
        await interaction.response.send_message(f"No AFK history found for {user.display_name}")
        return

    message = f"**AFK History for {user.display_name}:**\n\n"
    for entry in history:
        display_name, until_date, reason, created_at, ended_at = entry
        message += f"From: {created_at}\n"
        message += f"Until: {until_date}\n"
        if ended_at:
            message += f"Ended: {ended_at}\n"
        message += f"Reason: {reason}\n\n"

    await interaction.response.send_message(message)

def run_bot():
    bot.run(TOKEN)

if __name__ == "__main__":
    run_bot() 