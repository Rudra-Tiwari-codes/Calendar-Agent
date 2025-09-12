#!/usr/bin/env python3
"""
Simple test script to demonstrate Calendar Agent functionality
"""

import asyncio
import sys
import os
from datetime import datetime, timedelta

# Add the src directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from events_agent.infra.date_parsing import parse_natural_datetime, extract_event_details
from events_agent.infra.db import session_scope
from events_agent.infra.event_repository import EventRepository, UserRepository
from events_agent.domain.models import User, Event


async def test_database_operations():
    """Test database operations with SQLite."""
    print("🔍 Testing Database Operations with SQLite")
    print("=" * 50)
    
    # Test 1: Create a user
    print("\n1. Creating a test user...")
    async for session in session_scope():
        user_repo = UserRepository(session)
        
        # Create a test user
        user = await user_repo.get_or_create_user("123456789", "test@example.com")
        print(f"✅ Created user: {user.discord_id} (ID: {user.id})")
        
        # Test 2: Create an event
        print("\n2. Creating a test event...")
        event_repo = EventRepository(session)
        
        start_time = datetime.now() + timedelta(hours=1)
        end_time = start_time + timedelta(hours=1)
        
        event = await event_repo.create_event(
            user_id=user.id,
            discord_user_id=user.discord_id,
            google_event_id="test_event_123",
            title="Test Meeting",
            description="This is a test event created by the Calendar Agent",
            location="Test Location",
            start_time=start_time,
            end_time=end_time,
            attendees=["test1@example.com", "test2@example.com"],
            google_calendar_link="https://calendar.google.com/test"
        )
        
        print(f"✅ Created event: {event.title} (ID: {event.id})")
        print(f"   Start: {event.start_time}")
        print(f"   End: {event.end_time}")
        print(f"   Location: {event.location}")
        
        # Test 3: Retrieve events
        print("\n3. Retrieving user events...")
        events = await event_repo.get_events_by_user(user.discord_id, limit=5)
        print(f"✅ Found {len(events)} events for user")
        
        for i, evt in enumerate(events, 1):
            print(f"   {i}. {evt.title} - {evt.start_time.strftime('%Y-%m-%d %H:%M')}")
        
        # Test 4: Check for duplicates
        print("\n4. Testing duplicate detection...")
        duplicate = await event_repo.check_duplicate_event(
            user.discord_id, "Test Meeting", start_time, end_time
        )
        
        if duplicate:
            print(f"✅ Duplicate detection working! Found duplicate: {duplicate.title}")
        else:
            print("❌ Duplicate detection not working")
        
        break
    
    print("\n" + "=" * 50)
    print("🎉 Database operations test completed!")
    print(f"📁 Database file location: {os.path.abspath('events_agent.db')}")


def test_natural_language():
    """Test natural language parsing."""
    print("\n🔍 Testing Natural Language Parsing")
    print("=" * 50)
    
    test_phrases = [
        "tomorrow 3pm",
        "next monday 2pm", 
        "in 2 hours",
        "december 25th 10am",
        "today 5pm"
    ]
    
    for phrase in test_phrases:
        try:
            result = parse_natural_datetime(phrase)
            print(f"✅ '{phrase}' -> {result.strftime('%Y-%m-%d %H:%M:%S %Z')}")
        except Exception as e:
            print(f"❌ '{phrase}' failed: {e}")
    
    print("\n🔍 Testing Event Details Extraction")
    print("-" * 30)
    
    test_events = [
        "Team meeting tomorrow 3pm with @john @jane",
        "Lunch with Sarah next Friday 12pm at the cafe",
        "Project review meeting tomorrow 2-4pm in conference room A"
    ]
    
    for event_text in test_events:
        try:
            details = extract_event_details(event_text)
            print(f"✅ '{event_text}'")
            print(f"   Title: {details['title']}")
            print(f"   Time: {details['time']}")
            print(f"   Attendees: {details['attendees']}")
        except Exception as e:
            print(f"❌ '{event_text}' failed: {e}")


async def main():
    """Run all tests."""
    print("🚀 Calendar Agent Simple Test")
    print("=" * 50)
    
    # Test natural language parsing
    test_natural_language()
    
    # Test database operations
    await test_database_operations()
    
    print("\n" + "=" * 50)
    print("📋 Next Steps to Test the Full Application:")
    print("1. Run: uv run python -m events_agent.main")
    print("2. The bot will start on Discord")
    print("3. Use /ping to test if bot is online")
    print("4. Use /connect to link Google Calendar")
    print("5. Use /addevent to create events")
    print("6. Check your Google Calendar for created events")
    print("7. Check the SQLite database for stored data")
    
    print(f"\n📁 Database file: {os.path.abspath('events_agent.db')}")
    print("💡 You can open this file with any SQLite browser to see the data!")


if __name__ == "__main__":
    asyncio.run(main())
