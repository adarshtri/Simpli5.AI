"""Telegram webhook for receiving and storing messages in Firestore."""

import os
import logging
from typing import Dict, Any, Optional
from datetime import datetime

import firebase_admin
from firebase_admin import credentials, firestore
from fastapi import FastAPI, Request, HTTPException
from pydantic import BaseModel
from telegram import Update
from telegram.ext import Application

logger = logging.getLogger(__name__)


class TelegramMessage(BaseModel):
    """Model for Telegram message data."""
    message_id: int
    chat_id: int
    user_id: int
    username: Optional[str] = None
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    text: Optional[str] = None
    timestamp: datetime
    message_type: str = "text"


class TelegramWebhook:
    """Handles Telegram webhook and stores messages in Firestore."""
    
    def __init__(self, 
                 telegram_token: str,
                 webhook_url: str,
                 firebase_credentials_path: Optional[str] = None,
                 collection_name: str = "telegram_messages"):
        """
        Initialize the Telegram webhook.
        
        Args:
            telegram_token: Telegram bot token
            webhook_url: URL where webhook will receive updates
            firebase_credentials_path: Path to Firebase service account JSON
            collection_name: Firestore collection name for messages
        """
        self.telegram_token = telegram_token
        self.webhook_url = webhook_url
        self.collection_name = collection_name
        
        # Initialize Firebase
        self._init_firebase(firebase_credentials_path)
        
        # Initialize FastAPI app
        self.app = FastAPI(title="Simpli5 Telegram Webhook")
        self._setup_routes()
        
        # Initialize Telegram bot
        self.bot = Application.builder().token(telegram_token).build()
        
    def _init_firebase(self, credentials_path: Optional[str] = None):
        """Initialize Firebase Admin SDK."""
        self.db = None
        try:
            if credentials_path:
                cred = credentials.Certificate(credentials_path)
                firebase_admin.initialize_app(cred)
            else:
                # Use default credentials (GOOGLE_APPLICATION_CREDENTIALS env var)
                firebase_admin.initialize_app()
            
            self.db = firestore.client()
            logger.info("Firebase initialized successfully")
        except Exception as e:
            logger.warning(f"Firebase not available: {e}")
            logger.info("Messages will be printed to console only")
            self.db = None
    
    def _setup_routes(self):
        """Setup FastAPI routes."""
        
        @self.app.post("/webhook")
        async def webhook_handler(request: Request):
            """Handle incoming webhook from Telegram."""
            try:
                # Parse the update from Telegram
                update_data = await request.json()
                update = Update.de_json(update_data, self.bot.bot)
                
                # Process the message
                await self._process_message(update)
                
                return {"status": "ok"}
            except Exception as e:
                logger.error(f"Error processing webhook: {e}")
                raise HTTPException(status_code=500, detail=str(e))
        
        @self.app.post("/")
        async def root_webhook_handler(request: Request):
            """Handle incoming webhook from Telegram at root path."""
            return await webhook_handler(request)
        
        @self.app.get("/health")
        async def health_check():
            """Health check endpoint."""
            return {"status": "healthy", "service": "telegram_webhook"}
    
    async def _process_message(self, update: Update):
        """Process incoming Telegram message and store in Firestore."""
        if not update.message:
            return
        
        message = update.message
        chat = message.chat
        user = message.from_user
        
        # Create message data
        message_data = TelegramMessage(
            message_id=message.message_id,
            chat_id=chat.id,
            user_id=user.id,
            username=user.username,
            first_name=user.first_name,
            last_name=user.last_name,
            text=message.text,
            timestamp=datetime.fromtimestamp(message.date.timestamp()),
            message_type="text"  # We can extend this for other message types
        )
        
        # Add chat type information
        chat_type = chat.type  # 'private', 'group', 'supergroup', 'channel'
        if chat_type == 'private':
            logger.info(f"Private chat detected - chat_id and user_id are the same: {chat.id}")
        else:
            logger.info(f"Group/Channel chat detected - chat_id: {chat.id}, user_id: {user.id}")
        
        # Store in Firestore with chat type
        await self._store_message(message_data, chat_type)
        
        logger.info(f"Stored message from {user.username or user.first_name} in chat {chat.id}")
    
    async def _store_message(self, message: TelegramMessage, chat_type: str = "private"):
        """Store message in Firestore or print to console."""
        try:
            # Convert to dict for Firestore
            message_dict = message.model_dump()
            message_dict['chat_type'] = chat_type
            
            if self.db:
                # Store in Firestore if available
                doc_ref = self.db.collection(self.collection_name).document()
                doc_ref.set(message_dict)
                logger.debug(f"Message stored in Firestore with ID: {doc_ref.id}")
            else:
                # Print to console if Firebase not available
                print(f"\n📨 New Telegram Message:")
                print(f"   From: {message.first_name} {message.last_name} (@{message.username}) ({message.user_id})")
                print(f"   Chat ID: {message.chat_id} ({chat_type})")
                print(f"   Message: {message.text}")
                print(f"   Time: {message.timestamp}")
                print(f"   Type: {message.message_type}")
                print("-" * 50)
                
        except Exception as e:
            logger.error(f"Failed to process message: {e}")
            raise
    
    async def setup_webhook(self):
        """Setup webhook with Telegram."""
        try:
            await self.bot.bot.set_webhook(url=self.webhook_url)
            logger.info(f"Webhook set to: {self.webhook_url}")
        except Exception as e:
            logger.error(f"Failed to setup webhook: {e}")
            raise
    
    async def remove_webhook(self):
        """Remove webhook from Telegram."""
        try:
            await self.bot.bot.delete_webhook()
            logger.info("Webhook removed")
        except Exception as e:
            logger.error(f"Failed to remove webhook: {e}")
            raise
    
    def run(self, host: str = "0.0.0.0", port: int = 8000):
        """Run the FastAPI server."""
        import uvicorn
        uvicorn.run(self.app, host=host, port=port)
    
    async def run_async(self, host: str = "0.0.0.0", port: int = 8000):
        """Run the FastAPI server asynchronously."""
        import uvicorn
        config = uvicorn.Config(self.app, host=host, port=port)
        server = uvicorn.Server(config)
        await server.serve() 