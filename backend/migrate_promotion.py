"""
推广系统数据库迁移脚本
创建 user_profiles, invitations, commissions, withdrawals, rewards, agent_relations, invite_milestones, promotion_configs 表
"""
import asyncio
from sqlalchemy import text
from app.core.database import engine

async def migrate():
    async with engine.begin() as conn:
        # 创建 user_profiles 表
        await conn.execute(text("""
            CREATE TABLE IF NOT EXISTS user_profiles (
                id SERIAL PRIMARY KEY,
                user_id INTEGER UNIQUE NOT NULL REFERENCES users(id) ON DELETE CASCADE,
                invite_code VARCHAR(20) UNIQUE NOT NULL,
                inviter_id INTEGER REFERENCES users(id) ON DELETE SET NULL,
                agent_level INTEGER DEFAULT 0,
                commission_rate DECIMAL(5,4) DEFAULT 0,
                agent_status VARCHAR(20) DEFAULT 'inactive',
                agent_applied_at TIMESTAMP,
                agent_approved_at TIMESTAMP,
                total_invites INTEGER DEFAULT 0,
                valid_invites INTEGER DEFAULT 0,
                total_team_size INTEGER DEFAULT 0,
                total_commission DECIMAL(12,2) DEFAULT 0,
                available_balance DECIMAL(12,2) DEFAULT 0,
                frozen_balance DECIMAL(12,2) DEFAULT 0,
                total_withdrawn DECIMAL(12,2) DEFAULT 0,
                total_reward_days INTEGER DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """))
        
        # 创建 invitations 表
        await conn.execute(text("""
            CREATE TABLE IF NOT EXISTS invitations (
                id SERIAL PRIMARY KEY,
                inviter_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
                invitee_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
                invite_code VARCHAR(20) NOT NULL,
                device_fingerprint VARCHAR(255),
                ip_address VARCHAR(50),
                user_agent TEXT,
                is_valid BOOLEAN DEFAULT FALSE,
                invalid_reason VARCHAR(100),
                register_rewarded BOOLEAN DEFAULT FALSE,
                recharge_rewarded BOOLEAN DEFAULT FALSE,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                validated_at TIMESTAMP
            )
        """))
        
        # 创建 commissions 表
        await conn.execute(text("""
            CREATE TABLE IF NOT EXISTS commissions (
                id SERIAL PRIMARY KEY,
                agent_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
                from_user_id INTEGER REFERENCES users(id) ON DELETE SET NULL,
                order_id INTEGER,
                order_amount DECIMAL(12,2) NOT NULL,
                commission_type VARCHAR(20) NOT NULL,
                commission_rate DECIMAL(5,4) NOT NULL,
                commission_amount DECIMAL(12,2) NOT NULL,
                level_diff INTEGER DEFAULT 1,
                status VARCHAR(20) DEFAULT 'pending',
                settled_at TIMESTAMP,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """))
        
        # 创建 withdrawals 表
        await conn.execute(text("""
            CREATE TABLE IF NOT EXISTS withdrawals (
                id SERIAL PRIMARY KEY,
                user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
                amount DECIMAL(12,2) NOT NULL,
                fee DECIMAL(12,2) DEFAULT 0,
                actual_amount DECIMAL(12,2) NOT NULL,
                withdraw_type VARCHAR(20) NOT NULL,
                account_name VARCHAR(50),
                account_number VARCHAR(100),
                bank_name VARCHAR(50),
                status VARCHAR(20) DEFAULT 'pending',
                reject_reason VARCHAR(255),
                operator_id INTEGER REFERENCES users(id) ON DELETE SET NULL,
                processed_at TIMESTAMP,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """))
        
        # 创建 rewards 表
        await conn.execute(text("""
            CREATE TABLE IF NOT EXISTS rewards (
                id SERIAL PRIMARY KEY,
                user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
                reward_type VARCHAR(30) NOT NULL,
                reward_content VARCHAR(20) NOT NULL,
                reward_value DECIMAL(12,2) NOT NULL,
                reward_desc VARCHAR(255),
                source_type VARCHAR(30),
                source_id INTEGER,
                claimed BOOLEAN DEFAULT FALSE,
                claimed_at TIMESTAMP,
                expire_at TIMESTAMP,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """))
        
        # 创建 agent_relations 表
        await conn.execute(text("""
            CREATE TABLE IF NOT EXISTS agent_relations (
                id SERIAL PRIMARY KEY,
                ancestor_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
                descendant_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
                level_depth INTEGER NOT NULL,
                path VARCHAR(500),
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """))
        
        # 创建 invite_milestones 表
        await conn.execute(text("""
            CREATE TABLE IF NOT EXISTS invite_milestones (
                id SERIAL PRIMARY KEY,
                invite_count INTEGER UNIQUE NOT NULL,
                reward_type VARCHAR(20) NOT NULL,
                reward_value DECIMAL(12,2) NOT NULL,
                reward_desc VARCHAR(255),
                is_active BOOLEAN DEFAULT TRUE,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """))
        
        # 创建 promotion_configs 表
        await conn.execute(text("""
            CREATE TABLE IF NOT EXISTS promotion_configs (
                id SERIAL PRIMARY KEY,
                config_key VARCHAR(50) UNIQUE NOT NULL,
                config_value TEXT NOT NULL,
                config_desc VARCHAR(255),
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """))
        
        # 创建索引
        await conn.execute(text("CREATE INDEX IF NOT EXISTS idx_user_profile_inviter ON user_profiles(inviter_id)"))
        await conn.execute(text("CREATE INDEX IF NOT EXISTS idx_user_profile_agent_level ON user_profiles(agent_level)"))
        await conn.execute(text("CREATE INDEX IF NOT EXISTS idx_invitation_inviter ON invitations(inviter_id)"))
        await conn.execute(text("CREATE INDEX IF NOT EXISTS idx_invitation_invitee ON invitations(invitee_id)"))
        await conn.execute(text("CREATE INDEX IF NOT EXISTS idx_invitation_code ON invitations(invite_code)"))
        await conn.execute(text("CREATE INDEX IF NOT EXISTS idx_commission_agent ON commissions(agent_id)"))
        await conn.execute(text("CREATE INDEX IF NOT EXISTS idx_commission_status ON commissions(status)"))
        await conn.execute(text("CREATE INDEX IF NOT EXISTS idx_withdrawal_user ON withdrawals(user_id)"))
        await conn.execute(text("CREATE INDEX IF NOT EXISTS idx_withdrawal_status ON withdrawals(status)"))
        await conn.execute(text("CREATE INDEX IF NOT EXISTS idx_reward_user ON rewards(user_id)"))
        await conn.execute(text("CREATE INDEX IF NOT EXISTS idx_reward_claimed ON rewards(claimed)"))
        
        # 插入默认里程碑配置
        await conn.execute(text("""
            INSERT INTO invite_milestones (invite_count, reward_type, reward_value, reward_desc)
            VALUES 
                (5, 'vip_days', 3, '邀请5人，奖励3天VIP'),
                (10, 'vip_days', 7, '邀请10人，奖励7天VIP'),
                (20, 'vip_days', 15, '邀请20人，奖励15天VIP'),
                (50, 'vip_days', 30, '邀请50人，奖励30天VIP'),
                (100, 'vip_days', 90, '邀请100人，奖励90天VIP')
            ON CONFLICT (invite_count) DO NOTHING
        """))
        
        print("Migration completed successfully!")

if __name__ == "__main__":
    asyncio.run(migrate())


创建 user_profiles, invitations, commissions, withdrawals, rewards, agent_relations, invite_milestones, promotion_configs 表
"""
import asyncio
from sqlalchemy import text
from app.core.database import engine

async def migrate():
    async with engine.begin() as conn:
        # 创建 user_profiles 表
        await conn.execute(text("""
            CREATE TABLE IF NOT EXISTS user_profiles (
                id SERIAL PRIMARY KEY,
                user_id INTEGER UNIQUE NOT NULL REFERENCES users(id) ON DELETE CASCADE,
                invite_code VARCHAR(20) UNIQUE NOT NULL,
                inviter_id INTEGER REFERENCES users(id) ON DELETE SET NULL,
                agent_level INTEGER DEFAULT 0,
                commission_rate DECIMAL(5,4) DEFAULT 0,
                agent_status VARCHAR(20) DEFAULT 'inactive',
                agent_applied_at TIMESTAMP,
                agent_approved_at TIMESTAMP,
                total_invites INTEGER DEFAULT 0,
                valid_invites INTEGER DEFAULT 0,
                total_team_size INTEGER DEFAULT 0,
                total_commission DECIMAL(12,2) DEFAULT 0,
                available_balance DECIMAL(12,2) DEFAULT 0,
                frozen_balance DECIMAL(12,2) DEFAULT 0,
                total_withdrawn DECIMAL(12,2) DEFAULT 0,
                total_reward_days INTEGER DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """))
        
        # 创建 invitations 表
        await conn.execute(text("""
            CREATE TABLE IF NOT EXISTS invitations (
                id SERIAL PRIMARY KEY,
                inviter_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
                invitee_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
                invite_code VARCHAR(20) NOT NULL,
                device_fingerprint VARCHAR(255),
                ip_address VARCHAR(50),
                user_agent TEXT,
                is_valid BOOLEAN DEFAULT FALSE,
                invalid_reason VARCHAR(100),
                register_rewarded BOOLEAN DEFAULT FALSE,
                recharge_rewarded BOOLEAN DEFAULT FALSE,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                validated_at TIMESTAMP
            )
        """))
        
        # 创建 commissions 表
        await conn.execute(text("""
            CREATE TABLE IF NOT EXISTS commissions (
                id SERIAL PRIMARY KEY,
                agent_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
                from_user_id INTEGER REFERENCES users(id) ON DELETE SET NULL,
                order_id INTEGER,
                order_amount DECIMAL(12,2) NOT NULL,
                commission_type VARCHAR(20) NOT NULL,
                commission_rate DECIMAL(5,4) NOT NULL,
                commission_amount DECIMAL(12,2) NOT NULL,
                level_diff INTEGER DEFAULT 1,
                status VARCHAR(20) DEFAULT 'pending',
                settled_at TIMESTAMP,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """))
        
        # 创建 withdrawals 表
        await conn.execute(text("""
            CREATE TABLE IF NOT EXISTS withdrawals (
                id SERIAL PRIMARY KEY,
                user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
                amount DECIMAL(12,2) NOT NULL,
                fee DECIMAL(12,2) DEFAULT 0,
                actual_amount DECIMAL(12,2) NOT NULL,
                withdraw_type VARCHAR(20) NOT NULL,
                account_name VARCHAR(50),
                account_number VARCHAR(100),
                bank_name VARCHAR(50),
                status VARCHAR(20) DEFAULT 'pending',
                reject_reason VARCHAR(255),
                operator_id INTEGER REFERENCES users(id) ON DELETE SET NULL,
                processed_at TIMESTAMP,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """))
        
        # 创建 rewards 表
        await conn.execute(text("""
            CREATE TABLE IF NOT EXISTS rewards (
                id SERIAL PRIMARY KEY,
                user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
                reward_type VARCHAR(30) NOT NULL,
                reward_content VARCHAR(20) NOT NULL,
                reward_value DECIMAL(12,2) NOT NULL,
                reward_desc VARCHAR(255),
                source_type VARCHAR(30),
                source_id INTEGER,
                claimed BOOLEAN DEFAULT FALSE,
                claimed_at TIMESTAMP,
                expire_at TIMESTAMP,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """))
        
        # 创建 agent_relations 表
        await conn.execute(text("""
            CREATE TABLE IF NOT EXISTS agent_relations (
                id SERIAL PRIMARY KEY,
                ancestor_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
                descendant_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
                level_depth INTEGER NOT NULL,
                path VARCHAR(500),
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """))
        
        # 创建 invite_milestones 表
        await conn.execute(text("""
            CREATE TABLE IF NOT EXISTS invite_milestones (
                id SERIAL PRIMARY KEY,
                invite_count INTEGER UNIQUE NOT NULL,
                reward_type VARCHAR(20) NOT NULL,
                reward_value DECIMAL(12,2) NOT NULL,
                reward_desc VARCHAR(255),
                is_active BOOLEAN DEFAULT TRUE,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """))
        
        # 创建 promotion_configs 表
        await conn.execute(text("""
            CREATE TABLE IF NOT EXISTS promotion_configs (
                id SERIAL PRIMARY KEY,
                config_key VARCHAR(50) UNIQUE NOT NULL,
                config_value TEXT NOT NULL,
                config_desc VARCHAR(255),
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """))
        
        # 创建索引
        await conn.execute(text("CREATE INDEX IF NOT EXISTS idx_user_profile_inviter ON user_profiles(inviter_id)"))
        await conn.execute(text("CREATE INDEX IF NOT EXISTS idx_user_profile_agent_level ON user_profiles(agent_level)"))
        await conn.execute(text("CREATE INDEX IF NOT EXISTS idx_invitation_inviter ON invitations(inviter_id)"))
        await conn.execute(text("CREATE INDEX IF NOT EXISTS idx_invitation_invitee ON invitations(invitee_id)"))
        await conn.execute(text("CREATE INDEX IF NOT EXISTS idx_invitation_code ON invitations(invite_code)"))
        await conn.execute(text("CREATE INDEX IF NOT EXISTS idx_commission_agent ON commissions(agent_id)"))
        await conn.execute(text("CREATE INDEX IF NOT EXISTS idx_commission_status ON commissions(status)"))
        await conn.execute(text("CREATE INDEX IF NOT EXISTS idx_withdrawal_user ON withdrawals(user_id)"))
        await conn.execute(text("CREATE INDEX IF NOT EXISTS idx_withdrawal_status ON withdrawals(status)"))
        await conn.execute(text("CREATE INDEX IF NOT EXISTS idx_reward_user ON rewards(user_id)"))
        await conn.execute(text("CREATE INDEX IF NOT EXISTS idx_reward_claimed ON rewards(claimed)"))
        
        # 插入默认里程碑配置
        await conn.execute(text("""
            INSERT INTO invite_milestones (invite_count, reward_type, reward_value, reward_desc)
            VALUES 
                (5, 'vip_days', 3, '邀请5人，奖励3天VIP'),
                (10, 'vip_days', 7, '邀请10人，奖励7天VIP'),
                (20, 'vip_days', 15, '邀请20人，奖励15天VIP'),
                (50, 'vip_days', 30, '邀请50人，奖励30天VIP'),
                (100, 'vip_days', 90, '邀请100人，奖励90天VIP')
            ON CONFLICT (invite_count) DO NOTHING
        """))
        
        print("Migration completed successfully!")

if __name__ == "__main__":
    asyncio.run(migrate())

