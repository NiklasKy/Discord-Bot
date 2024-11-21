# Requiem Discord Bot - Command Documentation

## Command Overview

### User Commands
- `/afk` - Set AFK status with start and end time
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
- `start_date` (required): DD/MM/YYYY or 'now'
- `start_time` (required): HH:MM or 'now'
- `end_date` (required): DD/MM/YYYY
- `end_time` (required): HH:MM
- `reason` (required): Text explanation

Examples:
```
/afk start_date:now start_time:now end_date:31/12/2023 end_time:23:59 reason:New Year's Eve
/afk start_date:24/12/2023 start_time:18:00 end_date:26/12/2023 end_time:10:00 reason:Christmas Holiday
/afk start_date:01/01/2024 start_time:00:01 end_date:02/01/2024 end_time:12:00 reason:Recovery Day
```

#### Remove AFK Status
Command: `/unafk`
- Removes your current AFK status
- Updates history automatically
- Marks end time as current time

Example:
```
/unafk
```

#### View AFK List
Command: `/listafk`
- Shows AFK players from your clan
- Admins see both clans separately
- Shows current, future, and recently expired AFKs

Example Output:
```
**Currently AFK Users (Requiem Sun):**

🟢 **PlayerName**
From: 24/12/2023 18:00 (UTC+1/CET)
Until: 26/12/2023 10:00 (UTC+1/CET)
Reason: Christmas Holiday

⚪ **FuturePlayer**
From: 31/12/2023 23:59 (UTC+1/CET)
Until: 01/01/2024 12:00 (UTC+1/CET)
Reason: New Year's Eve

🔴 **ExpiredPlayer**
From: 20/12/2023 10:00 (UTC+1/CET)
Until: 22/12/2023 18:00 (UTC+1/CET)
Reason: Work Trip
```

Status Indicators:
- 🟢 Currently AFK
- ⚪ Scheduled for future
- 🔴 Expired/Ended

#### View Personal History
Command: `/myafk`
- Shows your last 5 AFK entries
- Includes active, scheduled, and past entries
- Shows duration and early endings

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
Scheduled for future: 2
Average AFK duration: 5.2 days

__**Requiem Moon:**__
Total AFK entries: 10
Unique users: 6
Currently AFK: 2
Scheduled for future: 1
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

Example Output:
```
**AFK History for Username:**

🟢 **Requiem Sun**
Created: 24/12/2023 17:45
From: 24/12/2023 18:00
Until: 26/12/2023 10:00
Reason: Christmas Holiday
Planned duration: 1 days, 16 hours
─────────────
🔴 **Requiem Sun**
Created: 20/12/2023 09:45
From: 20/12/2023 10:00
Until: 22/12/2023 18:00
Reason: Work Trip
Ended early: 21/12/2023 20:00
Planned duration: 2 days, 8 hours
Actual duration: 1 day, 10 hours
─────────────
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

## Common Errors and Solutions

### Invalid Date Format
Error: "Invalid date/time format!"
Solution: Use DD/MM/YYYY format for date and HH:MM for time (UTC+1/CET)

### Past Date
Error: "The end date/time must be in the future!"
Solution: Ensure the end date and time are set in the future

### Invalid Time Order
Error: "The end date/time must be after the start date/time!"
Solution: Ensure start time is before end time

### Permission Denied
Error: "You don't have permission to use this command!"
Solution: Verify you have the required role (Admin/Officer for admin commands)

### Invalid Event ID
Error: "Error loading Raid-Helper data"
Solution: Check if the event ID is correct and the event exists

## Best Practices

1. **Setting AFK Status**
   - Use clear, concise reasons
   - Set accurate start and end times
   - Use 'now' for immediate starts
   - Update status if plans change

2. **Admin Commands**
   - Double-check before deleting entries
   - Regularly check AFK statistics
   - Monitor signup compliance
   - Review AFK history for patterns

3. **General Usage**
   - Keep reasons professional
   - Remove AFK status when returning early
   - Report any issues to admins
   - Use appropriate time zones (UTC+1/CET)