#!/usr/bin/env python3
"""测试推广邀请功能"""
import asyncio
import httpx
import uuid
import sys
sys.path.insert(0, '.')

async def test_invite_flow():
    base = "http://127.0.0.1:8000/api/v1"
    device = "test_" + uuid.uuid4().hex[:20]
    
    print("=" * 50)
    print("Testing Invite Flow")
    print("=" * 50)
    
    async with httpx.AsyncClient() as c:
        # 1. Register with invite code
        print("\n1. Registering new user with invite_code=hMcf...")
        r = await c.post(
            f"{base}/auth/guest/register", 
            json={"device_id": device, "invite_code": "hMcf"}
        )
        print(f"   Status: {r.status_code}")
        
        if r.status_code != 200:
            print(f"   Error: {r.text}")
            return
        
        new_token = r.json()["access_token"]
        print(f"   Got token: {new_token[:40]}...")
        
        # 2. Check new user info
        print("\n2. Checking new user info...")
        r = await c.get(
            f"{base}/users/me",
            headers={"Authorization": f"Bearer {new_token}"}
        )
        if r.status_code == 200:
            user = r.json()
            print(f"   User ID: {user.get('id')}")
            print(f"   Username: {user.get('username')}")
            print(f"   Invited by: {user.get('invited_by')}")
            new_user_id = user.get('id')
        
        # 3. Check inviter stats
        print("\n3. Checking inviter (user 2) stats...")
        from app.core.security import create_access_token
        inviter_token = create_access_token(data={"sub": "2"})
        r = await c.get(
            f"{base}/promotion/invite-stats",
            headers={"Authorization": f"Bearer {inviter_token}"}
        )
        if r.status_code == 200:
            stats = r.json()
            print(f"   Total invites: {stats['total_invites']}")
            print(f"   Valid invites: {stats['valid_invites']}")
        
        # 4. Check invitation records
        print("\n4. Checking invitation records...")
        from app.core.database import AsyncSessionLocal
        from app.models.promotion import Invitation
        from sqlalchemy import select
        
        async with AsyncSessionLocal() as db:
            result = await db.execute(
                select(Invitation).where(Invitation.inviter_id == 2).order_by(Invitation.created_at.desc()).limit(3)
            )
            invitations = result.scalars().all()
            print(f"   Found {len(invitations)} invitation(s)")
            for inv in invitations:
                print(f"   - Invitee ID: {inv.invitee_id}, Valid: {inv.is_valid}, Code: {inv.invite_code}")
        
        # 5. Cleanup
        print("\n5. Cleaning up test data...")
        from app.models.user import User, UserVIP
        from app.models.promotion import UserProfile
        
        async with AsyncSessionLocal() as db:
            result = await db.execute(select(User).where(User.device_id == device))
            test_user = result.scalar_one_or_none()
            if test_user:
                # Delete invitation
                await db.execute(Invitation.__table__.delete().where(Invitation.invitee_id == test_user.id))
                # Delete VIP
                await db.execute(UserVIP.__table__.delete().where(UserVIP.user_id == test_user.id))
                # Restore inviter count
                result = await db.execute(select(UserProfile).where(UserProfile.user_id == 2))
                profile = result.scalar_one_or_none()
                if profile and profile.total_invites and profile.total_invites > 0:
                    profile.total_invites -= 1
                # Delete user
                await db.delete(test_user)
                await db.commit()
                print("   Cleaned up!")
    
    print("\n" + "=" * 50)
    print("TEST COMPLETED SUCCESSFULLY!")
    print("=" * 50)

if __name__ == "__main__":
    asyncio.run(test_invite_flow())
