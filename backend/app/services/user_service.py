"""
User service for managing user authentication and user management
"""
import logging
from typing import List, Optional
from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, delete, desc

from app.models.user import User, UserRole
from app.models.user_role import UserRole as UserRoleMap
from app.models.role import Role
from app.schemas.user import UserCreate, UserUpdate
from app.core.security import get_password_hash, verify_password

logger = logging.getLogger(__name__)


class UserService:
    """Service for managing users"""
    
    def __init__(self, db: AsyncSession):
        self.db = db
    
    async def create_user(self, user_data: UserCreate) -> User:
        """Create a new user"""
        try:
            # Check if user already exists
            existing_user = await self.get_user_by_email(user_data.email)
            if existing_user:
                raise ValueError("User with this email already exists")
            
            # Check if username is taken
            existing_username = await self.get_user_by_username(user_data.username)
            if existing_username:
                raise ValueError("Username already taken")
            
            # Hash password
            hashed_password = get_password_hash(user_data.password)
            
            # Create user
            user = User(
                username=user_data.username,
                email=user_data.email,
                hashed_password=hashed_password,
                full_name=user_data.full_name,
                phone=user_data.phone,
                department=user_data.department,
                position=user_data.position,
                employee_id=user_data.employee_id,
                role=user_data.role or UserRole.EMPLOYEE,
                bio=user_data.bio,
                created_by=None,
                updated_by=None
            )
            
            self.db.add(user)
            await self.db.commit()
            await self.db.refresh(user)
            # 标记创建与更新者（由上层endpoint补充具体ID）
            # Assign role mapping if role_id provided
            if user_data.role_id:
                await self._set_user_roles(user.id, [user_data.role_id])
                await self.db.commit()
            
            logger.info(f"Created user {user.id} with email {user.email}")
            return user
            
        except Exception as e:
            await self.db.rollback()
            logger.error(f"Error creating user: {e}")
            raise
    
    async def authenticate(self, username_or_email: str, password: str) -> Optional[User]:
        """Authenticate a user by username or email and password"""
        try:
            # Try username first
            user = await self.get_user_by_username(username_or_email)
            if not user:
                # Try email
                user = await self.get_user_by_email(username_or_email)
            
            if not user:
                return None
            
            if not verify_password(password, user.hashed_password):
                return None
            
            # Update last login
            await self._update_last_login(user.id)
            
            return user
            
        except Exception as e:
            logger.error(f"Error authenticating user: {e}")
            return None

    async def authenticate_user(self, email: str, password: str) -> Optional[User]:
        """Authenticate a user by email and password"""
        try:
            user = await self.get_user_by_email(email)
            if not user:
                return None
            
            if not verify_password(password, user.hashed_password):
                return None
            
            # Update last login
            await self._update_last_login(user.id)
            
            return user
            
        except Exception as e:
            logger.error(f"Error authenticating user: {e}")
            return None
    
    async def get_user(self, user_id: UUID) -> Optional[User]:
        """Get a user by ID"""
        try:
            query = select(User).where(User.id == user_id, User.is_active == True)
            result = await self.db.execute(query)
            return result.scalar_one_or_none()
            
        except Exception as e:
            logger.error(f"Error getting user {user_id}: {e}")
            raise
    
    async def get_user_by_email(self, email: str) -> Optional[User]:
        """Get a user by email"""
        try:
            query = select(User).where(User.email == email, User.is_active == True)
            result = await self.db.execute(query)
            return result.scalar_one_or_none()
            
        except Exception as e:
            logger.error(f"Error getting user by email {email}: {e}")
            raise
    
    async def get_user_by_username(self, username: str) -> Optional[User]:
        """Get a user by username"""
        try:
            query = select(User).where(User.username == username, User.is_active == True)
            result = await self.db.execute(query)
            return result.scalar_one_or_none()
            
        except Exception as e:
            logger.error(f"Error getting user by username {username}: {e}")
            raise
    
    async def get_users(
        self,
        skip: int = 0,
        limit: int = 20,
        role: Optional[UserRole] = None,
        department: Optional[str] = None
    ) -> List[User]:
        """Get all users with optional filtering"""
        try:
            query = select(User).where(User.is_active == True)
            
            if role:
                query = query.where(User.role == role)
            
            if department:
                query = query.where(User.department == department)
            
            query = query.order_by(desc(User.created_at)).offset(skip).limit(limit)
            
            result = await self.db.execute(query)
            return result.scalars().all()
            
        except Exception as e:
            logger.error(f"Error getting users: {e}")
            raise
    
    async def update_user(
        self,
        user_id: UUID,
        user_data: UserUpdate,
        current_user: User
    ) -> Optional[User]:
        """Update a user"""
        try:
            # Get the user to update
            user = await self.get_user(user_id)
            if not user:
                return None
            
            # Check permissions
            if not self._can_update_user(current_user, user):
                raise PermissionError("Insufficient permissions to update this user")
            
            # Prepare update data
            update_data = user_data.dict(exclude_unset=True, exclude={'password', 'role_id'})
            
            # Handle password update separately
            if user_data.password:
                update_data['hashed_password'] = get_password_hash(user_data.password)
            
            # Check for email/username conflicts
            if 'email' in update_data and update_data['email'] != user.email:
                existing_email = await self.get_user_by_email(update_data['email'])
                if existing_email and existing_email.id != user_id:
                    raise ValueError("Email already in use")
            
            if 'username' in update_data and update_data['username'] != user.username:
                existing_username = await self.get_user_by_username(update_data['username'])
                if existing_username and existing_username.id != user_id:
                    raise ValueError("Username already taken")
            
            # Update user
            if update_data:
                query = (
                    update(User)
                    .where(User.id == user_id)
                    .values(**update_data, updated_by=current_user.id)
                )
                await self.db.execute(query)
                await self.db.commit()
                await self.db.refresh(user)

            # Update role mapping if provided
            if user_data.role_id:
                await self._set_user_roles(user_id, [user_data.role_id])
                await self.db.commit()
            
            logger.info(f"Updated user {user_id}")
            return user
            
        except Exception as e:
            await self.db.rollback()
            logger.error(f"Error updating user {user_id}: {e}")
            raise
    
    async def delete_user(
        self,
        user_id: UUID,
        current_user: User
    ) -> bool:
        """Soft delete a user"""
        try:
            # Get the user to delete
            user = await self.get_user(user_id)
            if not user:
                return False
            
            # Check permissions
            if not self._can_delete_user(current_user, user):
                raise PermissionError("Insufficient permissions to delete this user")
            
            # Soft delete by setting is_active to False
            query = (
                update(User)
                .where(User.id == user_id)
                .values(is_active=False)
            )
            
            await self.db.execute(query)
            await self.db.commit()
            
            logger.info(f"Deleted user {user_id}")
            return True
            
        except Exception as e:
            await self.db.rollback()
            logger.error(f"Error deleting user {user_id}: {e}")
            raise
    
    async def search_users(
        self,
        query: str,
        current_user: User,
        limit: int = 10
    ) -> List[User]:
        """Search users by name, email, or username"""
        try:
            # Only allow HR and admin users to search
            if current_user.role not in [UserRole.HR, UserRole.ADMIN]:
                raise PermissionError("Insufficient permissions to search users")
            
            search_query = (
                select(User)
                .where(
                    User.is_active == True,
                    (
                        User.full_name.ilike(f"%{query}%") |
                        User.email.ilike(f"%{query}%") |
                        User.username.ilike(f"%{query}%")
                    )
                )
                .limit(limit)
            )
            
            result = await self.db.execute(search_query)
            return result.scalars().all()
            
        except Exception as e:
            logger.error(f"Error searching users: {e}")
            raise
    
    async def _update_last_login(self, user_id: UUID) -> None:
        """Update user's last login timestamp"""
        try:
            from sqlalchemy import func
            query = (
                update(User)
                .where(User.id == user_id)
                .values(last_login=func.now())
            )
            await self.db.execute(query)
            await self.db.commit()
            
        except Exception as e:
            logger.error(f"Error updating last login for user {user_id}: {e}")

    async def _set_user_roles(self, user_id: UUID, role_ids):
        try:
            # Clear existing mappings
            await self.db.execute(
                delete(UserRoleMap).where(UserRoleMap.user_id == user_id)
            )
            # Insert new mappings
            for rid in role_ids:
                self.db.add(UserRoleMap(user_id=user_id, role_id=rid))
        except Exception as e:
            logger.error(f"Error setting user roles for {user_id}: {e}")
            raise

    async def get_user_roles(self, user_id: UUID):
        try:
            stmt = select(Role).join(UserRoleMap, Role.id == UserRoleMap.role_id).where(UserRoleMap.user_id == user_id)
            result = await self.db.execute(stmt)
            return [row[0] for row in result.all()]
        except Exception as e:
            logger.error(f"Error getting roles for user {user_id}: {e}")
            raise
    
    def _can_update_user(self, current_user: User, target_user: User) -> bool:
        """Check if current user can update target user"""
        # Users can update themselves
        if current_user.id == target_user.id:
            return True
        
        # Admins can update anyone
        if current_user.role == UserRole.ADMIN:
            return True
        
        # HR can update employees
        if current_user.role == UserRole.HR and target_user.role == UserRole.EMPLOYEE:
            return True
        
        return False
    
    def _can_delete_user(self, current_user: User, target_user: User) -> bool:
        """Check if current user can delete target user"""
        # Only admins can delete users
        if current_user.role == UserRole.ADMIN:
            return True
        
        return False
