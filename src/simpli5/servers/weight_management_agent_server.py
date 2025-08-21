#!/usr/bin/env python3
"""
Weight Management Agent MCP Server - A STDIO-based MCP server for weight tracking and fitness goals.

This server provides tools for weight tracking, fitness goals, and weight-related AI operations using Firebase Firestore.
"""

import logging
import sys
import os
from typing import Dict, Any, Optional, List
from datetime import datetime, date
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
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("weight-management-agent-server")

# Initialize Firebase
if not firebase_admin._apps:
    # Use default credentials (GOOGLE_APPLICATION_CREDENTIALS env var)
    firebase_admin.initialize_app()

db = firestore.client()
logger.info("Firebase initialized successfully")

# Create FastMCP server
mcp = FastMCP("WeightManagementAgent")

@mcp.tool()
def store_weight_entry(
    user_id: str,
    weight: float,
    date: Optional[str] = None,
    notes: Optional[str] = None,
    metadata: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """
    Store a weight entry in Firestore.
    
    Args:
        user_id: ID of the user
        weight: Weight in kg or lbs (specify unit in metadata)
        date: Date of the weight entry (YYYY-MM-DD format, optional - defaults to current UTC date)
        notes: Optional notes about the weight entry
        metadata: Additional metadata (unit, body fat %, etc.)
        
    Returns:
        Dict with success status and document reference
    """
    try:
        # Use current UTC date if no date provided
        if date is None:
            entry_date = datetime.utcnow().date()
        else:
            # Parse the provided date
            entry_date = datetime.strptime(date, "%Y-%m-%d").date()
        
        # Get user's weight collection
        user_collection = db.collection('users').document(str(user_id))
        weight_collection = user_collection.collection('weight_entries')
        
        # Check if entry already exists for this date
        existing_entries = weight_collection.where('date', '==', entry_date.isoformat()).limit(1).stream()
        existing_entry = next(existing_entries, None)
        
        if existing_entry:
            # Update existing entry
            existing_entry.reference.update({
                "weight": weight,
                "notes": notes,
                "metadata": metadata or {},
                "updated_at": datetime.utcnow()
            })
            logger.info(f"Updated weight entry for user {user_id} on {entry_date.isoformat()}")
            return f"Weight entry updated for {entry_date.isoformat()}: {weight}"
        
        # Create new weight entry
        weight_data = {
            "user_id": user_id,
            "weight": weight,
            "date": entry_date.isoformat(),
            "notes": notes,
            "metadata": metadata or {},
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow()
        }
        
        # Store in Firestore with structure: users/{user_id}/weight_entries/{entry_id}
        doc_ref = weight_collection.add(weight_data)
        
        logger.info(f"Stored weight entry for user {user_id} on {entry_date.isoformat()}")
        
        return f"Weight entry stored successfully for {entry_date.isoformat()}: {weight}"
        
    except Exception as e:
        logger.error(f"Failed to store weight entry: {e}")
        return f"Failed to store weight entry: {str(e)}"

@mcp.tool()
def get_weight_history(
    user_id: str,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    limit: int = 50
) -> Dict[str, Any]:
    """
    Retrieve weight history from Firestore.
    
    Args:
        user_id: ID of the user
        start_date: Start date for range (YYYY-MM-DD format, optional - defaults to 30 days ago)
        end_date: End date for range (YYYY-MM-DD format, optional - defaults to current UTC date)
        limit: Maximum number of entries to retrieve (default: 50)
        
    Returns:
        Dict with success status and weight entries
    """
    try:
        from datetime import timedelta
        
        # Use default dates if not provided
        if end_date is None:
            end_dt = datetime.utcnow().date()
        else:
            end_dt = datetime.strptime(end_date, "%Y-%m-%d").date()
        
        if start_date is None:
            start_dt = end_dt - timedelta(days=30)
        else:
            start_dt = datetime.strptime(start_date, "%Y-%m-%d").date()
        
        # Get user's weight collection
        user_collection = db.collection('users').document(str(user_id))
        weight_collection = user_collection.collection('weight_entries')
        
        # Build query with date range
        query = weight_collection.order_by('date', direction=firestore.Query.DESCENDING)
        query = query.where('date', '>=', start_dt.isoformat())
        query = query.where('date', '<=', end_dt.isoformat())
        
        # Execute query with limit
        entries = query.limit(limit).stream()
        
        # Convert to list of dicts
        weight_list = []
        for entry in entries:
            entry_data = entry.to_dict()
            entry_data['id'] = entry.id
            weight_list.append(entry_data)
        
        logger.info(f"Retrieved {len(weight_list)} weight entries for user {user_id} from {start_dt.isoformat()} to {end_dt.isoformat()}")
        
        return {
            "success": True,
            "entries": weight_list,
            "count": len(weight_list),
            "date_range": {
                "start_date": start_dt.isoformat(),
                "end_date": end_dt.isoformat()
            }
        }
        
    except Exception as e:
        logger.error(f"Failed to retrieve weight history: {e}")
        return {
            "success": False,
            "error": str(e)
        }



@mcp.tool()
def store_fitness_goal(
    user_id: str,
    goal_type: str,
    target_value: float,
    target_date: str,
    current_value: Optional[float] = None,
    notes: Optional[str] = None,
    metadata: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """
    Store a fitness goal in Firestore.
    
    Args:
        user_id: ID of the user
        goal_type: Type of fitness goal (e.g., 'weight_loss', 'muscle_gain', 'endurance')
        target_value: Target value for the goal
        target_date: Target date to achieve the goal (YYYY-MM-DD format)
        current_value: Current value (optional)
        notes: Optional notes about the goal
        metadata: Additional metadata (unit, progress tracking, etc.)
        
    Returns:
        Dict with success status and document reference
    """
    try:
        # Parse the target date
        goal_date = datetime.strptime(target_date, "%Y-%m-%d").date()
        
        # Get user's fitness goals collection
        user_collection = db.collection('users').document(str(user_id))
        goals_collection = user_collection.collection('fitness_goals')
        
        # Create fitness goal entry
        goal_data = {
            "user_id": user_id,
            "goal_type": goal_type,
            "target_value": target_value,
            "target_date": goal_date.isoformat(),
            "current_value": current_value,
            "notes": notes,
            "status": "active",
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow(),
            "metadata": metadata or {}
        }
        
        # Store in Firestore
        doc_ref = goals_collection.add(goal_data)
        
        logger.info(f"Stored fitness goal for user {user_id}: {goal_type}")
        
        return f"Fitness goal stored successfully: {goal_type} - Target: {target_value} by {target_date}"
        
    except Exception as e:
        logger.error(f"Failed to store fitness goal: {e}")
        return f"Failed to store fitness goal: {str(e)}"

@mcp.tool()
def get_fitness_goals(
    user_id: str,
    status: Optional[str] = None,
    limit: int = 50
) -> Dict[str, Any]:
    """
    Retrieve fitness goals from Firestore.
    
    Args:
        user_id: ID of the user
        status: Status of goals to retrieve (e.g., 'active', 'completed', 'cancelled', optional)
        limit: Maximum number of goals to retrieve (default: 50)
        
    Returns:
        Dict with success status and fitness goals
    """
    try:
        # Get user's fitness goals collection
        user_collection = db.collection('users').document(str(user_id))
        goals_collection = user_collection.collection('fitness_goals')
        
        # Build query
        query = goals_collection.order_by('created_at', direction=firestore.Query.DESCENDING)
        
        if status:
            query = query.where('status', '==', status)
        
        # Execute query with limit
        goals = query.limit(limit).stream()
        
        # Convert to list of dicts
        goals_list = []
        for goal in goals:
            goal_data = goal.to_dict()
            goal_data['id'] = goal.id
            goals_list.append(goal_data)
        
        logger.info(f"Retrieved {len(goals_list)} fitness goals for user {user_id}")
        
        return {
            "success": True,
            "goals": goals_list,
            "count": len(goals_list)
        }
        
    except Exception as e:
        logger.error(f"Failed to retrieve fitness goals: {e}")
        return {
            "success": False,
            "error": str(e)
        }

@mcp.tool()
def get_user_weight_summary(
    user_id: str,
    days: int = 30
) -> Dict[str, Any]:
    """
    Get a comprehensive weight summary for a user.
    
    Args:
        user_id: ID of the user
        days: Number of days to look back for summary (default: 30)
        
    Returns:
        Dict with weight summary including trends and fitness goals
    """
    try:
        from datetime import timedelta
        
        # Calculate date range
        end_date = date.today()
        start_date = end_date - timedelta(days=days)
        
        # Get weight entries
        weight_result = get_weight_history(user_id, start_date.isoformat(), end_date.isoformat(), 100)
        weight_entries = weight_result.get('entries', []) if weight_result.get('success') else []
        
        # Get active fitness goals
        goals_result = get_fitness_goals(user_id, 'active', 10)
        active_goals = goals_result.get('goals', []) if goals_result.get('success') else []
        
        # Calculate weight trend
        weight_trend = "stable"
        if len(weight_entries) >= 2:
            recent_weight = weight_entries[0].get('weight', 0)
            older_weight = weight_entries[-1].get('weight', 0)
            if recent_weight > older_weight:
                weight_trend = "increasing"
            elif recent_weight < older_weight:
                weight_trend = "decreasing"
        
        # Calculate average weight
        avg_weight = 0
        if weight_entries:
            total_weight = sum(entry.get('weight', 0) for entry in weight_entries)
            avg_weight = total_weight / len(weight_entries)
        
        logger.info(f"Generated weight summary for user {user_id}")
        
        return {
            "success": True,
            "summary": {
                "user_id": user_id,
                "period_days": days,
                "start_date": start_date.isoformat(),
                "end_date": end_date.isoformat(),
                "weight_entries_count": len(weight_entries),
                "active_goals_count": len(active_goals),
                "weight_trend": weight_trend,
                "average_weight": round(avg_weight, 2) if avg_weight > 0 else None,
                "recent_weight": weight_entries[0].get('weight') if weight_entries else None,
                "active_goals": [goal.get('goal_type') for goal in active_goals]
            }
        }
        
    except Exception as e:
        logger.error(f"Failed to generate health summary: {e}")
        return {
            "success": False,
            "error": str(e)
        }

def main():
    """Main entry point for Weight Management Agent MCP server."""
    logger.info("Starting Weight Management Agent MCP Server via STDIO...")
    mcp.run(transport="stdio")

if __name__ == "__main__":
    main()
