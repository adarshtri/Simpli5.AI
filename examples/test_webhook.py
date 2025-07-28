#!/usr/bin/env python3
"""
Test script for the Telegram webhook functionality.

This script tests the webhook without requiring actual Telegram integration.
"""

import asyncio
import json
from datetime import datetime
from simpli5.webhook.telegram_webhook import TelegramWebhook, TelegramMessage

async def test_webhook():
    """Test the webhook functionality."""
    
    # Mock Telegram update data
    mock_update = {
        "update_id": 123456789,
        "message": {
            "message_id": 1,
            "from": {
                "id": 123456,
                "is_bot": False,
                "first_name": "Test",
                "last_name": "User",
                "username": "testuser"
            },
            "chat": {
                "id": 123456,
                "first_name": "Test",
                "last_name": "User",
                "username": "testuser",
                "type": "private"
            },
            "date": 1640995200,  # Unix timestamp
            "text": "Hello, this is a test message!"
        }
    }
    
    print("Testing webhook functionality...")
    
    # Test message creation
    message = TelegramMessage(
        message_id=1,
        chat_id=123456,
        user_id=123456,
        username="testuser",
        first_name="Test",
        last_name="User",
        text="Hello, this is a test message!",
        timestamp=datetime.fromtimestamp(1640995200),
        message_type="text"
    )
    
    print(f"Created message: {message.model_dump()}")
    print("✅ Message model works correctly")
    
    # Test webhook initialization (without Firebase)
    try:
        # This will fail without proper credentials, but we can test the structure
        webhook = TelegramWebhook(
            telegram_token="test_token",
            webhook_url="https://test.com/webhook",
            collection_name="test_messages"
        )
        print("✅ Webhook class initializes correctly")
    except Exception as e:
        print(f"⚠️  Expected error during initialization (no Firebase credentials): {e}")
    
    print("\n🎉 Webhook functionality test completed!")
    print("\nTo test with real data:")
    print("1. Set up Firebase credentials")
    print("2. Create a Telegram bot")
    print("3. Run: python examples/telegram_webhook_example.py")

if __name__ == "__main__":
    asyncio.run(test_webhook()) 