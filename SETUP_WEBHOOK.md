# Telegram Webhook Setup Guide

This guide will help you set up the Telegram webhook to receive messages and store them in Firestore.

## Prerequisites

1. **Python Environment**: Make sure you have the Simpli5.AI environment set up
2. **Telegram Bot**: You'll need a Telegram bot token
3. **Firebase Project**: You'll need a Firebase project with Firestore enabled
4. **Public HTTPS URL**: For webhook to work, you need a public HTTPS URL

## Step 1: Create a Telegram Bot

1. Open Telegram and search for [@BotFather](https://t.me/botfather)
2. Send `/newbot` command
3. Follow the instructions to create your bot
4. Save the bot token (you'll need it later)

## Step 2: Set up Firebase

1. Go to [Firebase Console](https://console.firebase.google.com/)
2. Create a new project or select an existing one
3. Enable Firestore Database
4. Go to Project Settings > Service Accounts
5. Click "Generate new private key"
6. Download the JSON file and save it securely

## Step 3: Set up Environment Variables

Create a `.env` file in your project root:

```bash
# .env
TELEGRAM_BOT_TOKEN=your_bot_token_here
GOOGLE_APPLICATION_CREDENTIALS=path/to/your/service-account.json
```

## Step 4: Get a Public HTTPS URL

For development, you can use ngrok:

```bash
# Install ngrok
npm install -g ngrok

# Start your webhook server (in one terminal)
simpli5 webhook --telegram-token YOUR_TOKEN --webhook-url https://your-ngrok-url.ngrok.io/webhook

# Expose your local server (in another terminal)
ngrok http 8000
```

Copy the HTTPS URL from ngrok (e.g., `https://abc123.ngrok.io`)

## Step 5: Start the Webhook Server

```bash
# Using CLI command
simpli5 webhook \
  --telegram-token YOUR_BOT_TOKEN \
  --webhook-url https://your-ngrok-url.ngrok.io/webhook \
  --collection-name telegram_messages

# Or using the example script
python scripts/telegram_webhook_example.py
```

## Step 6: Test the Webhook

1. Send a message to your Telegram bot
2. Check the server logs to see if the message was received
3. Check your Firestore database to see if the message was stored

## Step 7: Integrate with Simpli5.AI Chat

Once you have messages stored in Firestore, you can:

1. Add the Firebase MCP server to your configuration
2. Use the chat interface to query and analyze the stored messages
3. Build AI-powered analysis of your Telegram conversations

## Troubleshooting

### Common Issues

1. **"Your default credentials were not found"**
   - Make sure you've set the `GOOGLE_APPLICATION_CREDENTIALS` environment variable
   - Verify the path to your service account JSON file is correct

2. **"Webhook URL must be HTTPS"**
   - Make sure your webhook URL starts with `https://`
   - For local development, use ngrok or similar service

3. **"Invalid bot token"**
   - Double-check your bot token from @BotFather
   - Make sure there are no extra spaces or characters

4. **"Connection refused"**
   - Make sure your server is running on the correct port
   - Check if the port is accessible from the internet

### Testing Without Real Credentials

You can test the webhook functionality without real credentials:

```bash
# test_webhook.py was removed - use scripts/telegram_webhook_example.py instead
```

This will test the message model and webhook structure without requiring actual Telegram or Firebase setup.

## Next Steps

Once your webhook is working:

1. **Analyze Messages**: Use the Simpli5.AI chat interface to query your stored messages
2. **Add More Features**: Extend the webhook to handle different message types (photos, documents, etc.)
3. **Build AI Analysis**: Use the stored messages to build AI-powered insights and responses

## Security Notes

- Keep your bot token and Firebase credentials secure
- Never commit credentials to version control
- Use environment variables for sensitive data
- Consider implementing webhook signature verification for production use 