from __future__ import annotations

import discord

from ..infra.logging import get_logger
from ..infra.settings import settings
from ..infra.date_parsing import parse_natural_range
from ..infra.db import session_scope
from ..infra.repo import get_user_token_by_discord_id
from ..adapters.gcal import (
    get_freebusy, create_event, list_events, 
    suggest_meeting_times, create_recurring_event, build_rrule
)
from ..infra.metrics import events_created_total
from ..infra.rate_limit import check_rate_limit
from ..domain.models import GuildSettings, User, EventTemplate
from sqlalchemy import select, update, insert
from datetime import datetime, timezone


logger = get_logger().bind(service="discord")


class DiscordClient(discord.Client):
    def __init__(self, *, intents: discord.Intents) -> None:
        super().__init__(intents=intents)
        self.tree = discord.app_commands.CommandTree(self)

    async def setup_hook(self) -> None:
        await self.tree.sync()


def build_bot() -> DiscordClient:
    intents = discord.Intents.default()
    client = DiscordClient(intents=intents)

    @client.tree.command(name="ping", description="Ping the bot")
    async def ping_command(interaction: discord.Interaction) -> None:
        await interaction.response.send_message("pong", ephemeral=True)
        logger.info("ping", interaction_id=str(interaction.id))

    @client.tree.command(name="connect", description="Link Google Account")
    async def connect_command(interaction: discord.Interaction) -> None:
        user_id = interaction.user.id
        base = f"http://{settings.http_host}:{settings.http_port}"
        url = f"{base}/oauth/start?discord_id={user_id}"
        await interaction.response.send_message(f"Connect your Google: {url}", ephemeral=True)
        logger.info("connect_link_sent", interaction_id=str(interaction.id))

    @client.tree.command(name="addevent", description="Create a calendar event")
    async def addevent_command(
        interaction: discord.Interaction,
        title: str,
        when: str,
        attendees: str | None = None,
        location: str | None = None,
        remind_minutes: int | None = None,
    ) -> None:
        await interaction.response.defer(ephemeral=True)
        tz = settings.default_tz
        try:
            start_dt, end_dt = parse_natural_range(when, tz)
        except Exception:
            await interaction.followup.send("Sorry, I couldn't parse the time. Try e.g. 'tomorrow 3-4pm'.", ephemeral=True)
            return

        async with session_scope() as session:
            token = await get_user_token_by_discord_id(session, str(interaction.user.id))
        if not token:
            await interaction.followup.send("Please /connect your Google account first.", ephemeral=True)
            return

        time_min = start_dt.astimezone(timezone.utc).isoformat()
        time_max = end_dt.astimezone(timezone.utc).isoformat()
        if not check_rate_limit(f"gcal:{interaction.user.id}"):
            await interaction.followup.send("Rate limit exceeded. Try again shortly.", ephemeral=True)
            return
        fb = await get_freebusy(token, time_min, time_max)
        busy = fb.get("calendars", {}).get("primary", {}).get("busy", [])
        if busy:
            await interaction.followup.send("That time looks busy. Please choose another slot.", ephemeral=True)
            return

        body = {
            "summary": title,
            "start": {"dateTime": start_dt.isoformat()},
            "end": {"dateTime": end_dt.isoformat()},
        }
        if location:
            body["location"] = location
        if attendees:
            body["attendees"] = [{"email": e.strip()} for e in attendees.split(",") if e.strip()]

        ev = await create_event(token, body)
        html_link = ev.get("htmlLink", "(no link)")
        await interaction.followup.send(f"Created: {html_link}", ephemeral=True)
        events_created_total.inc()

    @client.tree.command(name="myevents", description="List upcoming events")
    async def myevents_command(
        interaction: discord.Interaction,
        n: int = 5,
    ) -> None:
        await interaction.response.defer(ephemeral=True)
        async with session_scope() as session:
            token = await get_user_token_by_discord_id(session, str(interaction.user.id))
        if not token:
            await interaction.followup.send("Please /connect your Google account first.", ephemeral=True)
            return
        now = datetime.now(timezone.utc).isoformat()
        if not check_rate_limit(f"gcal:{interaction.user.id}"):
            await interaction.followup.send("Rate limit exceeded. Try again shortly.", ephemeral=True)
            return
        res = await list_events(token, time_min=now, max_results=n)
        items = res.get("items", [])
        if not items:
            await interaction.followup.send("No upcoming events.", ephemeral=True)
            return
        lines = []
        for it in items:
            start = it.get("start", {}).get("dateTime") or it.get("start", {}).get("date")
            lines.append(f"- {start} — {it.get('summary','(no title)')}")
        await interaction.followup.send("\n".join(lines), ephemeral=True)

    @client.tree.command(name="set_tz", description="Set your default timezone")
    async def set_tz_command(interaction: discord.Interaction, tz: str) -> None:
        await interaction.response.defer(ephemeral=True)
        async with session_scope() as session:
            # upsert user record
            res = await session.execute(select(User).where(User.discord_id == str(interaction.user.id)))
            user = res.scalars().first()
            if user:
                await session.execute(update(User).where(User.id == user.id).values(tz=tz))
            else:
                await session.execute(insert(User).values(discord_id=str(interaction.user.id), tz=tz))
            await session.commit()
        await interaction.followup.send(f"Timezone set to {tz}", ephemeral=True)

    @client.tree.command(name="set_channel", description="Set default events channel for this server")
    async def set_channel_command(interaction: discord.Interaction, channel: discord.TextChannel) -> None:
        await interaction.response.defer(ephemeral=True)
        if not interaction.guild or not interaction.user.guild_permissions.manage_guild:
            await interaction.followup.send("Admin only.", ephemeral=True)
            return
        async with session_scope() as session:
            res = await session.execute(select(GuildSettings).where(GuildSettings.guild_id == str(interaction.guild.id)))
            gs = res.scalars().first()
            if gs:
                await session.execute(update(GuildSettings).where(GuildSettings.id == gs.id).values(default_channel_id=str(channel.id)))
            else:
                await session.execute(insert(GuildSettings).values(guild_id=str(interaction.guild.id), default_channel_id=str(channel.id)))
            await session.commit()
        await interaction.followup.send(f"Default channel set to {channel.mention}", ephemeral=True)

    @client.tree.command(name="schedule", description="Find optimal meeting times for multiple attendees")
    async def schedule_command(
        interaction: discord.Interaction,
        title: str,
        duration_minutes: int = 60,
        attendees: str | None = None,
        days_ahead: int = 7,
        preferred_start_hour: int = 9,
        preferred_end_hour: int = 17,
    ) -> None:
        """Smart scheduling command that finds optimal meeting times."""
        await interaction.response.defer(ephemeral=True)
        
        # Get organizer's token
        async with session_scope() as session:
            organizer_token = await get_user_token_by_discord_id(session, str(interaction.user.id))
        
        if not organizer_token:
            await interaction.followup.send("Please /connect your Google account first.", ephemeral=True)
            return
        
        # Parse attendees (for now, we'll use the organizer's calendar only)
        # In a full implementation, you'd look up attendee tokens by Discord ID
        attendee_tokens = []  # Placeholder for attendee tokens
        
        if not check_rate_limit(f"gcal:{interaction.user.id}"):
            await interaction.followup.send("Rate limit exceeded. Try again shortly.", ephemeral=True)
            return
        
        try:
            suggestions = await suggest_meeting_times(
                organizer_token=organizer_token,
                attendee_tokens=attendee_tokens,
                duration_minutes=duration_minutes,
                days_ahead=days_ahead,
                preferred_start_hour=preferred_start_hour,
                preferred_end_hour=preferred_end_hour
            )
            
            if not suggestions:
                await interaction.followup.send("No available time slots found in the next few days.", ephemeral=True)
                return
            
            # Format suggestions
            response_lines = [f"**Suggested meeting times for '{title}' ({duration_minutes}min):**\n"]
            for i, suggestion in enumerate(suggestions[:5], 1):  # Show top 5
                start_time = datetime.fromisoformat(suggestion["start_time"])
                end_time = datetime.fromisoformat(suggestion["end_time"])
                response_lines.append(f"{i}. {start_time.strftime('%a %b %d, %I:%M %p')} - {end_time.strftime('%I:%M %p')}")
            
            response_lines.append(f"\nUse `/addevent` with one of these times to create the meeting.")
            await interaction.followup.send("\n".join(response_lines), ephemeral=True)
            
        except Exception as e:
            logger.error("schedule_command_error", error=str(e))
            await interaction.followup.send("Sorry, I couldn't find meeting times. Please try again.", ephemeral=True)

    @client.tree.command(name="recurring", description="Create a recurring event")
    async def recurring_command(
        interaction: discord.Interaction,
        title: str,
        when: str,
        frequency: str,
        interval: int = 1,
        count: int | None = None,
        attendees: str | None = None,
        location: str | None = None,
    ) -> None:
        """Create a recurring event with flexible patterns."""
        await interaction.response.defer(ephemeral=True)
        
        # Validate frequency
        valid_frequencies = ["DAILY", "WEEKLY", "MONTHLY", "YEARLY"]
        if frequency.upper() not in valid_frequencies:
            await interaction.followup.send(
                f"Invalid frequency. Use one of: {', '.join(valid_frequencies)}", 
                ephemeral=True
            )
            return
        
        tz = settings.default_tz
        try:
            start_dt, end_dt = parse_natural_range(when, tz)
        except Exception:
            await interaction.followup.send("Sorry, I couldn't parse the time. Try e.g. 'tomorrow 3-4pm'.", ephemeral=True)
            return
        
        async with session_scope() as session:
            token = await get_user_token_by_discord_id(session, str(interaction.user.id))
        
        if not token:
            await interaction.followup.send("Please /connect your Google account first.", ephemeral=True)
            return
        
        if not check_rate_limit(f"gcal:{interaction.user.id}"):
            await interaction.followup.send("Rate limit exceeded. Try again shortly.", ephemeral=True)
            return
        
        # Build RRULE
        rrule = build_rrule(
            frequency=frequency.upper(),
            interval=interval,
            count=count
        )
        
        # Create event body
        body = {
            "summary": title,
            "start": {"dateTime": start_dt.isoformat()},
            "end": {"dateTime": end_dt.isoformat()},
            "recurrence": [f"RRULE:{rrule}"]
        }
        
        if location:
            body["location"] = location
        if attendees:
            body["attendees"] = [{"email": e.strip()} for e in attendees.split(",") if e.strip()]
        
        try:
            ev = await create_recurring_event(token, body)
            html_link = ev.get("htmlLink", "(no link)")
            await interaction.followup.send(
                f"Created recurring event: {html_link}\n"
                f"Pattern: Every {interval} {frequency.lower()}(s)" + 
                (f" for {count} occurrences" if count else ""),
                ephemeral=True
            )
            events_created_total.inc()
            
        except Exception as e:
            logger.error("recurring_command_error", error=str(e))
            await interaction.followup.send("Sorry, I couldn't create the recurring event. Please try again.", ephemeral=True)

    @client.tree.command(name="conflicts", description="Check for scheduling conflicts")
    async def conflicts_command(
        interaction: discord.Interaction,
        when: str,
        duration_minutes: int = 60,
    ) -> None:
        """Check for scheduling conflicts at a specific time."""
        await interaction.response.defer(ephemeral=True)
        
        tz = settings.default_tz
        try:
            start_dt, end_dt = parse_natural_range(when, tz)
        except Exception:
            await interaction.followup.send("Sorry, I couldn't parse the time. Try e.g. 'tomorrow 3-4pm'.", ephemeral=True)
            return
        
        async with session_scope() as session:
            token = await get_user_token_by_discord_id(session, str(interaction.user.id))
        
        if not token:
            await interaction.followup.send("Please /connect your Google account first.", ephemeral=True)
            return
        
        if not check_rate_limit(f"gcal:{interaction.user.id}"):
            await interaction.followup.send("Rate limit exceeded. Try again shortly.", ephemeral=True)
            return
        
        time_min = start_dt.astimezone(timezone.utc).isoformat()
        time_max = end_dt.astimezone(timezone.utc).isoformat()
        
        try:
            fb = await get_freebusy(token, time_min, time_max)
            busy = fb.get("calendars", {}).get("primary", {}).get("busy", [])
            
            if busy:
                conflict_lines = ["**⚠️ Scheduling conflicts found:**\n"]
                for period in busy:
                    conflict_start = datetime.fromisoformat(period["start"].replace("Z", "+00:00"))
                    conflict_end = datetime.fromisoformat(period["end"].replace("Z", "+00:00"))
                    conflict_lines.append(f"• {conflict_start.strftime('%I:%M %p')} - {conflict_end.strftime('%I:%M %p')}")
                
                conflict_lines.append(f"\nConsider using `/schedule` to find available times.")
                await interaction.followup.send("\n".join(conflict_lines), ephemeral=True)
            else:
                await interaction.followup.send("✅ No conflicts found! This time slot is available.", ephemeral=True)
                
        except Exception as e:
            logger.error("conflicts_command_error", error=str(e))
            await interaction.followup.send("Sorry, I couldn't check for conflicts. Please try again.", ephemeral=True)

    @client.tree.command(name="template", description="Create or use event templates")
    async def template_command(
        interaction: discord.Interaction,
        action: str,
        name: str | None = None,
        title: str | None = None,
        duration_minutes: int = 60,
        location: str | None = None,
        description: str | None = None,
        attendees: str | None = None,
    ) -> None:
        """Manage event templates for quick event creation."""
        await interaction.response.defer(ephemeral=True)
        
        if action.lower() == "list":
            # List user's templates
            async with session_scope() as session:
                res = await session.execute(
                    select(EventTemplate).where(EventTemplate.user_id == interaction.user.id)
                )
                templates = res.scalars().all()
            
            if not templates:
                await interaction.followup.send("No templates found. Create one with `/template create`", ephemeral=True)
                return
            
            template_lines = ["**Your Event Templates:**\n"]
            for template in templates:
                template_lines.append(f"• **{template.name}** - {template.title} ({template.duration_minutes}min)")
                if template.location:
                    template_lines.append(f"  📍 {template.location}")
                if template.default_attendees:
                    template_lines.append(f"  👥 {template.default_attendees}")
            
            await interaction.followup.send("\n".join(template_lines), ephemeral=True)
            
        elif action.lower() == "create":
            # Create a new template
            if not name or not title:
                await interaction.followup.send("Please provide both name and title for the template.", ephemeral=True)
                return
            
            async with session_scope() as session:
                # Check if template already exists
                res = await session.execute(
                    select(EventTemplate).where(
                        EventTemplate.user_id == interaction.user.id,
                        EventTemplate.name == name
                    )
                )
                existing = res.scalars().first()
                
                if existing:
                    await interaction.followup.send(f"Template '{name}' already exists. Use a different name.", ephemeral=True)
                    return
                
                # Create new template
                template = EventTemplate(
                    user_id=interaction.user.id,
                    name=name,
                    title=title,
                    duration_minutes=duration_minutes,
                    location=location,
                    description=description,
                    default_attendees=attendees
                )
                session.add(template)
                await session.commit()
            
            await interaction.followup.send(f"✅ Created template '{name}' for '{title}'", ephemeral=True)
            
        elif action.lower() == "use":
            # Use a template to create an event
            if not name:
                await interaction.followup.send("Please specify which template to use.", ephemeral=True)
                return
            
            async with session_scope() as session:
                res = await session.execute(
                    select(EventTemplate).where(
                        EventTemplate.user_id == interaction.user.id,
                        EventTemplate.name == name
                    )
                )
                template = res.scalars().first()
            
            if not template:
                await interaction.followup.send(f"Template '{name}' not found.", ephemeral=True)
                return
            
            # Get user's token
            async with session_scope() as session:
                token = await get_user_token_by_discord_id(session, str(interaction.user.id))
            
            if not token:
                await interaction.followup.send("Please /connect your Google account first.", ephemeral=True)
                return
            
            # For now, create a placeholder event (user would need to specify time)
            await interaction.followup.send(
                f"**Template '{template.name}' loaded:**\n"
                f"Title: {template.title}\n"
                f"Duration: {template.duration_minutes} minutes\n"
                f"Location: {template.location or 'None'}\n"
                f"Attendees: {template.default_attendees or 'None'}\n\n"
                f"Use `/addevent` with these details to create the event.",
                ephemeral=True
            )
            
        elif action.lower() == "delete":
            # Delete a template
            if not name:
                await interaction.followup.send("Please specify which template to delete.", ephemeral=True)
                return
            
            async with session_scope() as session:
                res = await session.execute(
                    select(EventTemplate).where(
                        EventTemplate.user_id == interaction.user.id,
                        EventTemplate.name == name
                    )
                )
                template = res.scalars().first()
                
                if not template:
                    await interaction.followup.send(f"Template '{name}' not found.", ephemeral=True)
                    return
                
                await session.delete(template)
                await session.commit()
            
            await interaction.followup.send(f"✅ Deleted template '{name}'", ephemeral=True)
            
        else:
            await interaction.followup.send(
                "Invalid action. Use: `list`, `create`, `use`, or `delete`\n"
                "Examples:\n"
                "• `/template list` - Show your templates\n"
                "• `/template create name:standup title:Daily Standup duration_minutes:30`\n"
                "• `/template use name:standup` - Use a template\n"
                "• `/template delete name:standup` - Delete a template",
                ephemeral=True
            )

    return client


async def run_discord_bot(token: str) -> None:
    client = build_bot()
    await client.start(token)


