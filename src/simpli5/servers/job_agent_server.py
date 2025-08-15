#!/usr/bin/env python3
"""
Job Agent MCP Server - A STDIO-based MCP server for job-related operations and message storage.

This server provides tools for job management, message storage, and job-related AI operations using Firebase Firestore.
"""

import logging
import sys
import os
from typing import Dict, Any, Optional
from datetime import datetime
from mcp.server.fastmcp import FastMCP

# Load environment variables from .env file
from dotenv import load_dotenv
load_dotenv()

# Firebase imports
import firebase_admin
from firebase_admin import credentials, firestore

# Set up logging to stderr (not stdout!) to avoid interfering with MCP protocol
logging.basicConfig(
    level=logging.INFO,
    stream=sys.stderr,  # Important: log to stderr, not stdout
    format='%(asctime)s - %(name)s - %(levelname)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("job-agent-server")

# Initialize Firebase
if not firebase_admin._apps:
    # Use default credentials (GOOGLE_APPLICATION_CREDENTIALS env var)
    firebase_admin.initialize_app()

db = firestore.client()
logger.info("Firebase initialized successfully")

# Create FastMCP server
mcp = FastMCP("JobAgent")

@mcp.tool()
def store_job_message(
    user_id: str,
    original_message: str,
    extracted_job_link: str,
    company_name: str,
    metadata: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """
    Store a job-related message in Firestore.
    
    Args:
        user_id: ID of the user
        original_message: The original message text
        extracted_job_link: The job link extracted from the message
        company_name: Name of the company
        metadata: Additional metadata for the message (optional)
        
    Returns:
        Dict with success status and document reference
    """
    try:
        # First, check if a job with the same link already exists for this user
        user_collection = db.collection('users').document(str(user_id))
        job_messages_collection = user_collection.collection('job_messages')
        
        # Query for existing job with same link
        existing_jobs = job_messages_collection.where('extracted_job_link', '==', extracted_job_link).limit(1).stream()
        existing_job = next(existing_jobs, None)
        
        if existing_job:
            # Job with this link already exists
            existing_data = existing_job.to_dict()
            existing_company = existing_data.get('company_name', 'Unknown Company')
            existing_timestamp = existing_data.get('timestamp')
            
            logger.info(f"Job with link {extracted_job_link} already exists for user {user_id}")
            
            return f"This job from {existing_company} has already been saved. It was originally saved on {existing_timestamp.strftime('%Y-%m-%d %H:%M') if existing_timestamp else 'an earlier date'}."
        
        # Set company_name to "Unknown" if it's empty
        if not company_name or company_name.strip() == "":
            company_name = "Unknown"
        
        # Create message document
        message_data = {
            "user_id": user_id,
            "original_message": original_message,
            "extracted_job_link": extracted_job_link,
            "company_name": company_name,
            "timestamp": datetime.utcnow(),
            "metadata": metadata or {}
        }
        
        # Store in Firestore with structure: users/{user_id}/job_messages/{message_id}
        doc_ref = job_messages_collection.add(message_data)
        
        logger.info(f"Stored job message for user {user_id}")
        
        return f"Job from {company_name} has been saved successfully!"
        
    except Exception as e:
        logger.error(f"Failed to store job message: {e}")
        return "Failed to save job."

@mcp.tool()
def get_job_messages(user_id: str, limit: int = 50) -> Dict[str, Any]:
    """
    Retrieve job-related messages from Firestore.
    
    Args:
        user_id: ID of the user
        limit: Maximum number of messages to retrieve (default: 50)
        
    Returns:
        Dict with success status and messages
    """
    try:
        # Get messages from Firestore
        user_collection = db.collection('users').document(str(user_id))
        job_messages_collection = user_collection.collection('job_messages')
        
        # Query messages, ordered by timestamp
        messages = job_messages_collection.order_by('timestamp', direction=firestore.Query.DESCENDING).limit(limit).stream()
        
        # Convert to list of dicts
        message_list = []
        for msg in messages:
            msg_data = msg.to_dict()
            msg_data['id'] = msg.id
            message_list.append(msg_data)
        
        logger.info(f"Retrieved {len(message_list)} job messages for user {user_id}")
        
        return {
            "success": True,
            "messages": message_list,
            "count": len(message_list)
        }
        
    except Exception as e:
        logger.error(f"Failed to retrieve job messages: {e}")
        return {
            "success": False,
            "error": str(e)
        }

@mcp.tool()
def get_user_job_stats(user_id: str) -> Dict[str, Any]:
    """
    Get job-related statistics for a specific user.
    
    Args:
        user_id: ID of the user
        
    Returns:
        Dict with success status and job statistics
    """
    try:
        # Get user's job messages collection
        user_collection = db.collection('users').document(str(user_id))
        job_messages_collection = user_collection.collection('job_messages')
        
        # Get all messages for the user
        messages = job_messages_collection.stream()
        
        # Count total messages
        total_messages = 0
        unique_job_links = set()
        
        for msg in messages:
            total_messages += 1
            msg_data = msg.to_dict()
            if 'extracted_job_link' in msg_data:
                unique_job_links.add(msg_data['extracted_job_link'])
        
        logger.info(f"Found {total_messages} job messages and {len(unique_job_links)} unique job links for user {user_id}")
        
        return {
            "success": True,
            "total_messages": total_messages,
            "unique_job_links": len(unique_job_links),
            "job_links": list(unique_job_links)
        }
        
    except Exception as e:
        logger.error(f"Failed to get user job stats: {e}")
        return {
            "success": False,
            "error": str(e)
        }

def main():
    """Main entry point for Job Agent MCP server."""
    logger.info("Starting Job Agent MCP Server via STDIO...")
    mcp.run(transport="stdio")

if __name__ == "__main__":
    main()
