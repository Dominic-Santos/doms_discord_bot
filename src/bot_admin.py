import discord
from datetime import datetime


class TournamentCreateModal(discord.ui.Modal):
    def __init__(self, tournament_bot):
        super().__init__(title="Create Tournament")
        self.tournament_bot = tournament_bot

        self.name_input = discord.ui.InputText(
            label="Tournament name",
            placeholder="League Cup",
            required=True,
        )
        self.expire_datetime_input = discord.ui.InputText(
            label="Expiration datetime",
            placeholder="2026-05-21 18:30:00",
            required=True,
        )
        self.format_input = discord.ui.InputText(
            label="Tournament format",
            placeholder="standard or expanded",
            required=True,
        )
        self.password_input = discord.ui.InputText(
            label="Bot admin password",
            required=True,
        )

        for input_field in (
            self.name_input,
            self.expire_datetime_input,
            self.format_input,
            self.password_input,
        ):
            self.add_item(input_field)

    async def on_submit(self, interaction: discord.Interaction):
        await self.tournament_bot.create_tournament(
            ModalInteractionContext(interaction),
            self.name_input.value,
            self.expire_datetime_input.value,
            self.format_input.value,
            self.password_input.value,
        )


class ModalInteractionContext:
    def __init__(self, interaction: discord.Interaction):
        self.interaction = interaction
        self.guild = interaction.guild

    async def defer(self, ephemeral=False):
        await self.interaction.response.defer(ephemeral=ephemeral)

    async def respond(self, message, ephemeral=False):
        await self.interaction.followup.send(message, ephemeral=ephemeral)


class AdminBot:
    def add_admin_commands(self):
        maintenance = self.admin.create_subgroup(
            "maintenance", "Manage bot maintenance"
        )
        tournament = self.admin.create_subgroup(
            "tournament", "Manage tournament sign-up windows"
        )

        @maintenance.command(
            description="Check if the bot is in maintenance mode"
        )
        async def check(ctx):
            await self.maintenance_status(ctx)  # pragma: no cover

        @maintenance.command(description="Toggle bot maintenance mode")
        async def toggle(
            ctx,
            password: discord.Option(
                str, "Bot admin password"
            ),  # type: ignore
        ):
            await self.toggle_maintenance(ctx, password)  # pragma: no cover

        @tournament.command(
            description="Create a new tournament"
        )
        async def create(ctx):
            await ctx.send_modal(TournamentCreateModal(self))

        @tournament.command(
            description="List all tournaments"
        )
        async def list_tournaments(ctx):
            await self.list_tournaments(ctx)  # pragma: no cover

        @tournament.command(
            description="Delete a tournament"
        )
        async def delete(
            ctx,
            tournament_id: discord.Option(
                str, "Tournament ID to delete"
            ),  # type: ignore
            password: discord.Option(
                str, "Bot admin password"
            ),  # type: ignore
        ):
            await self.delete_tournament(
                ctx,
                tournament_id,
                password
            )  # pragma: no cover

        @tournament.command(
            description="Check current tournament sign-up expiration"
        )
        async def status(ctx):
            await self.tournament_status(ctx)  # pragma: no cover

        @tournament.command(
            description="Close tournament sign-ups (deprecated - use individual tournament deletion)"
        )
        async def close_signups(
            ctx,
            password: discord.Option(
                str, "Bot admin password"
            ),  # type: ignore
        ):
            await self.close_tournament_signups(
                ctx,
                password
            )  # pragma: no cover

    async def maintenance_status(self, ctx):
        await ctx.defer(ephemeral=True)

        status = "on" if self.maintenance else "off"
        await ctx.respond(f"Maintenance mode: {status}", ephemeral=True)

    async def toggle_maintenance(self, ctx, password: str):
        await ctx.defer(ephemeral=True)

        if password != self.password:
            await ctx.respond("Invalid admin password", ephemeral=True)
            return

        self.maintenance = not self.maintenance

        status = "on" if self.maintenance else "off"
        await ctx.respond(f"Maintenance mode: {status}", ephemeral=True)

    async def open_tournament_signups(
        self,
        ctx,
        expire_datetime: str,
        password: str
    ):
        await ctx.defer(ephemeral=True)

        if password != self.password:
            await ctx.respond("Invalid admin password", ephemeral=True)
            return

        try:
            expire = datetime.fromisoformat(expire_datetime.strip())
            if expire.tzinfo is not None:
                expire = expire.astimezone().replace(tzinfo=None)
        except ValueError:
            await ctx.respond(
                "Invalid datetime format. Use ISO format, for example: "
                "2026-05-21 18:30:00",
                ephemeral=True
            )
            return

        self.tournament_signup_expires_at = expire.isoformat(
            sep=" ", timespec="seconds"
        )
        self.tournament_signups[str(ctx.guild.id)] = []
        await ctx.respond(
            (
                "Tournament sign-ups are now open until "
                f"{self.tournament_signup_expires_at}"
            ),
            ephemeral=True
        )

    async def tournament_status(self, ctx):
        await ctx.defer(ephemeral=True)

        if not self.tournaments:
            await ctx.respond(
                "No tournaments created yet.",
                ephemeral=True
            )
            return

        tournament_list = "**Tournament Status:**\n"
        now = datetime.now()
        
        for tournament_id, tournament_data in self.tournaments.items():
            name = tournament_data.get("name", tournament_id)
            expires_at = tournament_data.get("expires_at", "Unknown")
            
            try:
                expire_datetime = datetime.fromisoformat(expires_at)
                status = "OPEN" if now <= expire_datetime else "CLOSED"
            except ValueError:
                status = "INVALID"
            
            tournament_format = tournament_data.get("format", "Unknown")
            tournament_list += (
                f"\n**{name}** (ID: `{tournament_id}`)"
                f"  Format: {tournament_format}\n"
                f"  Status: {status}\n"
                f"  Expires: {expires_at}\n"
            )

        await ctx.respond(tournament_list, ephemeral=True)

    async def close_tournament_signups(self, ctx, password: str):
        await ctx.defer(ephemeral=True)

        if password != self.password:
            await ctx.respond("Invalid admin password", ephemeral=True)
            return

        self.tournament_signup_expires_at = None
        await ctx.respond(
            "Tournament sign-ups are now closed.",
            ephemeral=True
        )

    async def create_tournament(
        self,
        ctx,
        name: str,
        expire_datetime: str,
        format: str,
        password: str
    ):
        await ctx.defer(ephemeral=True)

        if password != self.password:
            await ctx.respond("Invalid admin password", ephemeral=True)
            return

        try:
            expire = datetime.fromisoformat(expire_datetime.strip())
            if expire.tzinfo is not None:
                expire = expire.astimezone().replace(tzinfo=None)
        except ValueError:
            await ctx.respond(
                "Invalid datetime format. Use ISO format, for example: "
                "2026-05-21 18:30:00",
                ephemeral=True
            )
            return

        # Create tournament ID from name (lowercase, replace spaces with underscores)
        tournament_id = name.lower().replace(" ", "_")
        
        # Ensure unique ID
        if tournament_id in self.tournaments:
            counter = 1
            while f"{tournament_id}_{counter}" in self.tournaments:
                counter += 1
            tournament_id = f"{tournament_id}_{counter}"

        self.tournaments[tournament_id] = {
            "name": name,
            "format": format,
            "expires_at": expire.isoformat(sep=" ", timespec="seconds"),
            "created_at": datetime.now().isoformat(sep=" ", timespec="seconds")
        }
        
        self.save_tournaments()
        
        await ctx.respond(
            (
                f"Tournament '{name}' created successfully!\n"
                f"ID: {tournament_id}\n"
                f"Expires at: {self.tournaments[tournament_id]['expires_at']}"
            ),
            ephemeral=True
        )

    async def list_tournaments(self, ctx):
        await ctx.defer(ephemeral=True)

        if not self.tournaments:
            await ctx.respond(
                "No tournaments created yet.",
                ephemeral=True
            )
            return

        tournament_list = "**Tournaments:**\n"
        now = datetime.now()
        
        for tournament_id, tournament_data in self.tournaments.items():
            name = tournament_data.get("name", tournament_id)
            expires_at = tournament_data.get("expires_at", "Unknown")
            tournament_format = tournament_data.get("format", "Unknown")
            
            try:
                expire_datetime = datetime.fromisoformat(expires_at)
                status = "OPEN" if now <= expire_datetime else "CLOSED"
            except ValueError:
                status = "INVALID"
            
            tournament_list += (
                f"\n**{name}** (ID: `{tournament_id}`)\n"
                f"  Format: {tournament_format}\n"
                f"  Status: {status}\n"
                f"  Expires: {expires_at}\n"
            )

        await ctx.respond(tournament_list, ephemeral=True)

    async def delete_tournament(
        self,
        ctx,
        tournament_id: str,
        password: str
    ):
        await ctx.defer(ephemeral=True)

        if password != self.password:
            await ctx.respond("Invalid admin password", ephemeral=True)
            return

        if tournament_id not in self.tournaments:
            await ctx.respond(
                f"Tournament '{tournament_id}' not found.",
                ephemeral=True
            )
            return

        tournament_name = self.tournaments[tournament_id].get("name", tournament_id)
        del self.tournaments[tournament_id]
        self.save_tournaments()

        await ctx.respond(
            f"Tournament '{tournament_name}' has been deleted.",
            ephemeral=True
        )
