import os
import discord
import json

from .limitless import get_decklist_from_url
from .core import validate_decklist, fill_sheet
from .pokemon import get_decklist_png as get_sign_up_sheet

from .helpers import CustomThread

class DecklistBot:
    def load_output_channels(self):
        try:
            with open("output_channels.json", "r") as f:
                self.output_channels = json.load(f)
        except Exception as e:
            self.logger.info(f"Error loading output_channels.json: {e}")
            self.output_channels = {}

    def save_output_channels(self):
        try:
            with open("output_channels.json", "w") as f:
                json.dump(self.output_channels, f, indent=4)
        except Exception as e:
            self.logger.error(f"Error saving output_channels.json: {e}")

    async def set_output_channel(self, ctx):
        channel_id = ctx.channel.id
        self.output_channels[str(ctx.guild.id)] = channel_id
        self.save_output_channels()
        await ctx.respond(f"Output channel set to {ctx.channel.name}!", ephemeral=True)

    async def test_output_channel(self, ctx):
        channel, error = self.get_output_channel(str(ctx.guild.id))

        if channel is None:
            await ctx.respond(error, ephemeral=True)
            return
        
        await channel.send("This is a test message from the bot!")
        await ctx.respond("Test message sent to the output channel!", ephemeral=True)

    def get_output_channel(self, guild_id: str) -> tuple[discord.TextChannel | None, str]:
        if guild_id not in self.output_channels:
            return None, "Output channel is not set for this server."

        channel_id = self.output_channels[guild_id]
        channel = self.bot.get_channel(channel_id)
        if channel:
            return channel, ""

        return None, "Output channel not found. Please set it again."

    async def decklist_check(self, ctx, deck):
        await ctx.defer(ephemeral=True)
        valid, _, error = self.do_decklist_check(deck)
        if not valid:
            await ctx.respond(f"Decklist is not valid: {error}", ephemeral=True)
            return
        await ctx.respond("Decklist is valid!", ephemeral=True)

    def do_decklist_check(self, limitless_url: str) -> tuple[bool, dict, str]:
        valid = self.check_limitless_url(limitless_url)
        if not valid:
            return False, {}, "Invalid Limitless URL."
        t = CustomThread(get_decklist_from_url, args=(limitless_url,))
        t.start()
        deck_data = t.join()
        valid, error = validate_decklist(deck_data, self.legal_cards)
        return valid, deck_data, error

    async def tournament_signup(self, ctx, full_name: str, pokemon_id: int, year_of_birth: int, limitless_url: str):
        await ctx.defer(ephemeral=True)

        if not self.legal_cards:
            await ctx.respond("Legal cards are not loaded. Please try again later.", ephemeral=True)
            return
        
        channel, error = self.get_output_channel(str(ctx.guild.id))
        if channel is None:
            await ctx.respond(error, ephemeral=True)
            return
        
        if not self.check_sign_up_sheet():
            await ctx.respond("Sign-up sheet is not available. Please try again later.", ephemeral=True)
            return

        valid, deck_data, error = self.do_decklist_check(limitless_url)
        if not valid:
            await ctx.respond(f"Decklist is not valid: {error}", ephemeral=True)
            return
        
        output_filename = f"sign_up_sheet_{ctx.guild.id}_{ctx.author.id}.png"

        fill_sheet(
            player={
                "name": full_name,
                "pokemon_id": pokemon_id,
                "year_of_birth": year_of_birth
            },
            cards=deck_data,
            output_filename=output_filename
        )

        await channel.send(
            f"New tournament signup:\n- Name: {full_name}\n- Pokémon ID: {pokemon_id}\n- Year of Birth: {year_of_birth}\n- Decklist: {limitless_url}",
            file=discord.File(output_filename, filename="sign_up_sheet.png")
        )
        
        await ctx.respond(
            "Tournament signup has been processed!",
            ephemeral=True,
            file=discord.File(output_filename, filename="sign_up_sheet.png")
        )

        os.remove(output_filename)  # Clean up the temporary file
    
    async def update_signup_sheet(self, ctx):
        await ctx.defer(ephemeral=True)
        self.do_update_sheet()
        await ctx.respond("Sheet has been updated!", ephemeral=True)

    def update_signup_sheet_task(self):
        self.logger.info("Updating sign-up sheet...")
        self.do_update_sheet()
        self.logger.info("Sign-up sheet updated successfully.")

    def do_update_sheet(self):
        t = CustomThread(get_sign_up_sheet)
        t.start()
        t.join()

    def check_limitless_url(self, url: str) -> tuple[bool]:
        if url.startswith("https://my.limitlesstcg.com/builder?i="):
            return True
        if url.startswith("http://my.limitlesstcg.com/builder?i="):
            return True
        if url.startswith("my.limitlesstcg.com/builder?i="):
            return True
        return False

    def check_sign_up_sheet(self):
        return os.path.exists("sign_up_sheet.png")
