from __future__ import annotations
import uuid
import datetime
from decimal import Decimal
from typing import List, Optional, Dict, Any
import asyncpg
from src.models.visionboard import (
    VisionBoard, VisionBoardCreate, VisionBoardUpdate, VisionBoardWithGenres,
    Genre, GenreCreate, GenreUpdate, GenreWithAssignments,
    Equipment, EquipmentCreate, EquipmentUpdate,
    GenreAssignment, GenreAssignmentCreate, GenreAssignmentUpdate, GenreAssignmentWithDetails,
    RequiredEquipment, RequiredEquipmentCreate, RequiredEquipmentUpdate,
    VisionBoardTask, VisionBoardTaskCreate, VisionBoardTaskUpdate, VisionBoardTaskWithDetails,
    TaskDependency, TaskDependencyCreate,
    TaskComment, TaskCommentCreate, TaskCommentUpdate,
    TaskAttachment, TaskAttachmentCreate,
    VisionBoardSummary, VisionBoardStats,
    VisionBoardStatus, AssignmentStatus, TaskStatus, EquipmentStatus
)
from src.models.user import User
import json


class VisionBoardHandler:
    def __init__(self, pool: asyncpg.Pool):
        self.pool = pool

    # Vision Board CRUD Operations
    async def create_visionboard(self, visionboard: VisionBoardCreate, created_by: uuid.UUID) -> VisionBoard:
        """Create a new vision board"""
        async with self.pool.acquire() as conn:
            query = """
                INSERT INTO visionboards (name, description, start_date, end_date, status, created_by)
                VALUES ($1, $2, $3, $4, $5, $6)
                RETURNING id, name, description, start_date, end_date, status, created_at, updated_at, created_by
            """
            row = await conn.fetchrow(
                query,
                visionboard.name,
                visionboard.description,
                visionboard.start_date,
                visionboard.end_date,
                visionboard.status.value,
                created_by
            )
            return VisionBoard(**dict(row))

    async def get_visionboard(self, visionboard_id: uuid.UUID) -> Optional[VisionBoard]:
        """Get a vision board by ID"""
        async with self.pool.acquire() as conn:
            query = """
                SELECT id, name, description, start_date, end_date, status, created_at, updated_at, created_by
                FROM visionboards WHERE id = $1
            """
            row = await conn.fetchrow(query, visionboard_id)
            return VisionBoard(**dict(row)) if row else None

    async def get_visionboard_with_genres(self, visionboard_id: uuid.UUID) -> Optional[VisionBoardWithGenres]:
        """Get a vision board with all its genres"""
        async with self.pool.acquire() as conn:
            # Get vision board
            vb_query = """
                SELECT id, name, description, start_date, end_date, status, created_at, updated_at, created_by
                FROM visionboards WHERE id = $1
            """
            vb_row = await conn.fetchrow(vb_query, visionboard_id)
            if not vb_row:
                return None

            # Get genres
            genres_query = """
                SELECT id, visionboard_id, name, description, min_required_people, max_allowed_people, created_at
                FROM genres WHERE visionboard_id = $1
            """
            genres_rows = await conn.fetch(genres_query, visionboard_id)
            
            visionboard = VisionBoard(**dict(vb_row))
            genres = [Genre(**dict(row)) for row in genres_rows]
            
            return VisionBoardWithGenres(**visionboard.model_dump(), genres=genres)

    async def update_visionboard(self, visionboard_id: uuid.UUID, updates: VisionBoardUpdate) -> Optional[VisionBoard]:
        """Update a vision board"""
        async with self.pool.acquire() as conn:
            # Build dynamic update query
            set_clauses = []
            values = []
            param_count = 1
            
            if updates.name is not None:
                set_clauses.append(f"name = ${param_count}")
                values.append(updates.name)
                param_count += 1
            
            if updates.description is not None:
                set_clauses.append(f"description = ${param_count}")
                values.append(updates.description)
                param_count += 1
            
            if updates.start_date is not None:
                set_clauses.append(f"start_date = ${param_count}")
                values.append(updates.start_date)
                param_count += 1
            
            if updates.end_date is not None:
                set_clauses.append(f"end_date = ${param_count}")
                values.append(updates.end_date)
                param_count += 1
            
            if updates.status is not None:
                set_clauses.append(f"status = ${param_count}")
                values.append(updates.status.value)
                param_count += 1
            
            if not set_clauses:
                return await self.get_visionboard(visionboard_id)
            
            set_clauses.append(f"updated_at = ${param_count}")
            values.append(datetime.datetime.utcnow())
            param_count += 1
            
            values.append(visionboard_id)
            
            query = f"""
                UPDATE visionboards 
                SET {', '.join(set_clauses)}
                WHERE id = ${param_count}
                RETURNING id, name, description, start_date, end_date, status, created_at, updated_at, created_by
            """
            
            row = await conn.fetchrow(query, *values)
            return VisionBoard(**dict(row)) if row else None

    async def delete_visionboard(self, visionboard_id: uuid.UUID) -> bool:
        """Delete a vision board (cascade will handle related data)"""
        async with self.pool.acquire() as conn:
            query = "DELETE FROM visionboards WHERE id = $1"
            result = await conn.execute(query, visionboard_id)
            return result == "DELETE 1"

    async def get_user_visionboards(self, *, user_id: uuid.UUID, status: Optional[VisionBoardStatus] = None) -> List[VisionBoard]:
        """Get all vision boards created by a user"""
        async with self.pool.acquire() as conn:
            query = "SELECT * FROM visionboards WHERE created_by = $1"
            params = [user_id]
            
            if status:
                query += " AND status = $2"
                params.append(status.value)
            
            query += " ORDER BY created_at DESC"
            
            rows = await conn.fetch(query, *params)
            return [VisionBoard(**dict(row)) for row in rows]

    async def get_user_assigned_visionboards(self, *, user_id: uuid.UUID, status: Optional[VisionBoardStatus] = None) -> List[VisionBoard]:
        """Get all vision boards where a user is assigned/partner"""
        async with self.pool.acquire() as conn:
            query = """
                SELECT DISTINCT vb.* 
                FROM visionboards vb
                JOIN genres g ON vb.id = g.visionboard_id
                JOIN genre_assignments ga ON g.id = ga.genre_id
                WHERE ga.user_id = $1
            """
            params = [user_id]
            
            if status:
                query += " AND vb.status = $2"
                params.append(status.value)
            
            query += " ORDER BY vb.created_at DESC"
            
            rows = await conn.fetch(query, *params)
            return [VisionBoard(**dict(row)) for row in rows]

    # Genre Operations
    async def create_genre(self, visionboard_id: uuid.UUID, genre: GenreCreate) -> Genre:
        """Create a new genre for a vision board"""
        async with self.pool.acquire() as conn:
            query = """
                INSERT INTO genres (visionboard_id, name, description, min_required_people, max_allowed_people)
                VALUES ($1, $2, $3, $4, $5)
                RETURNING id, visionboard_id, name, description, min_required_people, max_allowed_people, created_at
            """
            row = await conn.fetchrow(
                query,
                visionboard_id,
                genre.name,
                genre.description,
                genre.min_required_people,
                genre.max_allowed_people
            )
            return Genre(**dict(row))

    async def get_genre_with_assignments(self, genre_id: uuid.UUID) -> Optional[GenreWithAssignments]:
        """Get a genre with all its assignments"""
        async with self.pool.acquire() as conn:
            # Get genre
            genre_query = """
                SELECT id, visionboard_id, name, description, min_required_people, max_allowed_people, created_at
                FROM genres WHERE id = $1
            """
            genre_row = await conn.fetchrow(genre_query, genre_id)
            if not genre_row:
                return None

            # Get assignments
            assignments_query = """
                SELECT id, genre_id, user_id, status, work_type, payment_type, payment_amount, currency,
                       invited_at, responded_at, assigned_by
                FROM genre_assignments WHERE genre_id = $1
            """
            assignments_rows = await conn.fetch(assignments_query, genre_id)
            
            genre = Genre(**dict(genre_row))
            assignments = [GenreAssignment(**dict(row)) for row in assignments_rows]
            
            return GenreWithAssignments(**genre.model_dump(), assignments=assignments)

    # Equipment Operations
    async def create_equipment(self, equipment: EquipmentCreate) -> Equipment:
        """Create new equipment"""
        async with self.pool.acquire() as conn:
            # Serialize specifications as JSON string if it's a dict
            specs = equipment.specifications
            if isinstance(specs, dict):
                specs = json.dumps(specs)
            query = """
                INSERT INTO equipment (name, description, category, brand, model, specifications)
                VALUES ($1, $2, $3, $4, $5, $6)
                RETURNING id, name, description, category, brand, model, specifications
            """
            row = await conn.fetchrow(
                query,
                equipment.name,
                equipment.description,
                equipment.category,
                equipment.brand,
                equipment.model,
                specs
            )
            # Parse specifications back to dict if it's a string
            equipment_data = dict(row)
            if isinstance(equipment_data.get('specifications'), str):
                try:
                    equipment_data['specifications'] = json.loads(equipment_data['specifications'])
                except Exception:
                    pass
            return Equipment(**equipment_data)

    async def get_equipment_by_category(self, category: str) -> List[Equipment]:
        """Get equipment by category"""
        async with self.pool.acquire() as conn:
            query = """
                SELECT id, name, description, category, brand, model, specifications
                FROM equipment WHERE category = $1
                ORDER BY name
            """
            rows = await conn.fetch(query, category)
            equipment_list = []
            for row in rows:
                equipment_data = dict(row)
                if isinstance(equipment_data.get('specifications'), str):
                    try:
                        equipment_data['specifications'] = json.loads(equipment_data['specifications'])
                    except Exception:
                        pass
                equipment_list.append(Equipment(**equipment_data))
            return equipment_list

    # Genre Assignment Operations
    async def create_genre_assignment(self, assignment: GenreAssignmentCreate, assigned_by: uuid.UUID) -> GenreAssignment:
        """Create a new genre assignment"""
        async with self.pool.acquire() as conn:
            query = """
                INSERT INTO genre_assignments (genre_id, user_id, work_type, payment_type, payment_amount, currency, assigned_by)
                VALUES ($1, $2, $3, $4, $5, $6, $7)
                RETURNING id, genre_id, user_id, status, work_type, payment_type, payment_amount, currency,
                       invited_at, responded_at, assigned_by
            """
            row = await conn.fetchrow(
                query,
                assignment.genre_id,
                assignment.user_id,
                assignment.work_type.value,
                assignment.payment_type.value,
                assignment.payment_amount,
                assignment.currency,
                assigned_by
            )
            return GenreAssignment(**dict(row))

    async def update_assignment_status(self, assignment_id: uuid.UUID, status: AssignmentStatus, user_id: uuid.UUID) -> Optional[GenreAssignment]:
        """Update assignment status (for accepting/rejecting invitations)"""
        async with self.pool.acquire() as conn:
            query = """
                UPDATE genre_assignments 
                SET status = $1, responded_at = $2
                WHERE id = $3 AND user_id = $4
                RETURNING id, genre_id, user_id, status, work_type, payment_type, payment_amount, currency,
                       invited_at, responded_at, assigned_by
            """
            row = await conn.fetchrow(
                query,
                status.value,
                datetime.datetime.utcnow(),
                assignment_id,
                user_id
            )
            return GenreAssignment(**dict(row)) if row else None

    async def get_user_assignments(self, user_id: uuid.UUID, status: Optional[AssignmentStatus] = None) -> List[GenreAssignmentWithDetails]:
        """Get all assignments for a user with details"""
        async with self.pool.acquire() as conn:
            if status:
                query = """
                    SELECT ga.id, ga.genre_id, ga.user_id, ga.status, ga.work_type, ga.payment_type, 
                           ga.payment_amount, ga.currency, ga.invited_at, ga.responded_at, ga.assigned_by,
                           g.name as genre_name, u.name as user_name
                    FROM genre_assignments ga
                    JOIN genres g ON ga.genre_id = g.id
                    JOIN users u ON ga.user_id = u.id
                    WHERE ga.user_id = $1 AND ga.status = $2
                    ORDER BY ga.invited_at DESC
                """
                rows = await conn.fetch(query, user_id, status.value)
            else:
                query = """
                    SELECT ga.id, ga.genre_id, ga.user_id, ga.status, ga.work_type, ga.payment_type, 
                           ga.payment_amount, ga.currency, ga.invited_at, ga.responded_at, ga.assigned_by,
                           g.name as genre_name, u.name as user_name
                    FROM genre_assignments ga
                    JOIN genres g ON ga.genre_id = g.id
                    JOIN users u ON ga.user_id = u.id
                    WHERE ga.user_id = $1
                    ORDER BY ga.invited_at DESC
                """
                rows = await conn.fetch(query, user_id)
            
            assignments = []
            for row in rows:
                assignment_data = dict(row)
                genre_name = assignment_data.pop('genre_name')
                user_name = assignment_data.pop('user_name')
                
                assignment = GenreAssignment(**assignment_data)
                assignment_with_details = GenreAssignmentWithDetails(
                    **assignment.model_dump(),
                    genre_name=genre_name,
                    user_name=user_name,
                    equipment=[],  # Will be populated separately if needed
                    tasks=[]       # Will be populated separately if needed
                )
                assignments.append(assignment_with_details)
            
            return assignments

    # Task Operations
    async def create_task(self, task: VisionBoardTaskCreate, created_by: uuid.UUID) -> VisionBoardTask:
        """Create a new task"""
        async with self.pool.acquire() as conn:
            query = """
                INSERT INTO tasks (genre_assignment_id, title, description, priority, due_date, estimated_hours, created_by)
                VALUES ($1, $2, $3, $4, $5, $6, $7)
                RETURNING id, genre_assignment_id, title, description, priority, status, due_date, 
                       estimated_hours, actual_hours, created_at, updated_at, created_by
            """
            row = await conn.fetchrow(
                query,
                task.genre_assignment_id,
                task.title,
                task.description,
                task.priority.value,
                task.due_date,
                task.estimated_hours,
                created_by
            )
            return VisionBoardTask(**dict(row))

    async def update_task_status(self, task_id: uuid.UUID, status: TaskStatus, user_id: uuid.UUID) -> Optional[VisionBoardTask]:
        """Update task status"""
        async with self.pool.acquire() as conn:
            query = """
                UPDATE tasks 
                SET status = $1, updated_at = $2
                WHERE id = $3 AND created_by = $4
                RETURNING id, genre_assignment_id, title, description, priority, status, due_date, 
                       estimated_hours, actual_hours, created_at, updated_at, created_by
            """
            row = await conn.fetchrow(
                query,
                status.value,
                datetime.datetime.utcnow(),
                task_id,
                user_id
            )
            return VisionBoardTask(**dict(row)) if row else None

    async def get_task_with_details(self, task_id: uuid.UUID) -> Optional[VisionBoardTaskWithDetails]:
        """Get a task with all its details (comments, attachments, dependencies)"""
        async with self.pool.acquire() as conn:
            # Get task
            task_query = """
                SELECT t.id, t.genre_assignment_id, t.title, t.description, t.priority, t.status, 
                       t.due_date, t.estimated_hours, t.actual_hours, t.created_at, t.updated_at, t.created_by,
                       u.name as user_name, g.name as genre_name
                FROM tasks t
                JOIN genre_assignments ga ON t.genre_assignment_id = ga.id
                JOIN users u ON ga.user_id = u.id
                JOIN genres g ON ga.genre_id = g.id
                WHERE t.id = $1
            """
            task_row = await conn.fetchrow(task_query, task_id)
            if not task_row:
                return None

            # Get comments
            comments_query = """
                SELECT id, task_id, user_id, comment, created_at, updated_at
                FROM task_comments WHERE task_id = $1
                ORDER BY created_at ASC
            """
            comments_rows = await conn.fetch(comments_query, task_id)

            # Get attachments
            attachments_query = """
                SELECT id, task_id, file_name, file_url, file_type, file_size, uploaded_by, uploaded_at
                FROM task_attachments WHERE task_id = $1
                ORDER BY uploaded_at ASC
            """
            attachments_rows = await conn.fetch(attachments_query, task_id)

            # Get dependencies
            dependencies_query = """
                SELECT id, task_id, depends_on_task_id, dependency_type
                FROM task_dependencies WHERE task_id = $1
            """
            dependencies_rows = await conn.fetch(dependencies_query, task_id)

            task_data = dict(task_row)
            user_name = task_data.pop('user_name')
            genre_name = task_data.pop('genre_name')

            task = VisionBoardTask(**task_data)
            comments = [TaskComment(**dict(row)) for row in comments_rows]
            attachments = [TaskAttachment(**dict(row)) for row in attachments_rows]
            dependencies = [TaskDependency(**dict(row)) for row in dependencies_rows]

            return VisionBoardTaskWithDetails(
                **task.model_dump(),
                user_name=user_name,
                genre_name=genre_name,
                comments=comments,
                attachments=attachments,
                dependencies=dependencies
            )

    # Statistics and Analytics
    async def get_visionboard_summary(self, visionboard_id: uuid.UUID) -> Optional[VisionBoardSummary]:
        """Get comprehensive summary of a vision board"""
        async with self.pool.acquire() as conn:
            query = """
                SELECT 
                    vb.id, vb.name, vb.status, vb.start_date, vb.end_date, vb.created_by,
                    COUNT(DISTINCT g.id) as total_genres,
                    COUNT(DISTINCT ga.id) as total_assignments,
                    COUNT(DISTINCT t.id) as total_tasks,
                    COUNT(DISTINCT CASE WHEN t.status = 'Completed' THEN t.id END) as completed_tasks
                FROM visionboards vb
                LEFT JOIN genres g ON vb.id = g.visionboard_id
                LEFT JOIN genre_assignments ga ON g.id = ga.genre_id
                LEFT JOIN tasks t ON ga.id = t.genre_assignment_id
                WHERE vb.id = $1
                GROUP BY vb.id, vb.name, vb.status, vb.start_date, vb.end_date, vb.created_by
            """
            row = await conn.fetchrow(query, visionboard_id)
            if not row:
                return None
            
            return VisionBoardSummary(**dict(row))

    async def get_user_stats(self, user_id: uuid.UUID) -> VisionBoardStats:
        """Get comprehensive stats for a user"""
        async with self.pool.acquire() as conn:
            query = """
                SELECT 
                    COUNT(DISTINCT vb.id) as total_visionboards,
                    COUNT(DISTINCT CASE WHEN vb.status = 'Active' THEN vb.id END) as active_visionboards,
                    COUNT(DISTINCT CASE WHEN vb.status = 'Completed' THEN vb.id END) as completed_visionboards,
                    COUNT(DISTINCT ga.id) as total_assignments,
                    COUNT(DISTINCT CASE WHEN ga.status = 'Pending' THEN ga.id END) as pending_assignments,
                    COUNT(DISTINCT t.id) as total_tasks,
                    COUNT(DISTINCT CASE WHEN t.status = 'Completed' THEN t.id END) as completed_tasks,
                    COUNT(DISTINCT CASE WHEN t.due_date < NOW() AND t.status != 'Completed' THEN t.id END) as overdue_tasks
                FROM users u
                LEFT JOIN visionboards vb ON u.id = vb.created_by
                LEFT JOIN genre_assignments ga ON u.id = ga.user_id
                LEFT JOIN tasks t ON ga.id = t.genre_assignment_id
                WHERE u.id = $1
            """
            row = await conn.fetchrow(query, user_id)
            return VisionBoardStats(**dict(row))

    # Complex Queries (as specified in the requirements)
    async def get_visionboard_assignments(self, visionboard_id: uuid.UUID) -> List[Dict[str, Any]]:
        """Get all people assigned to a vision board"""
        async with self.pool.acquire() as conn:
            query = """
                SELECT u.name as first_name, u.name as last_name, g.name as genre, 
                       ga.status, ga.work_type, ga.payment_type, ga.payment_amount, ga.currency
                FROM users u
                JOIN genre_assignments ga ON u.id = ga.user_id
                JOIN genres g ON ga.genre_id = g.id
                WHERE g.visionboard_id = $1
                ORDER BY g.name, u.name
            """
            rows = await conn.fetch(query, visionboard_id)
            return [dict(row) for row in rows]

    async def get_user_tasks_in_visionboard(self, user_id: uuid.UUID, visionboard_id: uuid.UUID) -> List[Dict[str, Any]]:
        """Get all tasks for a specific person in a vision board"""
        async with self.pool.acquire() as conn:
            query = """
                SELECT t.title, t.description, t.status, t.due_date, t.priority, g.name as genre
                FROM tasks t
                JOIN genre_assignments ga ON t.genre_assignment_id = ga.id
                JOIN genres g ON ga.genre_id = g.id
                WHERE ga.user_id = $1 AND g.visionboard_id = $2
                ORDER BY t.due_date ASC, t.priority DESC
            """
            rows = await conn.fetch(query, user_id, visionboard_id)
            return [dict(row) for row in rows]

    async def get_visionboard_equipment_requirements(self, visionboard_id: uuid.UUID) -> List[Dict[str, Any]]:
        """Get equipment requirements for a vision board"""
        async with self.pool.acquire() as conn:
            query = """
                SELECT 
                    e.name as equipment_name,
                    e.category,
                    e.brand,
                    e.model,
                    re.quantity,
                    re.is_provided_by_assignee,
                    re.notes,
                    re.status,
                    u.name as assigned_user_name,
                    g.name as genre_name
                FROM required_equipment re
                JOIN equipment e ON re.equipment_id = e.id
                JOIN genre_assignments ga ON re.genre_assignment_id = ga.id
                JOIN users u ON ga.user_id = u.id
                JOIN genres g ON ga.genre_id = g.id
                WHERE g.visionboard_id = $1
                ORDER BY g.name, e.category, e.name
            """
            rows = await conn.fetch(query, visionboard_id)
            return [dict(row) for row in rows]

    async def get_visionboard_users(self, visionboard_id: uuid.UUID) -> List[User]:
        """Get all users involved in a vision board (creator + assigned users)"""
        async with self.pool.acquire() as conn:
            # Get the vision board creator
            creator_query = "SELECT created_by FROM visionboards WHERE id = $1"
            creator_row = await conn.fetchrow(creator_query, visionboard_id)
            if not creator_row:
                return []
            
            creator_id = creator_row['created_by']
            
            # Get all assigned users
            assigned_users_query = """
                SELECT DISTINCT u.*
                FROM users u
                JOIN genre_assignments ga ON u.id = ga.user_id
                JOIN genres g ON ga.genre_id = g.id
                WHERE g.visionboard_id = $1
            """
            assigned_rows = await conn.fetch(assigned_users_query, visionboard_id)
            assigned_users = []
            for row in assigned_rows:
                row_dict = dict(row)
                # Parse location field
                if 'location' in row_dict and isinstance(row_dict['location'], str):
                    try:
                        row_dict['location'] = json.loads(row_dict['location'])
                    except Exception:
                        row_dict['location'] = None
                # Parse genres field
                if 'genres' in row_dict and isinstance(row_dict['genres'], str):
                    try:
                        row_dict['genres'] = json.loads(row_dict['genres'])
                    except Exception:
                        row_dict['genres'] = None
                assigned_users.append(User(**row_dict))
            
            # Get creator user details
            creator_query = "SELECT * FROM users WHERE id = $1"
            creator_row = await conn.fetchrow(creator_query, creator_id)
            creator_user = None
            if creator_row:
                creator_dict = dict(creator_row)
                # Parse location field
                if 'location' in creator_dict and isinstance(creator_dict['location'], str):
                    try:
                        creator_dict['location'] = json.loads(creator_dict['location'])
                    except Exception:
                        creator_dict['location'] = None
                # Parse genres field
                if 'genres' in creator_dict and isinstance(creator_dict['genres'], str):
                    try:
                        creator_dict['genres'] = json.loads(creator_dict['genres'])
                    except Exception:
                        creator_dict['genres'] = None
                creator_user = User(**creator_dict)
            
            # Combine creator and assigned users, removing duplicates
            all_users = assigned_users
            if creator_user and not any(user.id == creator_user.id for user in assigned_users):
                all_users.append(creator_user)
            
            return all_users 