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

# Import for LLM and MCP integration
from ..providers.llm.multi import MultiLLMProvider
from ..servers.telegram import MemoryCategorizationPrompt

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
        
        # Initialize LLM provider
        self._init_llm()
        
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
    
    def _init_llm(self):
        """Initialize LLM provider for memory categorization."""
        self.llm_manager = None
        try:
            self.llm_manager = MultiLLMProvider()
            if self.llm_manager.has_provider():
                logger.info("LLM provider initialized successfully")
            else:
                logger.warning("No LLM provider available - memory categorization will be disabled")
        except Exception as e:
            logger.warning(f"LLM initialization failed: {e}")
            logger.info("Memory categorization will be disabled")
    
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
        
        # Only process private chats for personal AI assistants
        if chat.type != 'private':
            return
        
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
        
        # Check for memory commands first
        is_memory_command = await self._handle_memory_command(message_data)
        
        # Store in Firestore (private chat only)
        await self._store_message(message_data, "private")
        
        # Generate personalized response if it's not a memory command
        if not is_memory_command:
            personalized_response = await self._generate_personalized_response(message_data)
            await self._send_response(chat.id, personalized_response)
    
    async def _handle_memory_command(self, message: TelegramMessage) -> bool:
        """Handle memory commands and categorize messages. Returns True if it was a memory command."""
        logger.info("🧠 _handle_memory_command called")
        logger.info(f"🔍 Checking message: '{message.text}'")
        
        if not message.text:
            return False
        
        # Handle /listmemory command
        if message.text.startswith('/listmemory'):
            await self._handle_list_memory_command(message)
            return True
        
        # Handle /memory command
        if not message.text.startswith('/memory'):
            return False
        
        # Extract the message content after /memory
        memory_content = message.text.replace('/memory', '').strip()
        if not memory_content:
            return False
        
        # Categorize the memory using LLM
        category = await self._categorize_memory(memory_content)
        
        # Only store memories that are not "not_applicable"
        if category == "not_applicable":
            # Send response to user
            response_text = f"🧠 Memory: \"{memory_content}\"\n❌ Not stored (not applicable for memory)"
            await self._send_response(message.chat_id, response_text)
            return True
        
        # Store the categorized memory in Firestore
        if self.db:
            try:
                memory_data = {
                    "message": memory_content,
                    "user_id": message.user_id,
                    "timestamp": message.timestamp,
                    "command_type": "memory",
                    "category": category,
                    "status": "categorized"
                }
                
                # Store in users/{user_id}/memories/{category}
                user_collection = self.db.collection('users').document(str(message.user_id))
                memories_collection = user_collection.collection('memories')
                category_doc = memories_collection.document(category)
                
                # Get existing memories for this category or create new
                category_doc_ref = category_doc.get()
                if category_doc_ref.exists:
                    existing_data = category_doc_ref.to_dict()
                    memories = existing_data.get('memories', [])
                    memories.append(memory_data)
                    category_doc.update({'memories': memories})
                else:
                    category_doc.set({'memories': [memory_data]})
                
                # Send success response to user
                response_text = f"🧠 Memory: \"{memory_content}\"\n✅ Stored as: {category.upper()}\nI'll remember this information about you for our future conversations."
                await self._send_response(message.chat_id, response_text)
                
            except Exception as e:
                # Send error response to user
                response_text = f"🧠 Memory: \"{memory_content}\"\n❌ Error storing memory: {e}"
                await self._send_response(message.chat_id, response_text)
        
        return True
    
    async def _handle_list_memory_command(self, message: TelegramMessage):
        """Handle the /list-memory command to show all user memories."""
        if not self.db:
            response_text = "❌ Memory storage not available"
            await self._send_response(message.chat_id, response_text)
            return
        
        try:
            # Get all memories for the user
            user_collection = self.db.collection('users').document(str(message.user_id))
            memories_collection = user_collection.collection('memories')
            
            all_memories = []
            categories = memories_collection.stream()
            
            for cat_doc in categories:
                data = cat_doc.to_dict()
                memories = data.get('memories', [])
                category = cat_doc.id
                
                if memories:
                    category_memories = []
                    for memory in memories:
                        memory_text = memory.get('message', '')
                        if memory_text:
                            category_memories.append(f"• {memory_text}")
                    
                    if category_memories:
                        all_memories.append(f"📁 {category.upper()}:")
                        all_memories.extend(category_memories)
                        all_memories.append("")  # Empty line for spacing
            
            if all_memories:
                response_text = "🧠 Your Memories:\n\n" + "\n".join(all_memories)
            else:
                response_text = "🧠 You don't have any memories stored yet.\n\nUse /memory \"your information\" to store memories!"
            
            await self._send_response(message.chat_id, response_text)
            
        except Exception as e:
            response_text = f"❌ Error retrieving memories: {e}"
            await self._send_response(message.chat_id, response_text)
    
    async def _get_user_memories(self, user_id: int) -> str:
        """Retrieve and format user memories for LLM context."""
        if not self.db:
            return ""
        
        try:
            # Get all memories for the user
            user_collection = self.db.collection('users').document(str(user_id))
            memories_collection = user_collection.collection('memories')
            
            all_memories = []
            categories = memories_collection.stream()
            
            for cat_doc in categories:
                data = cat_doc.to_dict()
                memories = data.get('memories', [])
                category = cat_doc.id
                
                for memory in memories:
                    memory_text = memory.get('message', '')
                    if memory_text:
                        all_memories.append(f"• {category.upper()}: {memory_text}")
            
            if all_memories:
                memories_text = "\n".join(all_memories)
                return f"User Memories:\n{memories_text}"
            else:
                return ""
                
        except Exception as e:
            return ""
    
    async def _send_response(self, chat_id: int, message_text: str):
        """Send a response back to the user via Telegram bot."""
        try:
            logger.info(f"📤 Sending response to chat {chat_id}: '{message_text}'")
            await self.bot.bot.send_message(chat_id=chat_id, text=message_text)
            logger.info(f"✅ Response sent successfully to chat {chat_id}")
        except Exception as e:
            logger.error(f"❌ Failed to send response to chat {chat_id}: {e}")
    
    async def _generate_personalized_response(self, message: TelegramMessage) -> str:
        """Generate a personalized response using LLM and user memories."""
        if not self.llm_manager or not self.llm_manager.has_provider():
            return message.text
        
        try:
            # Get user memories
            memories_context = await self._get_user_memories(message.user_id)
            
            # Create the personalized prompt
            if memories_context:
                prompt = f"""You are a helpful AI assistant. You have access to some information about the user, but only use it if it's relevant to their current message.

{memories_context}

User's message: "{message.text}"

Instructions:
- Only use the user's information if it's directly relevant to their current message
- If the user's message doesn't relate to any stored information, respond naturally without forcing the memories
- For simple greetings like "hi", "hello", etc., just respond naturally
- Only bring up personal information when it makes sense in context
- Keep your response conversational and natural

Please respond appropriately."""
            else:
                prompt = f"""You are a helpful AI assistant. The user has sent you a message.

User's message: "{message.text}"

Please respond in a helpful, conversational way. Keep your response concise and natural."""
            
            # Generate response using LLM
            response = self.llm_manager.generate_response(prompt)
            return response
            
        except Exception as e:
            return f"I'm sorry, I'm having trouble processing your request right now. Here's what you said: {message.text}"
    
    async def _categorize_memory(self, memory_content: str) -> str:
        """Categorize memory using LLM."""
        if not self.llm_manager or not self.llm_manager.has_provider():
            return "not_applicable"
        
        try:
            # Create the memory categorization prompt
            prompt = MemoryCategorizationPrompt()
            prompt_result = await prompt.generate({"user_message": memory_content})
            prompt_text = prompt_result.content
            
            # Send to LLM for categorization
            llm_response = self.llm_manager.generate_response(prompt_text)
            category = llm_response.strip().lower()
            
            # Validate category
            valid_categories = ["profile", "preference", "context", "not_applicable"]
            if category not in valid_categories:
                return "not_applicable"
            
            return category
            
        except Exception as e:
            return "not_applicable"
    
    async def _store_message(self, message: TelegramMessage, chat_type: str = "private"):
        """Store message in Firestore or print to console."""
        try:
            # Convert to dict for Firestore
            message_dict = message.model_dump()
            message_dict['chat_type'] = chat_type
            
            # Print to console (always show messages)
            print(f"\n📨 New Private Message:")
            print(f"   User: {message.first_name} {message.last_name} (@{message.username})")
            print(f"   User ID: {message.user_id}")
            print(f"   Message: {message.text}")
            print(f"   Time: {message.timestamp}")
            print(f"   Type: {message.message_type}")
            print("-" * 50)
            
            if self.db:
                # Store in Firestore with user segregation
                # Structure: users/{user_id}/interactions/{message_id}
                user_collection = self.db.collection('users').document(str(message.user_id))
                interactions_collection = user_collection.collection('interactions')
                
                # Use message_id as document ID to avoid duplicates
                doc_ref = interactions_collection.document(str(message.message_id))
                doc_ref.set(message_dict)
                
                logger.debug(f"Message stored for user {message.user_id} with message ID: {message.message_id}")
                
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