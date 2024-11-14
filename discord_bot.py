import discord
from discord.ext import commands
import asyncio
from config import TOKEN  # Import the token from config.py
import os

class MemberBot(commands.Bot):
    def __init__(self):
        intents = discord.Intents.default()
        intents.members = True  # Important for accessing member lists
        intents.message_content = True  # Important for reading messages
        super().__init__(command_prefix='!', intents=intents)

    async def setup_hook(self):
        print(f'Bot is logged in as {self.user}')

    async def on_ready(self):
        print(f'Bot is ready! Logged in as {self.user}')
        print(f'Bot is in the following servers:')
        for guild in self.guilds:
            print(f'- {guild.name} (id: {guild.id})')

    async def on_command_error(self, ctx, error):
        if isinstance(error, commands.errors.MissingRequiredArgument):
            await ctx.send('Error: Please provide all required parameters!')
        elif isinstance(error, commands.errors.CommandNotFound):
            await ctx.send('Error: Unknown command!')
        else:
            await ctx.send(f'An error occurred: {str(error)}')

bot = MemberBot()

@bot.command(name='getmembers')
async def get_members(ctx, *, role_name: str = None):
    """
    Lists all members with a specific role and saves their names in separate files
    Usage: !getmembers rolename
    """
    try:
        if role_name is None:
            await ctx.send("Please provide a role name! Example: !getmembers Player")
            return

        role = discord.utils.get(ctx.guild.roles, name=role_name)
        
        if role is None:
            await ctx.send(f"The role '{role_name}' was not found!")
            roles = [r.name for r in ctx.guild.roles if r.name != "@everyone"]
            await ctx.send(f"Available roles: {', '.join(roles)}")
            return

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

        # Save usernames to discord_usernames.txt
        with open('discord_usernames.txt', 'w', encoding='utf-8') as f:
            for member in members_info:
                f.write(f"{member['username']}\n")

        # Save display/global names to current_players.txt
        with open('current_players.txt', 'w', encoding='utf-8') as f:
            for member in members_info:
                if member['display_name']:  # Only write if there is a display name
                    f.write(f"{member['display_name']}\n")

        # Create formatted message
        message = f"**Members with role {role_name} ({len(members_info)}):**\n\n"
        message += "**Discord Usernames:**\n"
        for member in members_info:
            message += f"{member['username']}\n"
        
        message += "\n**Display/Global Names:**\n"
        for member in members_info:
            if member['display_name']:
                message += f"{member['display_name']}\n"

        # Send message (split if too long)
        if len(message) > 2000:
            chunks = [message[i:i+1900] for i in range(0, len(message), 1900)]
            for chunk in chunks:
                await ctx.send(chunk)
        else:
            await ctx.send(message)

        await ctx.send(f"""Files have been saved:
- 'discord_usernames.txt' (Discord usernames)
- 'current_players.txt' (Server nicknames or global names)""")

    except Exception as e:
        await ctx.send(f"An error occurred: {str(e)}")

@bot.command(name='listroles')
async def list_roles(ctx):
    """
    Lists all roles on the server with member counts
    Usage: !listroles
    """
    try:
        # Get all roles except @everyone
        roles = [role for role in ctx.guild.roles if role.name != "@everyone"]
        
        # Sort roles by position (higher roles first)
        roles.sort(reverse=True, key=lambda x: x.position)

        # Create formatted message
        message = "**Available Roles on this Server:**\n\n"
        for role in roles:
            # Count members with this role
            member_count = len(role.members)
            # Add role color in hex format
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
                await ctx.send(chunk)
        else:
            await ctx.send(message)

    except Exception as e:
        await ctx.send(f"An error occurred: {str(e)}")

@bot.command(name='info')
async def info_command(ctx):
    """Shows information about the bot and available commands"""
    try:
        # Get bot information
        bot_member = ctx.guild.get_member(bot.user.id)
        bot_roles = [role.name for role in bot_member.roles if role.name != "@everyone"]
        
        info_text = f"""
**Bot Information:**
Name: {bot.user.name}
ID: {bot.user.id}
Server: {ctx.guild.name}
Bot Roles: {', '.join(bot_roles)}

**Available Commands:**
`!getmembers rolename` - Shows all members with the specified role
`!listroles` - Shows all available roles on the server
`!info` - Shows this information message

**Examples:**
`!getmembers Player` - Lists all members with the 'Player' role
`!listroles` - Shows detailed information about all roles

**Files Created:**
• current_players.txt - Contains global names
• discord_usernames.txt - Contains Discord usernames
• discord_members_full.txt - Contains both names
        """
        await ctx.send(info_text)

    except Exception as e:
        await ctx.send(f"An error occurred: {str(e)}")

# Remove the old help command
bot.remove_command('help')

# Remove the TOKEN definition here since we're importing it
def run_bot():
    bot.run(TOKEN)

if __name__ == "__main__":
    run_bot() 