<!-- PROJECT LOGO -->
<br />
<div align="center">
  <a href="https://github.com/othneildrew/Best-README-Template">
    <img src="images/logo.gif" alt="Logo" width="114" height="96">
  </a>

  <h3 align="center">doms_discord_bot</h3>

  <p align="center">
    A Discord bot that provides TCG news, decklist validation, and tournament sign-ups — primarily focused on the Pokémon TCG.
    <br />
    <a href="https://github.com/Dominic-Santos/doms_discord_bot"><strong>Explore the docs »</strong></a>
  </p>
</div>

<!-- TABLE OF CONTENTS -->
<details>
  <summary>Table of Contents</summary>
  <ol>
    <li>
        <a href="#About-The-Project">About The Project</a>
    </li>
    <li>
        <a href="#How-to-use-the-bot">How to Use the Bot</a>
        <ul>
            <li><a href="#Installation">Installation</a></li>
        </ul>
    </li>
    <li>
        <a href="#Roles-based-commands">Role-Based Commands</a>
    </li>
    <li>
        <a href="#Commands">Commands</a>
    </li>
    <li>
        <a href="#Timed-tasks">Timed Tasks</a>
        <ul>
            <li><a href="#Update-sign-up-sheet">Update Sign-Up Sheet</a></li>
            <li><a href="#Update-legal-cards">Update Legal Cards</a></li>
            <li><a href="#Check-for-new-newsfeed-articles">Check for New Newsfeed Articles</a></li>
        </ul>
    </li>
    <li>
        <a href="#Create-your-own-bot">Create Your Own Bot</a>
        <ul>
            <li><a href="#Discord-App">Discord App</a></li>
            <li><a href="#Configure-the-App">Configure the App</a></li>
            <li><a href="#Install-requirements">Install Requirements</a></li>
            <li><a href="#Run-the-bot">Run the Bot</a></li>
        </ul>
    </li>
  </ol>
</details>


<!-- ABOUT THE PROJECT -->
## About The Project

This passion project was created to provide better tools and automation for my local game store. As a Pokémon Professor (Judge), I found the official tools to be severely lacking. To help address those shortcomings, I developed this bot to keep the community informed and streamline everyday operations — from deck checks to tournament sign-ups and more.

## How to Use the Bot

### Installation

Click [here](https://discord.com/oauth2/authorize?client_id=1398430497947779182) to install DomsBot on your server!

**OR**

<a href="#create-your-own-bot">Create your own bot</a> and add it to your server.

## Role-Based Commands

Some commands are intended for server administrators only. It’s recommended to restrict command access based on server roles, which can be managed through your server's integration settings.

**Admin Commands:**
* /admin
* /newsfeed
* /events

**User Commands:**
* /help
* /about
* /decklist
* /tournament

## Commands

### /help

> Brings you to this page.

### /about

> Information about the bot and its creator — me! 😊

### /admin check_maintenance

> Check whether the bot is currently in maintenance mode.

### /admin toggle_maintenance <password>

> Toggles maintenance mode on or off. Requires the bot admin password.

### /admin set_tournament_channel

> Set the current channel as the output for tournament sign-up messages.
> It’s recommended to use a hidden channel visible only to staff.

### /admin send_output_channel

> Send a generic message to the tournament sign-up output channel.

### /admin update_legal_cards

> Updates the standard legal card data. This is used for deck checks and tournament sign-ups.

### /admin update_signup_sheet

> Updates the tournament sign-up sheet.

### /events delete_all

> Delete all discord events created by the bot

### /events follow_premier

> Follow big events and tournaments like the world cup

### /events unfollow_premier

> Stop following big events and tournament

### /events follow_store <guid>

> Follow events of a store.
> * `guid`: find the store in the [pokemon event finder](https://events.pokemon.com/EventLocator/), and copy the guid from the url

### /events unfollow_store <guid>

> Stop following events of a store.
> * `guid`: find the store in the [pokemon event finder](https://events.pokemon.com/EventLocator/), and copy the guid from the url

### /events unfollow_all

> Stop following all premier and store events.

### /events sync

> Sync all followed events with discord events.

### /events set_channel

> Set the current channel to receive event update notifications.

### /events remove_channel

> Stop receiving event update notifications.

### /newsfeed set_channel

> Set the current channel to receive newsfeed updates.

### /newsfeed update

> Check for and fetch new newsfeed articles.

### /decklist check <deck_url>

> Validates whether a decklist is Standard legal.
> * `deck_url`: Create a deck using the [builder](https://my.limitlesstcg.com/builder), then click **Share** > **Copy Import Link**.

### /tournament signup <name> <pokemon_id> <year_of_birth> <deck_url>

> Sign up for a tournament. If the deck is Standard legal, the sign-up info is posted to the tournament output channel.
> * `name`: User’s first and last name  
> * `pokemon_id`: User’s Pokémon ID  
> * `year_of_birth`: User’s year of birth  
> * `deck_url`: Create a deck using the [builder](https://my.limitlesstcg.com/builder), then click **Share** > **Copy Import Link**

## Timed Tasks

The bot also includes scheduled tasks that run automatically at set intervals.

### Update Sign-Up Sheet

> Runs daily at 8 AM to refresh the tournament sign-up sheet.

### Update Legal Cards

> Runs daily at 7 AM to update the Standard legal cards used for deck validation and sign-ups.

### Check for New Newsfeed Articles

> Runs every 6 hours to fetch the latest articles from the newsfeed.

### Event Sync

> Runs daily at 9 AM, checks for changes in premier and store events and creates them as discord events.

## Create Your Own Bot

If you’d like to run your own version of the bot, feel free to fork or copy the code from this repository 😊 A shoutout is always appreciated!

### Discord App

You’ll need to create a Discord application. Follow the official guide [here](https://discord.com/developers/docs/intro).

The bot requires permissions to post messages in channels and manage events.

### Configure the App

Refer to the example below and fill out your own `config.json`:
```json
{
    "app_token": "app_token_placeholder",
    "admin_password": "123abc",
    "maintenance_mode": true
}
```
* app_token: this is provided by Discord when creating the Discord App.
* admin_password: this is used by super-admin to control the bot via discord commands, make up your own.
* maintenance_mode: if the bot will start in maintenance mode.

### Install requirements
```sh
pip install -r requirements.txt
```

### Run the bot
```sh
python main.py
```
