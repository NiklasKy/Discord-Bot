# Requiem Discord Bot - Command Documentation

## Command Overview

### User Commands
- `/afk` - Set AFK status with start and end time
- `/unafk` - Remove AFK status
- `/listafk` - View AFK list for your clan
- `/myafk` - View your current and future AFK status
- `/quickafk` - Quick AFK setting

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
- `start_date` (required): DDMM, DD/MM or DD.MM
- `start_time` (required): HHMM or HH:MM
- `end_date` (required): DDMM, DD/MM or DD.MM
- `end_time` (required): HHMM or HH:MM
- `reason` (required): Text explanation

Examples:
```
/afk start_date:1109 start_time:1254 end_date:1212 end_time:1208 reason:Holiday
/afk start_date:11.09 start_time:12:54 end_date:12/12 end_time:12:08 reason:Holiday
```

Note: 
- Dates in the past will automatically be set to next year
- If end date is before start date in the same year, end date will be set to next year
- All times are shown in your local timezone

Example Output:
```
✅ Set AFK status for Username
From: <t:1757588040:f>
Until: <t:1765699680:f>
Reason: Holiday
```

#### Quick AFK Setting
Command: `/quickafk`
Parameters:
- `reason` (required): Text explanation
- `days` (optional): Number of days to be AFK

Examples:
```
# AFK until end of today
/quickafk reason:Quick meeting

# AFK for specific number of days
/quickafk reason:Short vacation days:3
```

Example Output:
```
✅ Quick AFK set for Username
From: <t:1703163000:f>
Until: <t:1703199540:f>
Reason: Quick meeting
```

#### View Current and Future AFK Status
Command: `/myafk`
- Shows your current and upcoming AFK entries
- No parameters required

Example Output:
```
**Your AFK Status:**

🟢 **Requiem Sun**
From: <t:1703426400:f>
Until: <t:1703599200:f>
Reason: Holiday
─────────────
⚪ **Requiem Sun**
From: <t:1704031200:f>
Until: <t:1704135600:f>
Reason: New Year's Eve
─────────────
```

#### View AFK List
Command: `/listafk`
- Shows AFK players from your clan
- Admins see both clans separately

Example Output:
```
**Currently AFK Users (Requiem Sun):**

🟢 **PlayerName**
From: <t:1703426400:f> (<t:1703426400:R>)
Until: <t:1703599200:f> (<t:1703599200:R>)
Reason: Holiday

⚪ **FuturePlayer**
From: <t:1704031200:f> (<t:1704031200:R>)
Until: <t:1704135600:f> (<t:1704135600:R>)
Reason: New Year's Eve
```

Status Indicators:
- 🟢 Currently AFK
- ⚪ Scheduled for future
- 🔴 Recently expired/Ended

#### Remove AFK Status
Command: `/unafk`
- Removes your current AFK status
- Updates history automatically
- Marks end time as current time

Example:
```
/unafk
```

### Quick AFK Setting
Command: `/quickafk`
Parameters:
- `reason` (required): Text explanation
- `days` (optional): Number of days to be AFK

Examples:
```
# AFK until end of today
/quickafk reason:Quick meeting

# AFK for specific number of days
/quickafk reason:Short vacation days:3
```

Example Output:
```
✅ Quick AFK set for Username
From: 24/12/2023 14:30 (UTC+1/CET)
Until: 24/12/2023 23:59 (UTC+1/CET)
Reason: Quick meeting
```

or with days specified:
```
✅ Quick AFK set for Username
From: 24/12/2023 14:30 (UTC+1/CET)
Until: 27/12/2023 23:59 (UTC+1/CET)
Reason: Short vacation
```

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

## Time Format Information

### Date Input Formats
- `DDMM` - e.g., 1109 for September 11th
- `DD.MM` - e.g., 11.09 for September 11th
- `DD/MM` - e.g., 11/09 for September 11th

### Time Input Formats
- `HHMM` - e.g., 1254 for 12:54
- `HH:MM` - e.g., 12:54 for 12:54

### Time Display
- All times are displayed using Discord's timestamp format (<t:timestamp:f>)
- Times are automatically converted to each user's local timezone
- Relative time indicators (e.g., "in 2 days") are shown in listafk command

### Automatic Year Handling
- Past dates are automatically set to next year
- If end date is before start date in the same year, end date is set to next year
- System automatically handles year transitions