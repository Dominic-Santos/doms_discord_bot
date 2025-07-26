from .core import  load_card_database
from .pkmncards import get_legal_cards

from .helpers import CustomThread


class LegalCardsBot:
   
    def load_legal_cards(self):
        try:
            legal_pokemon, legal_trainers, legal_energies = load_card_database()
            self.legal_cards = {
                "pokemon": legal_pokemon,
                "trainers": legal_trainers,
                "energies": legal_energies
            }
        except Exception as e:
            self.logger.info(f"Error loading legal cards database: {e}")
            self.legal_cards = None

    def get_legal_cards_task(self):
        self.logger.info("Updating legal cards...")
        self.do_get_legal_cards()
        self.logger.info("Legal cards updated successfully.")

    async def get_legal_cards(self, ctx):
        await ctx.defer(ephemeral=True)
        self.do_get_legal_cards()
        await ctx.respond("Legal cards list has been updated!", ephemeral=True)

    def do_get_legal_cards(self):
        t = CustomThread(get_legal_cards)
        t.start()
        t.join()
        self.load_legal_cards()
