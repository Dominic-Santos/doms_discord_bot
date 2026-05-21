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
      <a href="#about-the-project">About The Project</a>
    </li>
    <li>
      <a href="#how-to-use-the-bot">How to Use the Bot</a>
        <ul>
        <li><a href="#installation">Installation</a></li>
        </ul>
    </li>
    <li>
      <a href="#role-based-commands">Role-Based Commands</a>
    </li>
    <li>
      <a href="#commands">Commands</a>
    </li>
    <li>
      <a href="#timed-tasks">Timed Tasks</a>
        <ul>
        <li><a href="#update-legal-cards">Update Legal Cards</a></li>
        <li><a href="#update-banned-cards">Update Banned Cards</a></li>
        <li><a href="#update-sign-up-sheet">Update Sign-Up Sheet</a></li>
        <li><a href="#update-events">Update Events</a></li>
        <li><a href="#check-for-new-newsfeed-articles">Check for New Newsfeed Articles</a></li>
        </ul>
    </li>
    <li>
      <a href="#create-your-own-bot">Create Your Own Bot</a>
        <ul>
        <li><a href="#discord-app">Discord App</a></li>
        <li><a href="#configure-the-app">Configure the App</a></li>
        <li><a href="#install-requirements">Install Requirements</a></li>
        <li><a href="#run-the-bot">Run the Bot</a></li>
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
* /deck
* /tournament

## Commands

### /help

> Brings you to this page.

### /about

> Information about the bot and its creator — me! 😊

### /admin maintenance check

> Check whether the bot is currently in maintenance mode.

### /admin maintenance toggle {password}

> Toggles maintenance mode on or off. Requires the bot admin password.
> * `password`: defined in the config file

### /admin tournament open_signups {expire_datetime} {password}

> Open tournament sign-ups until a specific expiration datetime.
> * `expire_datetime`: ISO datetime string (example: `2026-05-21 18:30:00`)
> * `password`: defined in the config file

### /admin tournament status

> Show the current in-memory tournament sign-up expiration.

### /admin pokemon set_tournament_channel

> Set the current channel as the output for tournament sign-up messages.
> It’s recommended to use a hidden channel visible only to staff.

### /admin pokemon test_tournament_channel

> Send a generic message to the tournament sign-up output channel.

### /admin pokemon update_legal_cards

> Updates the standard legal card data. This is used for deck checks and tournament sign-ups.

### /admin pokemon update_banned_cards

> Updates the banned cards list. This is used for deck checks and tournament sign-ups.

### /admin pokemon update_signup_sheet

> Updates the tournament sign-up sheet.

### /events pokemon delete_all

> Delete all discord events created by the bot

### /events pokemon follow_premier

> Follow big events and tournaments like the world cup

### /events pokemon unfollow_premier

> Stop following big events and tournament

### /events pokemon follow_store {guid}

> Follow events of a store.
> * `guid`: find the store in the [pokemon event finder](https://events.pokemon.com/EventLocator/), and copy the guid from the url

### /events pokemon unfollow_store {guid}

> Stop following events of a store.
> * `guid`: find the store in the [pokemon event finder](https://events.pokemon.com/EventLocator/), and copy the guid from the url

### /events pokemon unfollow_all

> Stop following all premier and store events.

### /events pokemon sync

> Sync all followed events with discord events.

### /events pokemon set_channel

> Set the current channel to receive event update notifications.

### /events pokemon remove_channel

> Stop receiving event update notifications.

### /newsfeed pokemon set_channel

> Set the current channel to receive newsfeed updates.

### /newsfeed pokemon update

> Check for and fetch new newsfeed articles.

### /newsfeed pokemon disable

> Disable newsfeed updates for the current server.

### /deck pokemon check_url {limitless_url}

> Validates whether a limitless url decklist is Standard legal.
> * `limitless_url`: Create a deck using the [builder](https://my.limitlesstcg.com/builder), then click **Share** > **Copy Import Link**.

### /deck pokemon create {name} {limitless_url}
> Save a deck to be used later, can be used for tournament signups, if a deck with the same name exists, its overwritten.
> * `name`: User defined deck name
> * `limitless_url`: Create a deck using the [builder](https://my.limitlesstcg.com/builder), then click **Share** > **Copy Import Link**.

### /deck pokemon delete {name}
> Delete a saved deck.
> * `name`: The deck to delete

### /deck pokemon info {name}
> Show information on a saved deck, if it's standard legal, last time it was checked, cards in the deck and any errors the deck may have.
> * `name`: The deck to show info

### /deck pokemon check {name}
> Check if a saved game is standard legal.
> * `name`: The deck to check

### /deck pokemon list
> List all saved decks.

### /tournament pokemon_standard signup {name} {pokemon_id} {year_of_birth} {deck_name}

> Sign up for a Standard tournament. If the deck is Standard legal, the sign-up info is posted to the tournament output channel.
> * `name`: User’s first and last name  
> * `pokemon_id`: User’s Pokémon ID  
> * `year_of_birth`: User’s year of birth  
> * `deck_name`: Name of the saved deck

### /tournament pokemon_standard signup_url {name} {pokemon_id} {year_of_birth} {limitless_url}

> Sign up for a Standard tournament. If the deck is Standard legal, the sign-up info is posted to the tournament output channel.
> * `name`: User’s first and last name  
> * `pokemon_id`: User’s Pokémon ID  
> * `year_of_birth`: User’s year of birth  
> * `limitless_url`: Create a deck using the [builder](https://my.limitlesstcg.com/builder), then click **Share** > **Copy Import Link**

### /tournament pokemon_expanded signup {name} {pokemon_id} {year_of_birth} {deck_name}

> Sign up for an Expanded tournament. If the deck is Expanded legal, the sign-up info is posted to the tournament output channel.
> * `name`: User’s first and last name
> * `pokemon_id`: User’s Pokémon ID
> * `year_of_birth`: User’s year of birth
> * `deck_name`: Name of the saved deck

### /tournament pokemon_expanded signup_url {name} {pokemon_id} {year_of_birth} {limitless_url}

> Sign up for an Expanded tournament. If the deck is Expanded legal, the sign-up info is posted to the tournament output channel.
> * `name`: User’s first and last name
> * `pokemon_id`: User’s Pokémon ID
> * `year_of_birth`: User’s year of birth
> * `limitless_url`: Create a deck using the [builder](https://my.limitlesstcg.com/builder), then click **Share** > **Copy Import Link**

## Timed Tasks

The bot also includes scheduled tasks that run automatically at set intervals.

### Update Legal Cards

> Runs daily at 7 AM to update legal cards used for deck validation and sign-ups.

### Update Banned Cards

> Runs daily at 8 AM to update the banned cards used for deck validation and sign-ups.

### Update Sign-Up Sheet

> Runs daily at 9 AM to refresh the tournament sign-up sheet.

### Update Events

> Runs daily at 11 AM to check for new premier and store events.

### Check for New Newsfeed Articles

> Runs every 6 hours to fetch the latest articles from the newsfeed.


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
