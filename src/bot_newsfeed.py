import json

from .pokebeach import get_newsfeed
from .helpers import CustomThread, MAINTENANCE_MODE_MESSAGE


class NewsfeedBot:
    def load_newsfeed_channels(self):
        try:
            with open("newsfeed_channels.json", "r") as f:
                self.newsfeed_channels = json.load(f)
        except Exception as e:
            self.logger.info(f"Error loading newsfeed_channels.json: {e}")
            self.newsfeed_channels = {}

    def save_newsfeed_channels(self):
        try:
            with open("newsfeed_channels.json", "w") as f:
                json.dump(self.newsfeed_channels, f, indent=4)
        except Exception as e:
            self.logger.error(f"Error saving newsfeed_channels.json: {e}")

    async def set_newsfeed_channel(self, ctx):
        channel_id = ctx.channel.id
        if str(ctx.guild.id) not in self.newsfeed_channels:
            self.newsfeed_channels[str(ctx.guild.id)] = {}
        self.newsfeed_channels[str(ctx.guild.id)]["channel_id"] = channel_id
        self.save_newsfeed_channels()
        await ctx.respond(f"Newsfeed channel set to {ctx.channel.name}!", ephemeral=True)

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
                self.logger.warning(f"Channel {channel_id} not found in guild {guild_id}. Skipping newsfeed post.")
                continue

            should_post = []
            for post in posts:
                if post == latest_post:
                    break

                should_post.append(post)
                
            for post in should_post[::-1]:
                await channel.send(post)

            self.newsfeed_channels[guild_id]["latest_post"] = posts[0]

        self.save_newsfeed_channels()
