import json
import re

from .pokebeach import get_newsfeed
from .helpers import CustomThread, MAINTENANCE_MODE_MESSAGE
from .core import DATA_FOLDER

NEWSFEED_CHANNELS_FILE = f"{DATA_FOLDER}/newsfeed_channels.json"


THREAD_ID_RE = re.compile(r"\.(\d+)/?$")


def post_id(post):
    match = THREAD_ID_RE.search(post)
    return int(match.group(1)) if match else None


def newest_post(posts):
    with_ids = [p for p in posts if post_id(p) is not None]
    return max(with_ids, key=post_id) if with_ids else posts[0]


class NewsfeedBot:
    def load_newsfeed_channels(self):
        try:
            with open(NEWSFEED_CHANNELS_FILE, "r") as f:
                self.newsfeed_channels = json.load(f)
        except Exception as e:
            self.logger.warning(f"Error loading {NEWSFEED_CHANNELS_FILE}: {e}")
            self.newsfeed_channels = {}

    def save_newsfeed_channels(self):
        try:
            with open(NEWSFEED_CHANNELS_FILE, "w") as f:
                json.dump(self.newsfeed_channels, f, indent=4)
        except Exception as e:
            self.logger.error(f"Error saving {NEWSFEED_CHANNELS_FILE}: {e}")

    def add_newsfeed_commands(self):
        newsfeed = self.bot.create_group("newsfeed", "Manage newsfeed posts")
        pokemon = newsfeed.create_subgroup("pokemon", "pokemon tcg")

        @pokemon.command(description="Set the newsfeed channel")
        async def set_channel(ctx):
            await self.set_newsfeed_channel(ctx)  # pragma: no cover

        @pokemon.command(description="Check for newsfeed updates")
        async def update(ctx):
            await self.get_newsfeed(ctx)  # pragma: no cover

        @pokemon.command(description="Disable newsfeed updates")
        async def disable(ctx):
            await self.disable_newsfeed(ctx)  # pragma: no cover

    async def set_newsfeed_channel(self, ctx):
        channel_id = ctx.channel.id
        if str(ctx.guild.id) not in self.newsfeed_channels:
            self.newsfeed_channels[str(ctx.guild.id)] = {}
        self.newsfeed_channels[str(ctx.guild.id)]["channel_id"] = channel_id
        self.save_newsfeed_channels()
        await ctx.respond(
            f"Newsfeed channel set to {ctx.channel.name}!",
            ephemeral=True
        )

    async def disable_newsfeed(self, ctx):
        if str(ctx.guild.id) not in self.newsfeed_channels:
            await ctx.respond("Newsfeed already disabled!", ephemeral=True)
            return

        del self.newsfeed_channels[str(ctx.guild.id)]
        self.save_newsfeed_channels()
        await ctx.respond("Newsfeed disabled!", ephemeral=True)

    async def get_newsfeed(self, ctx):
        await ctx.defer(ephemeral=True)

        if self.maintenance:
            await ctx.respond(MAINTENANCE_MODE_MESSAGE, ephemeral=True)
            return

        await self.do_get_newsfeed()
        await ctx.respond("Newsfeed posts have been updated!", ephemeral=True)

    async def get_newsfeed_task(self):
        self.logger.info("Checking newsfeed posts...")

        if self.maintenance:
            self.logger.info("Won't get newsfeed, Maintenance mode is active")
            return

        await self.do_get_newsfeed()
        self.logger.info("Newsfeed posts updated successfully.")

    async def do_get_newsfeed(self):
        t = CustomThread(get_newsfeed)
        t.start()
        posts, _ = t.join()

        if not posts:
            self.logger.info("No newsfeed posts found.")
            return

        for guild_id, guild_config in self.newsfeed_channels.items():
            channel_id = guild_config.get("channel_id")

            latest_post = guild_config.get("latest_post", None)
            channel = self.bot.get_channel(int(channel_id))

            if not channel:
                self.logger.warning(
                    f"Channel {channel_id} not found in guild {guild_id}. "
                    "Skipping newsfeed post."
                )
                continue

            # the feed is ordered by activity, so bumped threads can appear at
            # the top; thread ids only increase, so compare by id instead
            latest_id = post_id(latest_post) if latest_post else None
            if latest_post is not None and latest_id is None:
                # previous post is from an unknown source, only remember the
                # newest id instead of posting the whole feed
                guild_config["latest_post"] = newest_post(posts)
                continue

            should_post = sorted(
                (p for p in posts
                 if post_id(p) is not None
                 and (latest_id is None or post_id(p) > latest_id)),
                key=post_id
            )

            for post in should_post:
                await channel.send(post)
                guild_config["latest_post"] = post

            if should_post:
                guild_config["latest_post"] = should_post[-1]
            elif latest_post is None:
                guild_config["latest_post"] = newest_post(posts)

        self.save_newsfeed_channels()
