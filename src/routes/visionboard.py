from __future__ import annotations
import uuid
from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import JSONResponse
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
import decimal
import datetime
from typing import List

from src.app import app
from src.utils import Token, TokenHandler
from src.utils.visionboard_handler import VisionBoardHandler
from src.models.visionboard import (
    VisionBoardCreate, VisionBoardUpdate, VisionBoardWithGenres,
    GenreCreate, GenreUpdate, GenreWithAssignments,
    EquipmentCreate, EquipmentUpdate,
    GenreAssignmentCreate, GenreAssignmentUpdate,
    RequiredEquipmentCreate, RequiredEquipmentUpdate,
    VisionBoardTaskCreate, VisionBoardTaskUpdate, VisionBoardTaskWithDetails,
    TaskDependencyCreate,
    TaskCommentCreate, TaskCommentUpdate,
    TaskAttachmentCreate,
    VisionBoardStatus, AssignmentStatus, TaskStatus,
    Invitation, InvitationCreate, InvitationUpdate, InvitationStatus
)
from src.models.notification import Notification

router = APIRouter(prefix="/v1/visionboard", tags=["Vision Board"])
security = HTTPBearer()

# Initialize handlers (lazy initialization)
visionboard_handler = None
token_handler = None

def get_visionboard_handler():
    global visionboard_handler
    if visionboard_handler is None:
        visionboard_handler = VisionBoardHandler(app.state.pool)
    return visionboard_handler

def get_token_handler():
    global token_handler
    if token_handler is None:
        token_handler = TokenHandler(app.state.jwt_secret)
    return token_handler

def get_user_token(credentials: HTTPAuthorizationCredentials = Depends(security)):
    token = get_token_handler().decode_token(credentials.credentials)
    print('DEBUG: Decoded token:', token)
    return token

def to_serializable(obj):
    if isinstance(obj, decimal.Decimal):
        return float(obj)
    if isinstance(obj, (datetime.datetime, datetime.date)):
        return obj.isoformat()
    if isinstance(obj, dict):
        return {k: to_serializable(v) for k, v in obj.items()}
    if isinstance(obj, list):
        return [to_serializable(i) for i in obj]
    return obj

# Vision Board CRUD Operations
@router.post("/create")
async def create_visionboard(
    request: Request, 
    visionboard: VisionBoardCreate, 
    token: Token = Depends(get_user_token)
):
    """Create a new vision board"""
    try:
        created_visionboard = await get_visionboard_handler().create_visionboard(
            visionboard=visionboard, 
            created_by=token.sub
        )
        return JSONResponse({
            "message": "Vision board created successfully",
            "visionboard": created_visionboard.model_dump(mode="json")
        })
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/{visionboard_id}")
async def get_visionboard(
    request: Request, 
    visionboard_id: str, 
    token: Token = Depends(get_user_token)
):
    """Get a vision board by ID"""
    try:
        visionboard = await get_visionboard_handler().get_visionboard(uuid.UUID(visionboard_id))
        if not visionboard:
            raise HTTPException(status_code=404, detail="Vision board not found")
        
        return JSONResponse({
            "message": "success",
            "visionboard": visionboard.model_dump(mode="json")
        })
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid vision board ID")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/{visionboard_id}/with-genres")
async def get_visionboard_with_genres(
    request: Request, 
    visionboard_id: str, 
    token: Token = Depends(get_user_token)
):
    """Get a vision board with all its genres"""
    try:
        visionboard = await get_visionboard_handler().get_visionboard_with_genres(uuid.UUID(visionboard_id))
        if not visionboard:
            raise HTTPException(status_code=404, detail="Vision board not found")
        
        return JSONResponse({
            "message": "success",
            "visionboard": visionboard.model_dump(mode="json")
        })
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid vision board ID")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.put("/{visionboard_id}")
async def update_visionboard(
    request: Request, 
    visionboard_id: str, 
    updates: VisionBoardUpdate, 
    token: Token = Depends(get_user_token)
):
    """Update a vision board"""
    try:
        visionboard = await get_visionboard_handler().update_visionboard(
            uuid.UUID(visionboard_id), 
            updates
        )
        if not visionboard:
            raise HTTPException(status_code=404, detail="Vision board not found")
        
        return JSONResponse({
            "message": "Vision board updated successfully",
            "visionboard": visionboard.model_dump(mode="json")
        })
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid vision board ID")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.delete("/{visionboard_id}")
async def delete_visionboard(
    request: Request, 
    visionboard_id: str, 
    token: Token = Depends(get_user_token)
):
    """Delete a vision board"""
    try:
        success = await get_visionboard_handler().delete_visionboard(uuid.UUID(visionboard_id))
        if not success:
            raise HTTPException(status_code=404, detail="Vision board not found")
        
        return JSONResponse({"message": "Vision board deleted successfully"})
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid vision board ID")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/user/visionboards")
async def get_user_visionboards(
    request: Request, 
    status: str = None,
    token: Token = Depends(get_user_token)
):
    """Get all vision boards created by the current user"""
    try:
        visionboard_status = None
        if status:
            try:
                visionboard_status = VisionBoardStatus(status)
            except ValueError:
                raise HTTPException(status_code=400, detail="Invalid status")
        
        visionboards = await get_visionboard_handler().get_user_visionboards(
            user_id=token.sub, 
            status=visionboard_status
        )
        
        return JSONResponse({
            "message": "success",
            "visionboards": [vb.model_dump(mode="json") for vb in visionboards]
        })
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("")
async def get_visionboards_by_query(
    request: Request,
    created_by: str = None,
    partner_id: str = None,
    status: str = None,
    token: Token = Depends(get_user_token)
):
    """Get vision boards by query parameters"""
    try:
        visionboard_status = None
        if status:
            try:
                visionboard_status = VisionBoardStatus(status)
            except ValueError:
                raise HTTPException(status_code=400, detail="Invalid status")
        
        if created_by:
            # Get vision boards created by a specific user
            try:
                user_uuid = uuid.UUID(created_by)
                visionboards = await get_visionboard_handler().get_user_visionboards(
                    user_id=user_uuid,
                    status=visionboard_status
                )
                return JSONResponse({
                    "message": "success",
                    "visionboards": [vb.model_dump(mode="json") for vb in visionboards]
                })
            except ValueError:
                raise HTTPException(status_code=400, detail="Invalid user ID")
        
        elif partner_id:
            # Get vision boards where user is assigned/partner
            try:
                user_uuid = uuid.UUID(partner_id)
                visionboards = await get_visionboard_handler().get_user_assigned_visionboards(
                    user_id=user_uuid,
                    status=visionboard_status
                )
                return JSONResponse({
                    "message": "success",
                    "visionboards": [vb.model_dump(mode="json") for vb in visionboards]
                })
            except ValueError:
                raise HTTPException(status_code=400, detail="Invalid user ID")
        
        else:
            # Default: get current user's vision boards
            visionboards = await get_visionboard_handler().get_user_visionboards(
                user_id=token.sub,
                status=visionboard_status
            )
            return JSONResponse({
                "message": "success",
                "visionboards": [vb.model_dump(mode="json") for vb in visionboards]
            })
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# Genre Operations
@router.post("/{visionboard_id}/genres")
async def create_genre(
    request: Request, 
    visionboard_id: str, 
    genre: GenreCreate, 
    token: Token = Depends(get_user_token)
):
    """Create a new genre for a vision board"""
    try:
        created_genre = await get_visionboard_handler().create_genre(
            visionboard_id=uuid.UUID(visionboard_id), 
            genre=genre
        )
        return JSONResponse({
            "message": "Genre created successfully",
            "genre": created_genre.model_dump(mode="json")
        })
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid vision board ID")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/genres/{genre_id}/with-assignments")
async def get_genre_with_assignments(
    request: Request, 
    genre_id: str, 
    token: Token = Depends(get_user_token)
):
    """Get a genre with all its assignments"""
    try:
        genre = await get_visionboard_handler().get_genre_with_assignments(uuid.UUID(genre_id))
        if not genre:
            raise HTTPException(status_code=404, detail="Genre not found")
        
        return JSONResponse({
            "message": "success",
            "genre": genre.model_dump(mode="json")
        })
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid genre ID")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# Equipment Operations
@router.post("/equipment")
async def create_equipment(
    request: Request, 
    equipment: EquipmentCreate, 
    token: Token = Depends(get_user_token)
):
    """Create new equipment"""
    try:
        created_equipment = await get_visionboard_handler().create_equipment(equipment)
        return JSONResponse({
            "message": "Equipment created successfully",
            "equipment": created_equipment.model_dump(mode="json")
        })
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/equipment/category/{category}")
async def get_equipment_by_category(
    request: Request, 
    category: str, 
    token: Token = Depends(get_user_token)
):
    """Get equipment by category"""
    try:
        equipment = await get_visionboard_handler().get_equipment_by_category(category)
        return JSONResponse({
            "message": "success",
            "equipment": [eq.model_dump(mode="json") for eq in equipment]
        })
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# Genre Assignment Operations
@router.post("/assignments")
async def create_genre_assignment(
    request: Request, 
    assignment: GenreAssignmentCreate, 
    token: Token = Depends(get_user_token)
):
    """Create a new genre assignment (invite someone to a role)"""
    try:
        created_assignment = await get_visionboard_handler().create_genre_assignment(
            assignment=assignment, 
            assigned_by=token.sub
        )
        return JSONResponse({
            "message": "Assignment created successfully",
            "assignment": created_assignment.model_dump(mode="json")
        })
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.put("/assignments/{assignment_id}/status")
async def update_assignment_status(
    request: Request, 
    assignment_id: str, 
    status: str, 
    token: Token = Depends(get_user_token)
):
    """Update assignment status (accept/reject invitation)"""
    try:
        try:
            assignment_status = AssignmentStatus(status)
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid status")
        
        assignment = await get_visionboard_handler().update_assignment_status(
            assignment_id=uuid.UUID(assignment_id), 
            status=assignment_status, 
            user_id=token.sub
        )
        if not assignment:
            raise HTTPException(status_code=404, detail="Assignment not found")
        
        return JSONResponse({
            "message": "Assignment status updated successfully",
            "assignment": assignment.model_dump(mode="json")
        })
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid assignment ID")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/user/assignments")
async def get_user_assignments(
    request: Request, 
    status: str = None,
    token: Token = Depends(get_user_token)
):
    """Get all assignments for the current user"""
    try:
        assignment_status = None
        if status:
            try:
                assignment_status = AssignmentStatus(status)
            except ValueError:
                raise HTTPException(status_code=400, detail="Invalid status")
        
        assignments = await get_visionboard_handler().get_user_assignments(
            user_id=token.sub, 
            status=assignment_status
        )
        
        return JSONResponse({
            "message": "success",
            "assignments": [assignment.model_dump(mode="json") for assignment in assignments]
        })
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# Task Operations
@router.post("/tasks")
async def create_task(
    request: Request, 
    task: VisionBoardTaskCreate, 
    token: Token = Depends(get_user_token)
):
    """Create a new task"""
    try:
        created_task = await get_visionboard_handler().create_task(
            task=task, 
            created_by=token.sub
        )
        return JSONResponse({
            "message": "Task created successfully",
            "task": created_task.model_dump(mode="json")
        })
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.put("/tasks/{task_id}/status")
async def update_task_status(
    request: Request, 
    task_id: str, 
    status: str, 
    token: Token = Depends(get_user_token)
):
    """Update task status"""
    try:
        try:
            task_status = TaskStatus(status)
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid status")
        
        task = await get_visionboard_handler().update_task_status(
            task_id=uuid.UUID(task_id), 
            status=task_status, 
            user_id=token.sub
        )
        if not task:
            raise HTTPException(status_code=404, detail="Task not found")
        
        return JSONResponse({
            "message": "Task status updated successfully",
            "task": task.model_dump(mode="json")
        })
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid task ID")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/tasks/{task_id}/with-details")
async def get_task_with_details(
    request: Request, 
    task_id: str, 
    token: Token = Depends(get_user_token)
):
    """Get a task with all its details (comments, attachments, dependencies)"""
    try:
        task = await get_visionboard_handler().get_task_with_details(uuid.UUID(task_id))
        if not task:
            raise HTTPException(status_code=404, detail="Task not found")
        
        return JSONResponse({
            "message": "success",
            "task": task.model_dump(mode="json")
        })
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid task ID")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# Analytics and Statistics
@router.get("/{visionboard_id}/summary")
async def get_visionboard_summary(
    request: Request, 
    visionboard_id: str, 
    token: Token = Depends(get_user_token)
):
    """Get comprehensive summary of a vision board"""
    try:
        summary = await get_visionboard_handler().get_visionboard_summary(uuid.UUID(visionboard_id))
        if not summary:
            raise HTTPException(status_code=404, detail="Vision board not found")
        
        return JSONResponse({
            "message": "success",
            "summary": summary.model_dump(mode="json")
        })
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid vision board ID")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/user/stats")
async def get_user_stats(
    request: Request, 
    token: Token = Depends(get_user_token)
):
    """Get comprehensive stats for the current user"""
    try:
        stats = await get_visionboard_handler().get_user_stats(token.sub)
        return JSONResponse({
            "message": "success",
            "stats": stats.model_dump(mode="json")
        })
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# Complex Queries (as specified in requirements)
@router.get("/{visionboard_id}/assignments")
async def get_visionboard_assignments(
    request: Request, 
    visionboard_id: str, 
    token: Token = Depends(get_user_token)
):
    """Get all people assigned to a vision board"""
    try:
        assignments = await get_visionboard_handler().get_visionboard_assignments(uuid.UUID(visionboard_id))
        return JSONResponse({
            "message": "success",
            "assignments": to_serializable(assignments)
        })
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid vision board ID")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/{visionboard_id}/user/{user_id}/tasks")
async def get_user_tasks_in_visionboard(
    request: Request, 
    visionboard_id: str, 
    user_id: str, 
    token: Token = Depends(get_user_token)
):
    """Get all tasks for a specific person in a vision board"""
    try:
        tasks = await get_visionboard_handler().get_user_tasks_in_visionboard(
            user_id=uuid.UUID(user_id), 
            visionboard_id=uuid.UUID(visionboard_id)
        )
        return JSONResponse({
            "message": "success",
            "tasks": to_serializable(tasks)
        })
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid ID")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/{visionboard_id}/equipment-requirements")
async def get_visionboard_equipment_requirements(
    request: Request, 
    visionboard_id: str, 
    token: Token = Depends(get_user_token)
):
    """Get equipment requirements for a vision board"""
    try:
        equipment = await get_visionboard_handler().get_visionboard_equipment_requirements(uuid.UUID(visionboard_id))
        return JSONResponse({
            "message": "success",
            "equipment_requirements": equipment
        })
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid vision board ID")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/notifications")
async def get_notifications(token: Token = Depends(get_user_token)):
    """
    Fetch all notifications for the logged-in user.
    """
    handler = get_visionboard_handler()
    notifications = await handler.get_notifications_for_user(token.sub)
    return {"notifications": [n.model_dump(mode="json") for n in notifications]}

@router.get("/{visionboard_id}/users")
async def get_visionboard_users(
    request: Request, 
    visionboard_id: str, 
    token: Token = Depends(get_user_token)
):
    """Get all users involved in a vision board (creator + assigned users)"""
    try:
        print(f"DEBUG: Raw visionboard_id received: '{visionboard_id}'")
        # Convert to lowercase to handle case sensitivity issues
        visionboard_id_lower = visionboard_id.lower()
        print(f"DEBUG: Lowercase visionboard_id: '{visionboard_id_lower}'")
        users = await get_visionboard_handler().get_visionboard_users(uuid.UUID(visionboard_id_lower))
        return JSONResponse({
            "message": "success",
            "users": [user.model_dump(mode="json") for user in users]
        })
    except ValueError as ve:
        print(f"DEBUG: ValueError for visionboard_id: '{visionboard_id}' - {ve}")
        raise HTTPException(status_code=400, detail="Invalid vision board ID")
    except Exception as e:
        print(f"DEBUG: Exception in get_visionboard_users: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/notifications/batch-create")
async def batch_create_notifications(request: Request, notifications: List[dict], token: Token = Depends(get_user_token)):
    """Batch create notifications for multiple events."""
    handler = get_visionboard_handler()
    created = []
    for notif in notifications:
        await handler.create_notification(
            receiver_id=notif["receiver_id"],
            sender_id=token.sub,
            object_type=notif["object_type"],
            object_id=notif["object_id"],
            event_type=notif["event_type"],
            data=notif.get("data"),
            message=notif.get("message")
        )
        created.append(notif["receiver_id"])
    return {"message": "Notifications created", "notified_users": created}

@router.post("/notifications/{notification_id}/respond")
async def respond_to_notification(notification_id: uuid.UUID, response: str, comment: str = None, token: Token = Depends(get_user_token)):
    """Accept or reject an invitation and notify the sender."""
    handler = get_visionboard_handler()
    notif = await handler.respond_to_notification(notification_id, responder_id=token.sub, response=response, comment=comment)
    if notif is None:
        raise HTTPException(status_code=404, detail="Notification not found or not allowed")
    return {"message": f"Invitation {response.lower()}.", "notification": notif.model_dump(mode="json")}

# Invitation Endpoints
@router.post("/invitations")
async def create_invitation(
    request: Request,
    invitation: InvitationCreate,
    token: Token = Depends(get_user_token)
):
    """Create a new invitation (generic)"""
    handler = get_visionboard_handler()
    inv = await handler.create_invitation(sender_id=token.sub, invitation=invitation)
    # Optionally, send a notification here
    await handler.create_notification(
        receiver_id=invitation.receiver_id,
        sender_id=token.sub,
        object_type=invitation.object_type,
        object_id=invitation.object_id,
        event_type="invited",
        data=invitation.data,
        message=f"You have been invited to a {invitation.object_type}."
    )
    return {"message": "Invitation created", "invitation": inv.model_dump(mode="json")}

@router.get("/invitations/user")
async def get_user_invitations(
    request: Request,
    status: str = None,
    token: Token = Depends(get_user_token)
):
    """Get all invitations for the current user (optionally filter by status)"""
    handler = get_visionboard_handler()
    inv_status = None
    if status:
        try:
            inv_status = InvitationStatus(status)
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid invitation status")
    invitations = await handler.get_invitations_for_user(token.sub, status=inv_status)
    return {"invitations": [i.model_dump(mode="json") for i in invitations]}

@router.get("/invitations/object/{object_type}/{object_id}")
async def get_object_invitations(
    request: Request,
    object_type: str,
    object_id: str,
    token: Token = Depends(get_user_token)
):
    """Get all invitations for a given object (e.g., visionboard, genre, etc.)"""
    handler = get_visionboard_handler()
    try:
        obj_uuid = uuid.UUID(object_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid object ID")
    invitations = await handler.get_invitations_for_object(object_type, obj_uuid)
    return {"invitations": [i.model_dump(mode="json") for i in invitations]}

@router.post("/invitations/{invitation_id}/respond")
async def respond_to_invitation(
    invitation_id: str,
    response: str,
    data: dict = None,
    token: Token = Depends(get_user_token)
):
    """Accept or reject an invitation (only receiver can respond)"""
    handler = get_visionboard_handler()
    try:
        inv_uuid = uuid.UUID(invitation_id)
        status = InvitationStatus(response)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid invitation ID or response")
    inv = await handler.respond_to_invitation(inv_uuid, responder_id=token.sub, status=status, data=data)
    if not inv:
        raise HTTPException(status_code=404, detail="Invitation not found or not allowed")
    # Optionally, send a notification to the sender
    await handler.create_notification(
        receiver_id=inv.sender_id,
        sender_id=token.sub,
        object_type=inv.object_type,
        object_id=inv.object_id,
        event_type="invitation_response",
        data={"response": response, "data": data},
        message=f"User responded: {response} to your invitation."
    )
    return {"message": f"Invitation {response.lower()}.", "invitation": inv.model_dump(mode="json")}

# Include the router in the main app
app.include_router(router) 