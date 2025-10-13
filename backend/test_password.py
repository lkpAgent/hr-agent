import asyncio
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import get_db
from app.models.user import User
from sqlalchemy import select
from passlib.context import CryptContext

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

async def test_password():
    """测试密码验证"""
    print("=== 测试密码验证 ===")
    
    async for session in get_db():
        # 查找用户
        result = await session.execute(
            select(User).where(User.username == "testuser")
        )
        user = result.scalar_one_or_none()
        
        if user:
            print(f"用户: {user.username}")
            print(f"存储的哈希密码: {user.hashed_password}")
            
            # 测试不同密码
            passwords = ["testpass123", "password", "123456", "admin"]
            
            for pwd in passwords:
                is_valid = pwd_context.verify(pwd, user.hashed_password)
                print(f"密码 '{pwd}': {'✅ 正确' if is_valid else '❌ 错误'}")
        else:
            print("❌ 用户不存在")

if __name__ == "__main__":
    asyncio.run(test_password())