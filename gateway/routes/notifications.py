"""
Inventory Notifications Routes
Provides endpoints for querying inventory notifications and alerts
"""

from fastapi import APIRouter, HTTPException, Query
from typing import Dict, Any
from datetime import datetime

router = APIRouter(prefix="/api/v1/notifications", tags=["notifications"])


class NotificationResponse:
    """Response model for notifications"""
    
    @staticmethod
    def inventory_update_response(item_id: int, product_id: str, change: int) -> Dict[str, Any]:
        return {
            "notification_type": "inventory_updated",
            "item_id": item_id,
            "product_id": product_id,
            "quantity_change": change,
            "timestamp": datetime.utcnow().isoformat(),
            "status": "acknowledged"
        }
    
    @staticmethod
    def low_stock_alert_response(product_id: str, current: int, threshold: int) -> Dict[str, Any]:
        return {
            "notification_type": "low_stock_alert",
            "product_id": product_id,
            "current_quantity": current,
            "threshold": threshold,
            "severity": "critical" if current == 0 else "warning",
            "timestamp": datetime.utcnow().isoformat(),
            "status": "acknowledged"
        }


@router.get("/", summary="List all notifications")
async def list_notifications(
    limit: int = Query(100, le=1000),
    offset: int = Query(0, ge=0),
    notification_type: str = Query(None)
) -> Dict[str, Any]:
    """
    List all inventory notifications
    
    Query Parameters:
    - limit: Maximum number of notifications to return (default: 100, max: 1000)
    - offset: Number of notifications to skip (default: 0)
    - notification_type: Filter by notification type (optional)
    
    Returns:
    - List of notifications with pagination info
    """
    from services.event_consumer import get_event_consumer
    
    consumer = get_event_consumer()
    history = consumer.get_history(limit=limit + offset)
    
    # Filter by type if specified
    if notification_type:
        history = [
            h for h in history 
            if h.get('message', {}).get('event_type') == notification_type
        ]
    
    # Apply offset and limit
    notifications = history[offset:offset + limit]
    
    return {
        "notifications": notifications,
        "total_count": len(history),
        "limit": limit,
        "offset": offset,
        "returned_count": len(notifications),
        "has_more": (offset + limit) < len(history)
    }


@router.get("/low-stock", summary="Get low stock alerts")
async def get_low_stock_alerts(
    limit: int = Query(50, le=1000)
) -> Dict[str, Any]:
    """
    Get all low stock alerts
    
    Query Parameters:
    - limit: Maximum number of alerts to return
    
    Returns:
    - List of low stock alerts sorted by severity and timestamp
    """
    from services.event_consumer import get_event_consumer
    
    consumer = get_event_consumer()
    history = consumer.get_history(limit=limit * 2)  # Get more to filter
    
    # Filter only low stock alerts
    low_stock_alerts = [
        h for h in history
        if h.get('message', {}).get('event_type') == 'low_stock_alert'
    ]
    
    # Sort by severity (critical first) and then by timestamp
    low_stock_alerts.sort(
        key=lambda x: (
            x.get('message', {}).get('severity') != 'critical',
            x.get('processed_at', '')
        ),
        reverse=True
    )
    
    return {
        "low_stock_alerts": low_stock_alerts[:limit],
        "total_count": len(low_stock_alerts),
        "critical_count": len([
            a for a in low_stock_alerts 
            if a.get('message', {}).get('severity') == 'critical'
        ])
    }


@router.get("/recent", summary="Get recent notifications")
async def get_recent_notifications(
    hours: int = Query(24, ge=1, le=720)
) -> Dict[str, Any]:
    """
    Get recent notifications from the last N hours
    
    Query Parameters:
    - hours: Look back period in hours (1-720 hours)
    
    Returns:
    - List of recent notifications
    """
    from datetime import timedelta
    from services.event_consumer import get_event_consumer
    
    consumer = get_event_consumer()
    history = consumer.get_history(limit=1000)
    
    cutoff_time = datetime.utcnow() - timedelta(hours=hours)
    
    # Filter recent notifications
    recent = [
        h for h in history
        if datetime.fromisoformat(h.get('processed_at', '')) >= cutoff_time
    ]
    
    # Group by event type
    by_type = {}
    for notification in recent:
        event_type = notification.get('message', {}).get('event_type', 'unknown')
        if event_type not in by_type:
            by_type[event_type] = []
        by_type[event_type].append(notification)
    
    return {
        "recent_notifications": recent,
        "grouped_by_type": by_type,
        "total_count": len(recent),
        "lookback_hours": hours,
        "stats": {
            event_type: len(notifications)
            for event_type, notifications in by_type.items()
        }
    }


@router.get("/summary", summary="Get notifications summary")
async def get_notifications_summary() -> Dict[str, Any]:
    """
    Get a summary of all notifications
    
    Returns:
    - Summary statistics of notifications
    """
    from services.event_consumer import get_event_consumer
    
    consumer = get_event_consumer()
    history = consumer.get_history(limit=1000)
    
    # Calculate stats
    by_type = {}
    critical_alerts = 0
    
    for notification in history:
        event_type = notification.get('message', {}).get('event_type', 'unknown')
        by_type[event_type] = by_type.get(event_type, 0) + 1
        
        if (notification.get('message', {}).get('event_type') == 'low_stock_alert' and
            notification.get('message', {}).get('severity') == 'critical'):
            critical_alerts += 1
    
    return {
        "summary": {
            "total_notifications": len(history),
            "critical_alerts": critical_alerts,
            "by_type": by_type
        },
        "timestamp": datetime.utcnow().isoformat(),
        "queue_status": "operational"
    }


@router.get("/by-product/{product_id}", summary="Get notifications for a product")
async def get_product_notifications(
    product_id: str,
    limit: int = Query(50, le=500)
) -> Dict[str, Any]:
    """
    Get all notifications for a specific product
    
    Path Parameters:
    - product_id: Product identifier
    
    Query Parameters:
    - limit: Maximum number of notifications to return
    
    Returns:
    - List of notifications for the product
    """
    from services.event_consumer import get_event_consumer
    
    consumer = get_event_consumer()
    history = consumer.get_history(limit=limit * 2)
    
    # Filter by product_id
    product_notifications = [
        h for h in history
        if h.get('message', {}).get('payload', {}).get('product_id') == product_id or
           h.get('message', {}).get('payload', {}).get('product_id') == product_id
    ]
    
    if not product_notifications:
        raise HTTPException(status_code=404, detail=f"No notifications found for product {product_id}")
    
    return {
        "product_id": product_id,
        "notifications": product_notifications[:limit],
        "total_count": len(product_notifications)
    }


@router.get("/health", summary="Check notifications service health")
async def notifications_health() -> Dict[str, Any]:
    """
    Check the health status of the notifications service
    
    Returns:
    - Health status and queue information
    """
    from services.event_consumer import get_event_consumer
    
    try:
        consumer = get_event_consumer()
        history_size = len(consumer.alert_history)
        
        return {
            "status": "healthy",
            "service": "notifications",
            "timestamp": datetime.utcnow().isoformat(),
            "event_consumer": {
                "initialized": True,
                "handlers_registered": len(consumer.handlers),
                "history_size": history_size,
                "max_history": consumer.max_history
            },
            "queues": {
                "inventory_updates": "listening",
                "low_stock_alerts": "listening",
                "stock_validation": "listening",
                "stock_reserved": "listening"
            }
        }
    except Exception as e:
        return {
            "status": "unhealthy",
            "service": "notifications",
            "error": str(e),
            "timestamp": datetime.utcnow().isoformat()
        }
