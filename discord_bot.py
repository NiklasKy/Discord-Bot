import discord
from discord import app_commands
from discord.ext import commands
import asyncio
import aiohttp
import json
from datetime import datetime, timedelta
from config import TOKEN, ADMIN_ROLE_ID, OFFICER_ROLE_ID, DATABASE_FILE, CLAN1_ROLE_ID, CLAN2_ROLE_ID
from database import Database
import os

def clean_name(name):
    return name.replace(" ", "").lower()

def parse_time(time_str: str) -> tuple[int, int]:
    """Parse time string in various formats (HH:MM or HHMM)"""
    clean_time = time_str.replace(':', '')
    
    if len(clean_time) != 4:
        raise ValueError("Time must be in format: HHMM or HH:MM")
    
    try:
        hour = int(clean_time[:2])
        minute = int(clean_time[2:])
        
        if not (0 <= hour <= 23 and 0 <= minute <= 59):
            raise ValueError("Invalid hour or minute")
            
        return hour, minute
    except ValueError as e:
        raise ValueError(f"Invalid time format: {str(e)}")

def parse_date(date_str: str, time_str: str) -> datetime:
    """Parse date string and time string into datetime object"""
    current_date = datetime.now()
    
    clean_date = date_str.replace('.', '').replace('/', '')
    if len(clean_date) != 4:
        raise ValueError("Date must be in format: DDMM, DD/MM or DD.MM")
    
    try:
        day = int(clean_date[:2])
        month = int(clean_date[2:])
        
        if not (1 <= month <= 12 and 1 <= day <= 31):
            raise ValueError("Invalid day or month")
            
        hour, minute = parse_time(time_str)
        
        # Start with current year
        year = current_date.year
        
        # Create datetime object
        date_time = datetime(year, month, day, hour, minute)
        
        # If date is in the past, add a year
        if date_time < current_date:
            date_time = datetime(year + 1, month, day, hour, minute)
            
        return date_time
        
    except ValueError as e:
        raise ValueError(f"Invalid date or time format: {str(e)}")

def discord_timestamp(dt: datetime, style: str = 'f') -> str:
    """
    Convert datetime to Discord timestamp format
    Styles:
    t: Short Time (16:20)
    T: Long Time (16:20:30)
    d: Short Date (20/04/2021)
    D: Long Date (20 April 2021)
    f: Short Date/Time (20 April 2021 16:20)
    F: Long Date/Time (Tuesday, 20 April 2021 16:20)
    R: Relative Time (2 months ago)
    """
    return f"<t:{int(dt.timestamp())}:{style}>"

class MemberBot(commands.Bot):
    def __init__(self):
        intents = discord.Intents.default()
        intents.members = True
        intents.message_content = True
        super().__init__(command_prefix='!', intents=intents)
        
        # Initialize database with explicit path
        try:
            db_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), DATABASE_FILE)
            self.db = Database(db_path)
            print(f"Database initialized at: {db_path}")
        except Exception as e:
            print(f"Failed to initialize database: {e}")
            raise

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

@bot.tree.command(name="afk", description="Set your AFK status")
@app_commands.describe(
    start_date="Start date (DDMM, DD/MM or DD.MM)",
    start_time="Start time (HHMM or HH:MM)",
    end_date="End date (DDMM, DD/MM or DD.MM)",
    end_time="End time (HHMM or HH:MM)",
    reason="Reason for being AFK"
)
async def afk(interaction: discord.Interaction, start_date: str, start_time: str, end_date: str, end_time: str, reason: str):
    try:
        # Parse dates
        start_datetime = parse_date(start_date, start_time)
        end_datetime = parse_date(end_date, end_time)
        current_time = datetime.now()

        # If end date is before start date, add a year to end date
        if end_datetime < start_datetime:
            end_datetime = datetime(
                end_datetime.year + 1,
                end_datetime.month,
                end_datetime.day,
                end_datetime.hour,
                end_datetime.minute
            )

        # Validations
        if end_datetime <= current_time:
            await interaction.response.send_message(
                "❌ The end date/time must be in the future!",
                ephemeral=True
            )
            return

        if end_datetime <= start_datetime:
            await interaction.response.send_message(
                "❌ The end date/time must be after the start date/time!",
                ephemeral=True
            )
            return

        if start_datetime < current_time:
            await interaction.response.send_message(
                "❌ The start date/time cannot be in the past!",
                ephemeral=True
            )
            return

        # Check clan role
        user_roles = interaction.user.roles
        clan_role_id = None
        if any(role.id == CLAN1_ROLE_ID for role in user_roles):
            clan_role_id = CLAN1_ROLE_ID
        elif any(role.id == CLAN2_ROLE_ID for role in user_roles):
            clan_role_id = CLAN2_ROLE_ID
            
        if clan_role_id is None:
            await interaction.response.send_message(
                "❌ You must be a member of a clan to use this command!",
                ephemeral=True
            )
            return

        # Store AFK info in database
        bot.db.set_afk(
            user_id=interaction.user.id,
            display_name=interaction.user.display_name,
            start_date=start_datetime,
            end_date=end_datetime,
            reason=reason,
            clan_role_id=clan_role_id
        )
        
        await interaction.response.send_message(
            f"✅ Set AFK status for {interaction.user.display_name}\n"
            f"From: <t:{int(start_datetime.timestamp())}:f>\n"
            f"Until: <t:{int(end_datetime.timestamp())}:f>\n"
            f"Reason: {reason}"
        )
    except ValueError as e:
        await interaction.response.send_message(f"❌ {str(e)}", ephemeral=True)
    except Exception as e:
        await interaction.response.send_message(f"❌ An error occurred: {str(e)}", ephemeral=True)

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

@bot.tree.command(name="listafk", description="List all AFK users from your clan")
async def listafk(interaction: discord.Interaction):
    try:
        # Check if user is admin/officer
        is_admin = any(role.id in [ADMIN_ROLE_ID, OFFICER_ROLE_ID] for role in interaction.user.roles)
        
        # For regular users, check clan membership
        user_roles = interaction.user.roles
        user_clan_role_id = None
        
        if any(role.id == CLAN1_ROLE_ID for role in user_roles):
            user_clan_role_id = CLAN1_ROLE_ID
        elif any(role.id == CLAN2_ROLE_ID for role in user_roles):
            user_clan_role_id = CLAN2_ROLE_ID
            
        if not is_admin and user_clan_role_id is None:
            await interaction.response.send_message(
                "❌ You must be a member of a clan to use this command!",
                ephemeral=True
            )
            return

        # Create message
        message = "**Currently AFK Users:**\n\n"
        current_time = datetime.now()

        # Function to format AFK users for a clan
        def format_clan_afk_users(afk_users):
            formatted_msg = ""
            for user in afk_users:
                user_id, display_name, start_date_str, end_date_str, reason, created_at = user
                start_date = datetime.strptime(start_date_str, "%Y-%m-%d %H:%M:%S")
                end_date = datetime.strptime(end_date_str, "%Y-%m-%d %H:%M:%S")
                
                # Determine status based on current time and dates
                status = "🟢"
                if end_date < current_time:
                    status = "🔴"
                elif start_date > current_time:
                    status = "⚪"  # Not started yet
                
                formatted_msg += f"{status} **{display_name}**\n"
                formatted_msg += f"From: <t:{int(start_date.timestamp())}:f> (<t:{int(start_date.timestamp())}:R>)\n"
                formatted_msg += f"Until: <t:{int(end_date.timestamp())}:f> (<t:{int(end_date.timestamp())}:R>)\n"
                formatted_msg += f"Reason: {reason}\n\n"
            return formatted_msg

        if is_admin:
            # Get and display AFK users for each clan
            clan_configs = [
                (CLAN1_ROLE_ID, "Requiem Sun"),
                (CLAN2_ROLE_ID, "Requiem Moon")
            ]
            
            for clan_role_id, clan_name in clan_configs:
                afk_users = bot.db.get_all_active_afk(clan_role_id)
                if afk_users:
                    message += f"__**{clan_name}:**__\n"
                    message += format_clan_afk_users(afk_users)
                    message += "─────────────\n"
        else:
            # Regular users only see their own clan
            clan_name = "Requiem Sun" if user_clan_role_id == CLAN1_ROLE_ID else "Requiem Moon"
            afk_users = bot.db.get_all_active_afk(user_clan_role_id)
            
            if not afk_users:
                await interaction.response.send_message(f"No users from {clan_name} are currently AFK!")
                return
                
            message += f"__**{clan_name}:**__\n"
            message += format_clan_afk_users(afk_users)

        # Send message (split if too long)
        if len(message) > 2000:
            chunks = [message[i:i+1900] for i in range(0, len(message), 1900)]
            for i, chunk in enumerate(chunks):
                if i == 0:
                    await interaction.response.send_message(chunk)
                else:
                    await interaction.followup.send(chunk)
        else:
            await interaction.response.send_message(message)

    except Exception as e:
        await interaction.response.send_message(
            f"❌ An error occurred: {str(e)}",
            ephemeral=True
        )

@bot.tree.command(name="afkstats", description="Show AFK statistics for all clans")
@has_required_role()
async def afkstats(interaction: discord.Interaction):
    try:
        await interaction.response.defer()

        message = "**AFK Statistics:**\n\n"
        current_time = datetime.now()

        # Get stats for each clan
        clan_configs = [
            (CLAN1_ROLE_ID, "Requiem Sun"),
            (CLAN2_ROLE_ID, "Requiem Moon")
        ]

        for clan_role_id, clan_name in clan_configs:
            stats = bot.db.get_afk_statistics(clan_role_id)
            if stats:
                total_afk, unique_users, active_now, scheduled_future, avg_duration = stats
                
                message += f"__**{clan_name}:**__\n"
                message += f"Total AFK entries: {total_afk}\n"
                message += f"Unique users: {unique_users}\n"
                message += f"Currently AFK: {active_now}\n"
                message += f"Scheduled for future: {scheduled_future}\n"
                if avg_duration:
                    message += f"Average AFK duration: {avg_duration:.1f} days\n"
                message += "\n"

        await interaction.followup.send(message)

    except Exception as e:
        if not interaction.response.is_done():
            await interaction.response.send_message(
                f"❌ An error occurred: {str(e)}",
                ephemeral=True
            )
        else:
            await interaction.followup.send(
                f"❌ An error occurred: {str(e)}",
                ephemeral=True
            )

@bot.tree.command(name="afkhistory", description="Show AFK history for a user (Admin only)")
@app_commands.describe(user="The user to check history for")
@has_required_role()
async def afkhistory(interaction: discord.Interaction, user: discord.Member):
    try:
        await interaction.response.defer()
        
        # Get user's AFK history from database
        history = bot.db.get_user_afk_history(user.id)
        
        if not history:
            await interaction.followup.send(
                f"No AFK history found for {user.display_name}",
                ephemeral=True
            )
            return

        # Create message
        message = f"**AFK History for {user.display_name}:**\n\n"
        current_time = datetime.now()
        
        for entry in history:
            display_name, start_date_str, end_date_str, reason, created_at, ended_at, clan_role_id = entry
            
            # Convert strings to datetime objects
            start_date = datetime.strptime(start_date_str, "%Y-%m-%d %H:%M:%S")
            end_date = datetime.strptime(end_date_str, "%Y-%m-%d %H:%M:%S")
            created_datetime = datetime.strptime(created_at, "%Y-%m-%d %H:%M:%S")
            
            # Determine clan name
            clan_name = "Requiem Sun" if clan_role_id == CLAN1_ROLE_ID else "Requiem Moon"
            
            # Determine status
            status = "🟢"
            if end_date < current_time:
                status = "🔴"
            elif start_date > current_time:
                status = "⚪"
            
            message += f"{status} **{clan_name}**\n"
            message += f"Created: <t:{int(created_datetime.timestamp())}:f>\n"
            message += f"From: <t:{int(start_date.timestamp())}:f>\n"
            message += f"Until: <t:{int(end_date.timestamp())}:f>\n"
            message += f"Reason: {reason}\n"
            
            if ended_at:
                ended_datetime = datetime.strptime(ended_at, "%Y-%m-%d %H:%M:%S")
                message += f"Ended early: <t:{int(ended_datetime.timestamp())}:f>\n"
            
            # Calculate duration
            planned_duration = end_date - start_date
            message += f"Planned duration: {planned_duration.days} days, {planned_duration.seconds//3600} hours\n"
            
            if ended_at:
                actual_end = ended_datetime if ended_datetime < end_date else end_date
                actual_duration = actual_end - start_date
                message += f"Actual duration: {actual_duration.days} days, {actual_duration.seconds//3600} hours\n"
            
            message += "─────────────\n"

        # Send message (split if too long)
        if len(message) > 2000:
            chunks = [message[i:i+1900] for i in range(0, len(message), 1900)]
            for i, chunk in enumerate(chunks):
                if i == 0:
                    await interaction.followup.send(chunk)
                else:
                    await interaction.followup.send(chunk)
        else:
            await interaction.followup.send(message)

    except Exception as e:
        if not interaction.response.is_done():
            await interaction.response.send_message(
                f"❌ An error occurred: {str(e)}",
                ephemeral=True
            )
        else:
            await interaction.followup.send(
                f"❌ An error occurred: {str(e)}",
                ephemeral=True
            )

@bot.tree.command(name="myafk", description="Show your current and future AFK status")
async def myafk(interaction: discord.Interaction):
    try:
        # Get current time for comparison
        current_time = datetime.now()
        
        # Get user's AFK entries from database
        afk_entries = bot.db.get_user_active_afk(interaction.user.id)
        
        if not afk_entries:
            await interaction.response.send_message(
                "You have no current or future AFK entries.",
                ephemeral=True
            )
            return

        # Create message
        message = "**Your AFK Status:**\n\n"
        
        for entry in afk_entries:
            display_name, start_date_str, end_date_str, reason, created_at, clan_role_id = entry
            
            start_date = datetime.strptime(start_date_str, "%Y-%m-%d %H:%M:%S")
            end_date = datetime.strptime(end_date_str, "%Y-%m-%d %H:%M:%S")
            
            # Determine status
            status = "🟢"  # Current
            if end_date < current_time:
                status = "🔴"  # Expired
            elif start_date > current_time:
                status = "⚪"  # Future
            
            # Get clan name
            clan_name = "Requiem Sun" if clan_role_id == CLAN1_ROLE_ID else "Requiem Moon"
            
            message += f"{status} **{clan_name}**\n"
            message += f"From: <t:{int(start_date.timestamp())}:f>\n"
            message += f"Until: <t:{int(end_date.timestamp())}:f>\n"
            message += f"Reason: {reason}\n"
            message += "─────────────\n"

        await interaction.response.send_message(message)

    except Exception as e:
        await interaction.response.send_message(
            f"❌ An error occurred: {str(e)}",
            ephemeral=True
        )

@bot.tree.command(name="afkdelete", description="Delete AFK entries (Admin only)")
@app_commands.describe(
    user="The user whose AFK entries you want to delete",
    all_entries="Delete all entries for this user? If false, only deletes active entries"
)
@has_required_role()
async def afkdelete(
    interaction: discord.Interaction, 
    user: discord.Member, 
    all_entries: bool = False
):
    try:
        await interaction.response.defer()

        # Delete entries and get count of deleted entries
        deleted_count = bot.db.delete_afk_entries(user.id, all_entries)

        if deleted_count > 0:
            message = f"✅ Successfully deleted {deleted_count} AFK "
            message += f"{'entries' if deleted_count > 1 else 'entry'} for {user.display_name}"
            if not all_entries:
                message += " (active entries only)"
        else:
            message = f"❌ No {'active ' if not all_entries else ''}AFK entries found for {user.display_name}"

        await interaction.followup.send(message)

    except Exception as e:
        await interaction.followup.send(
            f"❌ An error occurred: {str(e)}",
            ephemeral=True
        )

@bot.tree.command(name="quickafk", description="Quickly set AFK status until end of day (or specified days)")
@app_commands.describe(
    reason="Reason for being AFK",
    days="Optional: Number of days to be AFK (default: until end of today)"
)
async def quickafk(interaction: discord.Interaction, reason: str, days: int = None):
    try:
        # Get current time as start
        start_datetime = datetime.now()
        
        # Calculate end time (end of current day or specified days)
        if days is None:
            # Set to end of current day (23:59:59)
            end_datetime = start_datetime.replace(hour=23, minute=59, second=59)
        else:
            if days <= 0:
                await interaction.response.send_message(
                    "❌ Number of days must be positive!",
                    ephemeral=True
                )
                return
                
            # Add specified days and set to end of that day
            end_datetime = (start_datetime + timedelta(days=days)).replace(hour=23, minute=59, second=59)

        # Check if user has any clan role
        user_roles = interaction.user.roles
        clan_role_id = None
        
        if any(role.id == CLAN1_ROLE_ID for role in user_roles):
            clan_role_id = CLAN1_ROLE_ID
        elif any(role.id == CLAN2_ROLE_ID for role in user_roles):
            clan_role_id = CLAN2_ROLE_ID
            
        if clan_role_id is None:
            await interaction.response.send_message(
                "❌ You must be a member of a clan to use this command!",
                ephemeral=True
            )
            return

        # Store AFK info in database
        bot.db.set_afk(
            user_id=interaction.user.id,
            display_name=interaction.user.display_name,
            start_date=start_datetime,
            end_date=end_datetime,
            reason=reason,
            clan_role_id=clan_role_id
        )
        
        await interaction.response.send_message(
            f"✅ Quick AFK set for {interaction.user.display_name}\n"
            f"From: <t:{int(start_datetime.timestamp())}:f>\n"
            f"Until: <t:{int(end_datetime.timestamp())}:f>\n"
            f"Reason: {reason}"
        )
    except Exception as e:
        await interaction.response.send_message(f"❌ An error occurred: {str(e)}", ephemeral=True)

def run_bot():
    bot.run(TOKEN)

if __name__ == "__main__":
    run_bot() 