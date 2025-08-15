from .core import load_card_database
from .pkmncards import get_legal_cards

from .helpers import CustomThread, MAINTENANCE_MODE_MESSAGE


class LegalCardsBot:
    def load_legal_cards(self):
        try:
            pokemon, trainers, energies = load_card_database()
            self.legal_cards = {
                "pokemon": pokemon,
                "trainers": trainers,
                "energies": energies
            }
        except Exception as e:
            self.logger.info(f"Error loading legal cards database: {e}")
            self.legal_cards = None

    def get_legal_cards_task(self):
        self.logger.info("Updating legal cards...")
        if self.maintenance:
            self.logger.info(
                "Won't update legal cards, Maintenance mode is active"
            )
            return

        error = self.do_get_legal_cards()
        if error is not None:
            self.logger.error(f"Legal cards update failed. {error}")
            return
        self.logger.info("Legal cards updated successfully.")

    async def get_legal_cards(self, ctx):
        await ctx.defer(ephemeral=True)

        if self.maintenance:
            await ctx.respond(MAINTENANCE_MODE_MESSAGE, ephemeral=True)
            return

        error = self.do_get_legal_cards()
        if error is not None:
            await ctx.respond(
                f"Legal cards update failed! {error}",
                ephemeral=True
            )
            return

        await ctx.respond("Legal cards list has been updated!", ephemeral=True)

    def do_get_legal_cards(self):
        t = CustomThread(get_legal_cards)
        t.start()
        _, error = t.join()
        self.load_legal_cards()
        return error
