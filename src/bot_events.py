import json
import discord
import requests
from datetime import datetime, timedelta

from .pokemon import (
    get_store_events, get_premier_events,
    POKEMON_EVENTS_BASE_URL, Pokemon_Event
)
from .helpers import MAINTENANCE_MODE_MESSAGE, CustomThread


class EventsBot:
    def load_events_data(self):
        try:
            with open("events_data.json", "r") as f:
                data = json.load(f)
                self.events_following = data.get("events", {})
                self.premier_following = data.get("premier", {})
                self.event_channels = data.get("channels", {})
        except Exception as e:
            self.logger.warning(f"Error loading events_data.json: {e}")
            self.events_following = {}
            self.premier_following = {}
            self.event_channels = {}

    def save_events_data(self):
        try:
            data = {
                "events": self.events_following,
                "premier": self.premier_following,
                "channels": self.event_channels
            }
            with open("events_data.json", "w") as f:
                json.dump(data, f, indent=4)
        except Exception as e:
            self.logger.error(f"Error saving events_data.json: {e}")

    def add_event_commands(self):
        events = self.bot.create_group("events", "Events commands")

        @events.command(
            name="follow_premier",
            description="Follow premier events"
        )
        async def follow_premier_events(ctx):
            await self.follow_premier_events(ctx)  # pragma: no cover

        @events.command(
            name="unfollow_premier",
            description="Unfollow premier events"
        )
        async def unfollow_premier_events(ctx):
            await self.unfollow_premier_events(ctx)  # pragma: no cover

        @events.command(description="Unfollow all store events")
        async def unfollow_all(ctx):
            await self.unfollow_all_events(ctx)  # pragma: no cover

        @events.command(
            name="follow_store",
            description="Follow store events"
        )
        async def follow_events(
            ctx,
            guid: discord.Option(
                str, "Store GUID on event locator"
            ),  # type: ignore
        ):
            await self.follow_events(ctx, guid)  # pragma: no cover

        @events.command(
            name="unfollow_store",
            description="Unfollow store events"
        )
        async def unfollow_events(
            ctx,
            guid: discord.Option(
                str, "Store GUID on event locator"
            ),  # type: ignore
        ):
            await self.unfollow_events(ctx, guid)  # pragma: no cover

        @events.command(
            name="sync",
            description="Sync events"
        )
        async def sync_events(ctx):
            await self.sync_events(ctx)  # pragma: no cover

        @events.command(description="Cancel all events")
        async def delete_all(ctx):
            await self.delete_all_events(ctx)  # pragma: no cover

        @events.command(description="Set event updates channel")
        async def set_channel(ctx):
            await self.set_events_channel(ctx)  # pragma: no cover

        @events.command(description="Remove event updates channel")
        async def remove_channel(ctx):
            await self.remove_events_channel(ctx)  # pragma: no cover

    async def follow_premier_events(self, ctx):
        guild_id = str(ctx.guild.id)
        self.premier_following[guild_id] = True
        self.save_events_data()
        await ctx.respond(
            "Following premier events!",
            ephemeral=True
        )

    async def unfollow_premier_events(self, ctx):
        guild_id = str(ctx.guild.id)
        self.premier_following[guild_id] = False
        self.save_events_data()
        await ctx.respond(
            "Not following premier events!",
            ephemeral=True
        )

    async def follow_events(self, ctx, guid: str):
        guild_id = str(ctx.guild.id)
        if guild_id not in self.events_following:
            self.events_following[guild_id] = []

        if guid in self.events_following[guild_id]:
            await ctx.respond(
                f"Already following {guid}",
                ephemeral=True
            )
            return

        self.events_following[guild_id].append(guid)
        self.save_events_data()
        await ctx.respond(
            f"Following events from {guid}",
            ephemeral=True
        )

    async def unfollow_events(self, ctx, guid: str):
        guild_id = str(ctx.guild.id)
        if guild_id not in self.events_following:
            self.events_following[guild_id] = []

        if guid not in self.events_following[guild_id]:
            await ctx.respond(
                f"Not following {guid}",
                ephemeral=True
            )
            return

        self.events_following[guild_id].remove(guid)
        self.save_events_data()
        await ctx.respond(
            f"Stopped following events from {guid}",
            ephemeral=True
        )

    async def unfollow_all_events(self, ctx):
        guild_id = str(ctx.guild.id)
        self.events_following[guild_id] = []
        self.premier_following[guild_id] = False

        self.save_events_data()
        await ctx.respond(
            "Stopped following all events",
            ephemeral=True
        )

    async def sync_events(self, ctx):
        await ctx.defer(ephemeral=True)
        if self.maintenance:
            await ctx.respond(MAINTENANCE_MODE_MESSAGE, ephemeral=True)
            return

        guild_id = str(ctx.guild.id)
        stores = self.events_following.get(guild_id, [])
        premier = self.premier_following.get(guild_id, False)

        if len(stores) == 0 and not premier:
            await ctx.respond("Nothing to sync", ephemeral=True)
            return

        events = []
        if premier:
            t = CustomThread(get_premier_events)
            t.start()
            data, _ = t.join()
            events += data

        if len(stores) > 0:
            t = CustomThread(get_store_events, kwargs={"guids": stores})
            t.start()
            store_events, _ = t.join()
            for store in stores:
                for event in store_events[store]:
                    events.append(event)

        await self.update_guild_events(ctx.guild.id, events)

        await ctx.respond(
            "Events synced successfully!",
            ephemeral=True
        )

    async def delete_all_events(self, ctx):
        await ctx.defer(ephemeral=True)
        guild = await self.bot.fetch_guild(ctx.guild.id)
        channel = self.event_channels.get(str(ctx.guild.id), None)
        if channel is not None:
            channel = self.bot.get_channel(int(channel))

        guild_events = await guild.fetch_scheduled_events()
        for event in guild_events:
            if event.creator_id == self.bot.user.id:
                await event.cancel()

                if channel is None:
                    continue

                event_text = self.print_event(event, with_url=False)
                await channel.send(
                    "An event was canceled!\n" + event_text
                )

        await ctx.respond(
            "Events deleted successfully!",
            ephemeral=True
        )

    async def sync_events_task(self):
        self.logger.info("Checking events...")

        if self.maintenance:
            self.logger.info("Won't sync events, Maintenance mode is active")
            return

        await self.do_sync_events()
        self.logger.info("Events updated successfully.")

    async def update_guild_events(
        self,
        guild_id: int,
        events: list[Pokemon_Event]
    ):
        guild = await self.bot.fetch_guild(guild_id)
        channel = self.event_channels.get(str(guild_id), None)
        if channel is not None:
            channel = self.bot.get_channel(int(channel))

        guild_events = await guild.fetch_scheduled_events()
        bot_events = [
            e for e in guild_events if e.creator_id == self.bot.user.id
        ]
        keep_events = []

        for event in events:
            if event.start_date < datetime.now():
                continue

            already_exists = False
            for g_event in bot_events:
                g_start = g_event.start_time.replace(tzinfo=None)
                g_end = g_event.end_time.replace(tzinfo=None)
                if (
                    g_event.name == event.name and
                    g_start == event.start_date and
                    g_end == event.end_date
                ):
                    keep_events.append(g_event)
                    already_exists = True
                    break

            if already_exists:
                continue

            kwargs = {
                "name": event.name,
                "location": event.location,
                "privacy_level": discord.ScheduledEventPrivacyLevel.guild_only,
                "description": event.type,
                "start_time": event.start_date,
                "end_time": event.end_date
            }

            url = f"{POKEMON_EVENTS_BASE_URL}{event.logo}"
            response = requests.get(url)

            if response.status_code == 200:
                kwargs["image"] = response.content

            new_event = await guild.create_scheduled_event(**kwargs)

            if channel is None:
                continue

            event_text = self.print_event(new_event)
            await channel.send(
                "An event was created!\n" + event_text
            )

        # Clean all old events:
        for event in bot_events:
            # Skip if already started
            if event.start_time.replace(tzinfo=None) < datetime.now():
                continue

            # Skip if event still exists
            if event in keep_events:
                continue

            # Delete the event
            await event.cancel()

            if channel is None:
                continue

            event_text = self.print_event(event, with_url=False)
            await channel.send(
                "An event was canceled!\n" + event_text
            )

    @staticmethod
    def print_event(event, with_url: bool = True) -> str:
        text = f"{event.name}\n{event.location}\n"

        start_date = event.start_time.date()
        end_date = (event.end_time - timedelta(days=1)).date()

        text += f"{start_date}"
        if end_date != start_date:
            text += f"/{end_date}"

        if with_url:
            text += f"\n\n{event.url}"
        return text

    async def set_events_channel(self, ctx):
        channel_id = ctx.channel.id
        self.event_channels[str(ctx.guild.id)] = channel_id

        self.save_events_data()
        await ctx.respond(
            "Events channel set successfully!",
            ephemeral=True
        )

    async def remove_events_channel(self, ctx):
        guild_id = str(ctx.guild.id)
        if guild_id in self.event_channels:
            del self.event_channels[guild_id]

        self.save_events_data()
        await ctx.respond(
            "Events channel removed successfully!",
            ephemeral=True
        )

    async def do_sync_events(self):
        get_premier = any(self.premier_following.values())
        all_guids = [
            guid
            for guid_list in self.events_following.values()
            for guid in guid_list
        ]
        unique_guids = list(set(all_guids))

        premier_events = []
        if get_premier:
            t = CustomThread(get_premier_events)
            t.start()
            data, _ = t.join()
            premier_events = data

        store_events = {}
        if len(unique_guids) > 0:
            t = CustomThread(get_store_events, kwargs={"guids": unique_guids})
            t.start()
            store_events, _ = t.join()

        premier_servers = list(self.premier_following.keys())
        store_servers = list(self.events_following.keys())
        servers = list(set(premier_servers + store_servers))

        for server in servers:
            s_events = []
            s_premier = self.premier_following.get(server, False)
            s_stores = self.events_following.get(server, [])
            if s_premier:
                s_events += premier_events
            for store in s_stores:
                for event in store_events.get(store, []):
                    s_events.append(event)

            if len(s_events) == 0:
                self.logger.info(f"Skipping events for {server}.")
                continue

            self.logger.info(f"Syncing events for {server}.")
            await self.update_guild_events(int(server), s_events)
