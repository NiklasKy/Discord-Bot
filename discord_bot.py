import discord
from discord.ext import commands
import asyncio
from config import TOKEN  # Import the token from config.py
import os
import json
import aiohttp  # Für asynchrones Laden der JSON-Daten

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

def clean_name(name):
    # Removes spaces and converts to lowercase for better comparison
    return name.replace(" ", "").lower()

@bot.command(name='getmembers')
async def get_members(ctx, *, args=None):
    """
    Lists members with a specific role that are not in the JSON data
    Usage: !getmembers "Role Name" [json_url]
    """
    try:
        if not args:
            await ctx.send('Please provide a role name! Example: !getmembers "Role Name" [json_url]')
            return

        # Split args into role_name and optional json_url
        args_split = args.split('" ')
        if args.startswith('"'):
            role_name = args_split[0][1:]  # Remove starting quote
            json_url = args_split[1] if len(args_split) > 1 else None
        else:
            args_split = args.split(' ')
            role_name = args_split[0]
            json_url = args_split[1] if len(args_split) > 1 else None

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

        # Save all discord members first
        with open('discord_usernames.txt', 'w', encoding='utf-8') as f:
            for member in members_info:
                f.write(f"{member['username']}\n")

        with open('current_players.txt', 'w', encoding='utf-8') as f:
            for member in members_info:
                if member['display_name']:
                    f.write(f"{member['display_name']}\n")

        # If JSON URL is provided, compare members
        if json_url:
            try:
                async with aiohttp.ClientSession() as session:
                    async with session.get(json_url) as response:
                        if response.status == 200:
                            json_data = await response.json()
                            
                            # Get signed up players from JSON
                            signed_up_players = []
                            original_names = {}
                            
                            if 'signUps' in json_data:
                                for player in json_data['signUps']:
                                    if 'name' in player:
                                        cleaned_name = clean_name(player['name'])
                                        signed_up_players.append(cleaned_name)
                                        original_names[cleaned_name] = player['name']

                            # Get current discord players (using display names)
                            current_players = [
                                clean_name(member['display_name'])
                                for member in members_info
                                if member['display_name']
                            ]

                            # Find players not signed up
                            not_signed_up = [
                                member for member in members_info
                                if member['display_name'] and 
                                clean_name(member['display_name']) not in signed_up_players
                            ]

                            # Create message with statistics
                            message = f"**Comparison Results for '{role_name}':**\n\n"
                            
                            if not_signed_up:
                                message += "**Not Signed Up Players:**\n"
                                for member in not_signed_up:
                                    message += f"{member['display_name']} ({member['username']})\n"
                            else:
                                message += "All players are signed up! 🎉\n"

                            message += f"\n**Statistics:**\n"
                            message += f"Signed up: {len(signed_up_players)}\n"
                            message += f"Not signed up: {len(not_signed_up)}\n"
                            message += f"Total Discord members: {len(current_players)}\n"

                        else:
                            message = f"Error loading JSON data: HTTP {response.status}"
            except Exception as e:
                message = f"Error processing JSON data: {str(e)}"
        else:
            # If no JSON URL, show all members
            message = f"**All members with role {role_name} ({len(members_info)}):**\n\n"
            for member in members_info:
                if member['display_name']:
                    message += f"{member['display_name']} ({member['username']})\n"

        # Send message (split if too long)
        if len(message) > 2000:
            chunks = [message[i:i+1900] for i in range(0, len(message), 1900)]
            for chunk in chunks:
                await ctx.send(chunk)
        else:
            await ctx.send(message)

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
        bot_member = ctx.guild.get_member(bot.user.id)
        bot_roles = [role.name for role in bot_member.roles if role.name != "@everyone"]
        
        info_text = f"""
**Bot Information:**
Name: {bot.user.name}
ID: {bot.user.id}
Server: {ctx.guild.name}
Bot Roles: {', '.join(bot_roles)}

**Available Commands:**
`!getmembers "Role Name" [json_url]` - Shows all members with the specified role and compares with JSON data if URL provided
`!listroles` - Shows all available roles on the server
`!info` - Shows this information message

**Examples:**
`!getmembers "Minecraft Player"` - Lists all members with the 'Minecraft Player' role
`!getmembers "Discord Admin" https://example.com/data.json` - Lists members and compares with JSON data
`!listroles` - Shows detailed information about all roles
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