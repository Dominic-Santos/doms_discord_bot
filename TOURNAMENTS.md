# Tournament System Documentation

## Overview

The tournament system allows server admins to create and manage multiple tournaments simultaneously. Each tournament has a unique name and expiration date, and persists across bot restarts via `data/tournaments.json`.

## Features

- **Multiple Concurrent Tournaments**: Run several tournaments at the same time
- **Data Persistence**: Tournaments are saved to JSON and survive bot restarts
- **User-Friendly Selection**: Dropdown menu when multiple tournaments are open
- **Tournament Tracking**: Each signup records which tournament it was for
- **CSV Export**: Export signups with tournament information

## Admin Commands

### Create a Tournament

```
/admin tournament create name:"Tournament Name" expire_datetime:"2026-05-21 18:30:00" password:"your_password"
```

**Parameters:**
- `name` (string): Display name for the tournament
- `expire_datetime` (string): Expiration date/time in ISO format: `YYYY-MM-DD HH:MM:SS`
- `password` (string): Your admin password from `config.json`

**Example:**
```
/admin tournament create name:"Regional Championship" expire_datetime:"2026-05-21 18:30:00" password:"abc123"
```

### List Tournaments

```
/admin tournament list
```

Shows all tournaments with their status (OPEN/CLOSED), expiration times, and tournament IDs.

**Example Output:**
```
Tournaments:

Regional Championship (ID: `regional_championship`)
  Status: OPEN
  Expires: 2026-05-21 18:30:00

Local Qualifier (ID: `local_qualifier`)
  Status: CLOSED
  Expires: 2026-05-15 14:00:00
```

### Delete a Tournament

```
/admin tournament delete tournament_id:"tournament_id" password:"your_password"
```

**Parameters:**
- `tournament_id` (string): The ID of the tournament to delete (shown in list command)
- `password` (string): Your admin password

**Example:**
```
/admin tournament delete tournament_id:"local_qualifier" password:"abc123"
```

### Tournament Status

```
/admin tournament status
```

Shows general tournament status information.

## User Sign-Up Flow

Users sign up using the tournament commands:

```
/tournament pokemon_standard signup name:"John Doe" pokemon_id:123456789 year_of_birth:1995 deck_name:"MyDeck"
/tournament pokemon_expanded signup name:"Jane Smith" pokemon_id:987654321 year_of_birth:1998 deck_name:"MyDeck"
/tournament pokemon_standard signup_url name:"Bob Jones" pokemon_id:555555555 year_of_birth:2000 limitless_url:"https://my.limitlesstcg.com/builder?i=abc123"
```

### Tournament Selection Behavior

1. **Zero Tournaments Open**
   - Bot responds: "No tournaments are open at this moment."
   - User cannot sign up

2. **One Tournament Open**
   - Tournament is auto-selected
   - User signs up immediately
   - No dropdown shown

3. **Multiple Tournaments Open**
   - Bot displays dropdown menu
   - User selects tournament from list
   - Dropdown times out after 30 seconds if no selection

**Example Dropdown Display:**
```
Please select a tournament to sign up for:

[Select a tournament ▼]
  • Regional Championship - Expires: 2026-05-21 18:30:00
  • Local Qualifier - Expires: 2026-05-15 14:00:00
```

## Tournament Data Storage

### File Structure

Tournaments are stored in `data/tournaments.json`:

```json
{
    "tournaments": {
        "regional_championship": {
            "name": "Regional Championship",
            "expires_at": "2026-05-21 18:30:00",
            "created_at": "2026-05-01 10:00:00"
        },
        "local_qualifier": {
            "name": "Local Qualifier",
            "expires_at": "2026-05-15 14:00:00",
            "created_at": "2026-05-01 10:00:00"
        }
    }
}
```

### Tournament ID Generation

Tournament IDs are automatically generated from the tournament name:
- Name converted to lowercase
- Spaces replaced with underscores
- If a duplicate ID exists, a counter is appended (e.g., `regional_championship_1`)

**Examples:**
- "Regional Championship" → `regional_championship`
- "Local Qualifier" → `local_qualifier`
- "Local Qualifier" (second one) → `local_qualifier_1`

## Signup Tracking

### In-Memory Storage

Signups are stored in memory by guild ID and include:
- Tournament ID (which tournament the signup is for)
- Format (standard or expanded)
- Full name
- Pokemon ID
- Year of birth
- Limitless URL
- Discord user ID
- Timestamp

### Export Signups

Export current signups as CSV:

```
/admin pokemon list_signups
```

**Example Output:**
```csv
format,full_name,pokemon_id,year_of_birth,tournament_id
standard,John Doe,123456789,1995,regional_championship
standard,Jane Smith,987654321,1998,regional_championship
expanded,Bob Jones,555555555,2000,local_qualifier
```

### Signup Replacement

If a user with the same `pokemon_id` signs up again:
- Their previous signup is replaced
- Tournament ID may change if they chose a different tournament
- Timestamp is updated

## Best Practices

### Tournament Naming

Use clear, descriptive names:
- ✅ "Regional Championship"
- ✅ "Friday Night Magic"
- ✅ "Local Qualifier Round 1"
- ❌ "t1" (unclear)
- ❌ "event" (too generic)

### Expiration Times

Set expiration times based on your needs:
- For a same-day event, set expiration to tournament start time or a few hours before
- For multi-day signups, set expiration to registration deadline
- Leave buffer time for late signups if desired

**Example Timeline:**
```
Monday 10:00 AM  - Tournament created, signups open
Friday 5:00 PM   - Signup deadline (expiration set to this time)
Saturday 10:00 AM - Tournament runs (everyone already checked in)
```

### Cleanup

Delete closed tournaments to keep the list manageable:

```
/admin tournament delete tournament_id:"old_tournament" password:"abc123"
```

Note: This only removes the tournament definition, not existing signups.

## Datetime Format Reference

All tournament datetime fields use ISO 8601 format:

```
YYYY-MM-DD HH:MM:SS
```

| Component | Format | Example | Valid Range |
| --- | --- | --- | --- |
| Year | YYYY | 2026 | 1900-9999 |
| Month | MM | 05 | 01-12 |
| Day | DD | 21 | 01-31 |
| Hour | HH | 18 | 00-23 |
| Minute | MM | 30 | 00-59 |
| Second | SS | 00 | 00-59 |

**Examples:**
- `2026-05-21 18:30:00` - May 21, 2026 at 6:30 PM
- `2026-12-25 09:00:00` - December 25, 2026 at 9:00 AM
- `2026-01-01 00:00:00` - January 1, 2026 at midnight

### Timezone Handling

- Times are interpreted in your **server's local timezone**
- Timezone-aware ISO datetimes (with timezone info) are automatically converted to local time
- The bot uses server local time for all comparisons

Example with timezone:
```
2026-05-21T18:30:00-04:00  (EDT)
→ Converted to your server's local time for storage
```

## Troubleshooting

### Tournament isn't showing up in the list

**Possible Causes:**
1. Tournament hasn't been created yet - create it with `/admin tournament create`
2. Bot restart cleared tournaments - check `data/tournaments.json` exists
3. Wrong server context - list shows tournaments for current server only

### Users can't select a tournament from dropdown

**Possible Causes:**
1. Dropdown timed out after 30 seconds - have them try again
2. No tournaments are actually open - check `/admin tournament list`
3. All tournaments are expired - create new ones or extend expiration times

### Signup doesn't appear in CSV export

**Possible Causes:**
1. Wrong server - signups are stored per guild
2. Signup failed during validation - check bot response
3. Signup was replaced - same `pokemon_id` can only have one active signup

## API Reference (For Developers)

Key methods in `TournamentBot` class:

### Load/Save
- `load_tournaments()` - Load from `data/tournaments.json`
- `save_tournaments()` - Write to `data/tournaments.json`

### Query
- `get_open_tournaments(now=None)` - Get all currently open tournaments

### Selection
- `get_tournament_selection(ctx, open_tournaments)` - Show dropdown and get user's choice

### Signup Recording
- `record_tournament_signup(guild_id, user_id, full_name, pokemon_id, year_of_birth, limitless_url, format, tournament_id)`

All tournament data persists across bot restarts via the JSON storage layer.
