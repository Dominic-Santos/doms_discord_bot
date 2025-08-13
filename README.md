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
        <li><a href="#configure-the-app">Configure the App</a></li>
        <li><a href="#install-requirements">Install requirements</a></li>
      </ul>
    </li>
  </ol>
</details>


<!-- ABOUT THE PROJECT -->
## About The Project

This is a passion project aimed at providing better tools and automation for my local game store. As a Pokémon Professor (Judge), I found the official tools to be severely lacking. To help alleviate some of the pain points, I’ve been developing this bot with features designed to keep the community informed and streamline daily operations — from deck checks to sign-ups and more.

## Create your own bot

If you wish to run your own version of the bot, feel free to fork/use/copy the code in this repo :smiley: a mention is always apreciated

### Discord App

You will need to create a discord app, follow the guide [here](https://discord.com/developers/docs/intro)

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
