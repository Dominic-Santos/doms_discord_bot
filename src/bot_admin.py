import discord


class AdminBot:
    def add_admin_commands(self):
        maintenance = self.admin.create_subgroup(
            "maintenance", "Manage bot maintenance"
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
