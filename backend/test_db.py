import os
import sys
sys.path.append('.')

# 设置环境变量
os.environ['DATABASE_URL'] = 'postgresql://user:password@localhost:5432/datalabels'

try:
    from app.database import engine, Base
    from app.models import *
    
    print("✅ 数据库连接成功")
    
    # 创建表
    Base.metadata.create_all(bind=engine)
    print("✅ 数据库表创建成功")
    
    # 测试插入数据
    from app.database import SessionLocal
    from app.models.user import User, UserRole
    from app.utils.auth import get_password_hash
    
    db = SessionLocal()
    try:
        # 检查是否已存在管理员用户
        admin_user = db.query(User).filter(User.username == 'admin').first()
        if not admin_user:
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
            print("✅ 默认管理员用户创建成功")
        else:
            print("ℹ️  管理员用户已存在")
    finally:
        db.close()
        
    print("✅ 数据库测试完成")
    
except Exception as e:
    print(f"❌ 数据库测试失败: {e}")
    sys.exit(1)
