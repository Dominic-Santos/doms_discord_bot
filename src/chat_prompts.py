import discord


async def send_prompt(ctx, message, **kwargs):
    if ctx.response.is_done():
        return await ctx.followup.send(message, **kwargs)
    return await ctx.respond(message, **kwargs)


class PromptContext:
    def __init__(self, ctx):
        self.ctx = ctx

    def __getattr__(self, name):
        return getattr(self.ctx, name)

    async def defer(self, ephemeral=False):
        return

    async def respond(self, message, ephemeral=False):
        await self.ctx.followup.send(message, ephemeral=ephemeral)


class ChoiceView(discord.ui.View):
    def __init__(self, label, choices):
        super().__init__(timeout=120)
        self.choice = None

        select = discord.ui.Select(
            placeholder=label,
            options=[
                discord.SelectOption(label=choice, value=choice)
                for choice in choices
            ],
        )

        async def select_callback(interaction):
            self.choice = select.values[0]
            await interaction.response.edit_message(
                content=f"Selected: {self.choice}",
                view=None,
            )
            self.stop()

        select.callback = select_callback
        self.add_item(select)


async def prompt_text(ctx, label, timeout=120):
    await send_prompt(ctx, label, ephemeral=True)

    def check(message):
        return (
            message.author.id == ctx.author.id and
            message.channel.id == ctx.channel.id
        )

    message = await ctx.bot.wait_for("message", check=check, timeout=timeout)
    try:
        await message.delete()
    except discord.HTTPException:
        pass
    return message.content.strip()


async def prompt_choice(ctx, label, choices, timeout=120):
    view = ChoiceView(label, choices)
    await send_prompt(ctx, label, view=view, ephemeral=True)
    await view.wait()
    return view.choice


async def run_chat_prompt(ctx, fields, handler):
    values = {}
    try:
        for field in fields:
            name, label, field_type = field[:3]
            if field_type == "choice":
                values[name] = await prompt_choice(ctx, label, field[3])
            else:
                values[name] = await prompt_text(ctx, label)
                if field_type is int:
                    values[name] = int(values[name])
    except (ValueError, TimeoutError):
        await send_prompt(
            ctx,
            "The prompt timed out or contained an invalid value.",
            ephemeral=True,
        )
        return

    await handler(PromptContext(ctx), values)