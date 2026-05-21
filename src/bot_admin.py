import discord
from datetime import datetime


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
            description="Open tournament sign-ups until expiration datetime"
        )
        async def open_signups(
            ctx,
            expire_datetime: discord.Option(
                str,
                (
                    "Expiration datetime string "
                    "(ISO format, ex: 2026-05-21 18:30:00)"
                )
            ),  # type: ignore
            password: discord.Option(
                str, "Bot admin password"
            ),  # type: ignore
        ):
            await self.open_tournament_signups(
                ctx,
                expire_datetime,
                password
            )  # pragma: no cover

        @tournament.command(
            description="Check current tournament sign-up expiration"
        )
        async def status(ctx):
            await self.tournament_status(ctx)  # pragma: no cover

        @tournament.command(
            description="Close tournament sign-ups"
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

        expires_at = self.tournament_signup_expires_at
        if not expires_at:
            await ctx.respond(
                "No tournament sign-ups are currently open.",
                ephemeral=True
            )
            return

        await ctx.respond(
            f"Tournament sign-ups expire at {expires_at}",
            ephemeral=True
        )

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
