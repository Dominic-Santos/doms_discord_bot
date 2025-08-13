<!-- PROJECT LOGO -->
<br />
<div align="center">
  <a href="https://github.com/othneildrew/Best-README-Template">
    <img src="images/logo.gif" alt="Logo" width="114" height="96">
  </a>

  <h3 align="center">doms_discord_bot</h3>

  <p align="center">
    A discord bot that provides TCG news, decklist checking and tournament sign-ups. (Mostly around Pokémon TCG)
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
      <a href="#create-your-own-bot">Create your own bot</a>
      <ul>
        <li><a href="#discord-app">Discord App</a></li>
        <li><a href="#roles-based-commands">Roles based commands</a></li>
        <li><a href="#configure-the-app">Configure the App</a></li>
        <li><a href="#install-requirements">Install requirements</a></li>
        <li><a href="#run-the-bot">Run the bot</a></li>
      </ul>
    </li>
  </ol>
</details>


<!-- ABOUT THE PROJECT -->
## About The Project

This is a passion project aimed at providing better tools and automation for my local game store. As a Pokémon Professor (Judge), I found the official tools to be severely lacking. To help alleviate some of the pain points, I’ve been developing this bot with features designed to keep the community informed and streamline daily operations — from deck checks to sign-ups and more.

## How to use the bot

### Installation

Click [here](https://discord.com/oauth2/authorize?client_id=1398430497947779182) to install DomsBot to your server!

OR

<a href="#create-your-own-bot">Create your own bot</a> and install it to your server!

## Roles based commands

Some commands are intended for server admins only. We recommend restricting access to commands based on server roles, which can be configured through your server's integration settings.

Admin commands:
* /admin
* /newsfeed

User commands:
* /about
* /decklist
* /tournament

## Commands

> /about

>> Info about the creator! Me 😊

> /admin check_maintenance

>> Check if the bot is in maintenance mode.

> /admin toggle_maintenance <password>

>> Owner can set the bot maintenance mode on/off. Bot admin password is required.

> /admin set_output_channel

>> Set the current channel as the output tournament sign-ups.

>> It's recommended this be a hidden channel available only to staff.

> /admin set_output_channel

>> Send a generic message to the tournament sign-up output channel.

> /admin update_legal_cards

>> Update the standard legal card data, this is used for deck checks and tournament sign-ups.

> /admin update_signup_sheet

>> Update the sign-up sheet, this is used for tournament sign-ups.

> /newsfeed set_channel

>> Set the current channel as the output for newsfeed updates.

> /newsfeed update

>> Check for new newsfeed articles.

> /decklist check <deck_url>

>> Check if a decklist is standard legal.

>>> deck_url: create a deck using the [builder](https://my.limitlesstcg.com/builder), then click Share > Copy Import Link

> /tournament signup <name> <pokemon_id> <year_of_birth> <deck_url>

>> Sign up for a tournament, if the deck is standard legal, the sign-up info is posted in the tournament sign-up output channel.

>>> name: Users first and last name.
>>> pokemon_id: Users Pokémon ID.
>>> year_of_birth: Users year of birth.
>>> deck_url: create a deck using the [builder](https://my.limitlesstcg.com/builder), then click Share > Copy Import Link

## Create your own bot

If you’d like to run your own version of the bot, feel free to fork, use, or copy the code in this repo 😊 A mention is always appreciated!

### Discord App

You will need to create a discord app, follow the guide [here](https://discord.com/developers/docs/intro)

The bot will require permissions to post messages in channels and manage events.

### Configure the App

Follow the example in config.json and fill out the fields:
```json
{
    "app_token": "app_token_placeholder",
    "admin_password": "123abc",
    "maintenance_mode": true
}
```
* app_token: this is provided by Discord when creating the Discord App.
* admin_password: this is used by super-admin to control the bot via discord commands.
* maintenance_mode: if the bot will start in maintenance mode.

### Install requirements
```sh
pip install -r requirements.txt
```

### Run the bot
```sh
python main.py
```
