#!/usr/bin/env python3
"""
Example script for running the Telegram webhook server.

This script demonstrates how to start the webhook server to receive
Telegram messages and store them in Firestore.

Prerequisites:
1. Create a Telegram bot with @BotFather and get the token
2. Set up a Firebase project and download service account JSON
3. Have a public HTTPS URL for the webhook (you can use ngrok for testing)

Usage:
    python scripts/telegram_webhook_example.py
"""

import asyncio
import os
from dotenv import load_dotenv
from simpli5.webhook import TelegramWebhook

# Load environment variables
load_dotenv()

async def main():
    """Run the webhook server."""
    
    # Get configuration from environment variables
    telegram_token = os.getenv('TELEGRAM_BOT_TOKEN')
    webhook_url = os.getenv('WEBHOOK_URL')
    firebase_credentials = os.getenv('GOOGLE_APPLICATION_CREDENTIALS')
    
    if not telegram_token:
        print("Error: TELEGRAM_BOT_TOKEN environment variable not set")
        print("Please set it in your .env file or environment")
        return
    
    if not webhook_url:
        print("Error: WEBHOOK_URL environment variable not set")
        print("Please set it in your .env file or environment")
        print("Example: https://your-domain.com/webhook")
        return
    
    print("Starting Telegram Webhook Server...")
    print(f"Webhook URL: {webhook_url}")
    
    if firebase_credentials:
        print(f"Firebase credentials: {firebase_credentials}")
    else:
        print("Firebase credentials: Not provided - messages will be printed to console")
    
    try:
        # Create webhook instance
        webhook = TelegramWebhook(
            telegram_token=telegram_token,
            webhook_url=webhook_url,
            firebase_credentials_path=firebase_credentials,
            collection_name="telegram_messages"
        )
        
        # Setup webhook with Telegram
        await webhook.setup_webhook()
        
        print("Webhook configured successfully!")
        print("Server starting on http://localhost:8000")
        print("Health check: http://localhost:8000/health")
        print("Press Ctrl+C to stop the server")
        
        # Run the server
        await webhook.run_async(host="0.0.0.0", port=8000)
        
    except KeyboardInterrupt:
        print("\nShutting down...")
        try:
            await webhook.remove_webhook()
        except:
            pass
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\nShutting down...") 