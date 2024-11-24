# Requiem Discord Bot

A Discord bot designed for managing AFK status and member tracking for Requiem Sun and Requiem Moon clans.

## Overview
This bot helps manage two World of Warcraft guilds (Requiem Sun and Requiem Moon) on the same Discord server. It provides AFK management and raid signup tracking functionality.

## Core Features

### Member Management
- Track guild members
- Compare Discord roles with Raid-Helper signups
- Export member lists

### AFK System
- Set AFK status with flexible date/time formats
- Automatic year calculation for dates
- View current and future AFK status
- Clan-specific AFK tracking
- AFK history and statistics
- Admin management tools
- Time zone support through Discord timestamps

## Technical Requirements

### Server Requirements
- Windows Server 2019 or higher
- Python 3.8+
- NSSM (Non-Sucking Service Manager)
- Git (for updates)

### Python Packages
- discord.py>=2.0.0
- aiohttp>=3.8.0
- python-dotenv>=0.19.0

## Installation

1. **Clone Repository**
```bash
git clone [repository-url]
cd [bot-directory]
```

2. **Install Dependencies**
```bash
pip install -r requirements.txt
```

3. **Configure Bot**
- Copy `config.example.py` to `config.py`
- Add your Discord bot token
- Configure role IDs:
```python
TOKEN = 'your-bot-token'
ADMIN_ROLE_ID = 123456789
OFFICER_ROLE_ID = 987654321
CLAN1_ROLE_ID = 111111111  # Requiem Sun
CLAN2_ROLE_ID = 222222222  # Requiem Moon
```

4. **Setup as Windows Service**
```bash
nssm install DiscordBot "[Python Path]\python.exe" "[Bot Path]\discord_bot.py"
nssm set DiscordBot AppDirectory "[Bot Path]"
```

## Project Structure
```
ProjectRoot/
├── discord_bot.py       # Main bot logic
├── database.py         # Database operations
├── config.py          # Bot configuration (private)
├── config.example.py  # Example configuration
├── requirements.txt   # Python dependencies
├── updatescript.bat   # Update script
├── README.md         # This file
└── command_examples.md # Command documentation
```

## Features

### AFK Management
- Flexible date/time input formats (DDMM, DD.MM, DD/MM, HHMM, HH:MM)
- Automatic year calculation for dates
- View current and upcoming AFK status
- Time zone support through Discord timestamps
- Clan-specific AFK lists
- Personal AFK history tracking
- Admin tools for AFK management

### Member Tracking
- Role-based member lists
- Raid-Helper signup comparison
- Export functionality for member data
- Clan-specific member management

### Admin Tools
- Comprehensive statistics
- User history viewing
- Data management tools
- Role-based access control

## Date and Time Handling

### Date Formats
- DDMM (e.g., 1109)
- DD.MM (e.g., 11.09)
- DD/MM (e.g., 11/09)

### Time Formats
- HHMM (e.g., 1254)
- HH:MM (e.g., 12:54)

### Automatic Year Calculation
- Past dates automatically set to next year
- Smart handling of date ranges across year boundaries
- All times displayed using Discord timestamps
- Automatic timezone conversion for each user

## Database
- SQLite database for reliable data storage
- Automatic creation and management
- Separate tracking for each clan
- Backup-friendly structure

## Security
- Role-based command access
- SQL injection protection
- Secure token handling
- Error logging and monitoring

## Maintenance

### Regular Tasks
- Database backups
- Log file monitoring
- Service status checks
- Update management

### Update Process
1. Run `updatescript.bat` as administrator
2. Script handles:
   - Service stopping
   - Git updates
   - Service restart

## Troubleshooting

### Common Issues
1. **Service Won't Start**
   - Check Python path
   - Verify file permissions
   - Review service logs

2. **Database Errors**
   - Check write permissions
   - Verify file paths
   - Review log files

3. **Command Issues**
   - Verify role assignments
   - Check command syntax
   - Review error messages

## Support
For technical support or questions:
1. Check command documentation
2. Review error logs
3. Contact system administrator

## Time Zone Handling
- All times stored in UTC
- Discord automatically converts to user's local time zone
- Uses Discord's built-in timestamp system (<t:timestamp:f>)
- Relative time indicators available in certain commands

## Notes
- Regular backups recommended
- Monitor disk space
- Keep Python updated
- Review logs regularly


