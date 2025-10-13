import asyncio
from app.core.database import get_db
from app.models.user import User
from sqlalchemy import select
from passlib.context import CryptContext
from uuid import uuid4

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

async def create_test_user():
    """创建新的测试用户"""
    print("=== 创建新的测试用户 ===")
    
    async for session in get_db():
        try:
            # 创建新用户 testuser2
            hashed_password = pwd_context.hash("testpass123")
            
            new_user = User(
                id=uuid4(),
                username="testuser2",
                email="test2@example.com",
                full_name="Test User 2",
                hashed_password=hashed_password,
                role="admin",
                is_superuser=True,
                is_verified=True,
                is_active=True
            )
            
            session.add(new_user)
            await session.commit()
            
            print(f"✅ 用户创建成功: {new_user.username}")
            print(f"密码: testpass123")
            print(f"哈希: {hashed_password}")
            
            # 验证密码
            is_valid = pwd_context.verify("testpass123", hashed_password)
            print(f"密码验证: {'✅ 正确' if is_valid else '❌ 错误'}")
            
        except Exception as e:
            await session.rollback()
            print(f"❌ 创建用户失败: {e}")

if __name__ == "__main__":
    asyncio.run(create_test_user())