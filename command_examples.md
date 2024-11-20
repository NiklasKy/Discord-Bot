# Requiem Discord Bot - Command Documentation

## Command Overview

### User Commands
- `/afk` - Set AFK status
- `/unafk` - Remove AFK status
- `/listafk` - View AFK list for your clan
- `/myafk` - View personal AFK history

### Admin/Officer Commands
- `/getmembers` - List role members
- `/checksignups` - Compare with Raid-Helper
- `/afkstats` - View AFK statistics
- `/afkhistory` - View user AFK history
- `/afkdelete` - Delete AFK entries

## Detailed Command Usage

### AFK Management

#### Setting AFK Status
Command: `/afk`
Parameters:
- `date` (required): DD/MM/YYYY
- `time` (required): HH:MM (24h format, UTC+1/CET)
- `reason` (required): Text explanation

Examples:
```
/afk date:31/12/2023 time:23:59 reason:New Year's Eve
/afk date:24/12/2023 time:18:00 reason:Christmas Holiday
/afk date:01/01/2024 time:12:00 reason:Recovery Day
```

#### Remove AFK Status
Command: `/unafk`
- Removes your current AFK status
- Updates history automatically

Example:
```
/unafk
```

#### View AFK List
Command: `/listafk`
- Shows AFK players from your clan
- Admins see both clans separately

Example Output:
```
**Currently AFK Users (Requiem Sun):**

🟢 **PlayerName**
Until: 31/12/2023 23:59 (UTC+1/CET)
Reason: New Year's Eve

🔴 **AnotherPlayer**
Until: 24/12/2023 18:00 (UTC+1/CET)
Reason: Christmas Holiday
```

#### View Personal History
Command: `/myafk`
- Shows your last 5 AFK entries
- Includes active and past entries

### Admin Commands

#### Get Members List
Command: `/getmembers`
Parameters:
- `role` (required): Discord role name

Example:
```
/getmembers role:"Requiem Sun"
```

#### Check Raid Signups
Command: `/checksignups`
Parameters:
- `role` (required): Discord role name
- `event_id` (required): Raid-Helper event ID

Example:
```
/checksignups role:"Requiem Sun" event_id:1234567890
```

Example Output:
```
**Raid-Helper Comparison Results for 'Requiem Sun':**
Event ID: 1234567890

**Not Signed Up Players:**
Player1
Player2
Player3

**Statistics:**
Signed up: 25
Not signed up: 3
Total Discord members: 28
```

#### View AFK Statistics
Command: `/afkstats`
- Shows statistics for both clans
- Only available to admins/officers

Example Output:
```
**AFK Statistics:**

__**Requiem Sun:**__
Total AFK entries: 15
Unique users: 8
Currently AFK: 3
Average AFK duration: 5.2 days

__**Requiem Moon:**__
Total AFK entries: 10
Unique users: 6
Currently AFK: 2
Average AFK duration: 4.8 days
```

#### View User History
Command: `/afkhistory`
Parameters:
- `user` (required): Discord user mention

Example:
```
/afkhistory user:@Username
```

#### Delete AFK Entries
Command: `/afkdelete`
Parameters:
- `user` (required): Discord user mention
- `all_entries` (optional): True/False

Examples:
```
/afkdelete user:@Username
/afkdelete user:@Username all_entries:True
```

## Status Indicators

- 🟢 Active AFK status
- 🔴 Expired AFK status

## Common Errors and Solutions

### Invalid Date Format
Error: "Invalid date/time format!"
Solution: Use DD/MM/YYYY format for date and HH:MM for time (UTC+1/CET)

### Past Date
Error: "The AFK date must be in the future!"
Solution: Ensure the date and time are set in the future

### Permission Denied
Error: "You don't have permission to use this command!"
Solution: Verify you have the required role (Admin/Officer for admin commands)

### Invalid Event ID
Error: "Error loading Raid-Helper data"
Solution: Check if the event ID is correct and the event exists

## Best Practices

1. **Setting AFK Status**
   - Use clear, concise reasons
   - Set accurate return dates
   - Update status if plans change

2. **Admin Commands**
   - Double-check before deleting entries
   - Regularly check AFK statistics
   - Monitor signup compliance

3. **General Usage**
   - Keep reasons professional
   - Remove AFK status when returning early
   - Report any issues to admins