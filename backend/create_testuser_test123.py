import asyncio
from app.core.database import get_db
from app.models.user import User
from sqlalchemy import select, delete
from passlib.context import CryptContext
from uuid import uuid4

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

async def create_test_user():
    """创建testuser/test123用户"""
    print("=== 创建testuser/test123用户 ===")
    
    async for session in get_db():
        try:
            # 先删除现有的testuser用户（如果存在）
            result = await session.execute(
                delete(User).where(User.username == "testuser")
            )
            if result.rowcount > 0:
                print(f"删除了现有的testuser用户")
            
            # 创建新用户 testuser
            hashed_password = pwd_context.hash("test123")
            
            new_user = User(
                id=uuid4(),
                username="testuser",
                email="test@example.com",
                full_name="Test User",
                hashed_password=hashed_password,
                role="admin",
                is_superuser=True,
                is_verified=True,
                is_active=True
            )
            
            session.add(new_user)
            await session.commit()
            
            print(f"✅ 用户创建成功: {new_user.username}")
            print(f"密码: test123")
            print(f"哈希: {hashed_password}")
            
            # 验证密码
            is_valid = pwd_context.verify("test123", hashed_password)
            print(f"密码验证: {'✅ 正确' if is_valid else '❌ 错误'}")
            
        except Exception as e:
            await session.rollback()
            print(f"❌ 创建用户失败: {e}")

if __name__ == "__main__":
    asyncio.run(create_test_user())