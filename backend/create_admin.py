#!/usr/bin/env python3
"""
创建默认管理员用户脚本
"""
import sys
import os

# 添加当前目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.database import SessionLocal, engine, Base
from app.models.user import User, UserRole
from app.utils.auth import get_password_hash

def create_admin_user():
    """创建默认管理员用户"""
    print("🔧 正在创建默认管理员用户...")
    
    # 确保数据库表存在
    Base.metadata.create_all(bind=engine)
    
    db = SessionLocal()
    try:
        # 检查是否已存在管理员用户
        admin_user = db.query(User).filter(User.username == 'admin').first()
        if admin_user:
            print("ℹ️  管理员用户已存在")
            print(f"   用户名: {admin_user.username}")
            print(f"   邮箱: {admin_user.email}")
            print(f"   角色: {admin_user.role.value}")
            print(f"   激活状态: {admin_user.is_active}")
            return
        
        # 创建新的管理员用户
        admin_user = User(
            username='admin',
            email='admin@example.com',
            full_name='系统管理员',
            role=UserRole.ADMIN,
            hashed_password=get_password_hash('admin123'),
            is_active=True
        )
        
        db.add(admin_user)
        db.commit()
        db.refresh(admin_user)
        
        print("✅ 默认管理员用户创建成功！")
        print(f"   用户名: {admin_user.username}")
        print(f"   密码: admin123")
        print(f"   邮箱: {admin_user.email}")
        print(f"   角色: {admin_user.role.value}")
        
    except Exception as e:
        print(f"❌ 创建管理员用户失败: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    create_admin_user()
