"""
添加测试图集数据
"""
import asyncio
import sys
sys.path.insert(0, '.')

from sqlalchemy import select
from app.core.database import AsyncSessionLocal
from app.models.community import GalleryCategory, Gallery

async def add_test_data():
    async with AsyncSessionLocal() as db:
        # 检查是否已有分类
        result = await db.execute(select(GalleryCategory))
        categories = result.scalars().all()
        
        if not categories:
            # 添加分类
            cats = [
                GalleryCategory(name="美女写真", sort_order=1),
                GalleryCategory(name="性感诱惑", sort_order=2),
                GalleryCategory(name="清纯可爱", sort_order=3),
            ]
            for cat in cats:
                db.add(cat)
            await db.commit()
            print("已添加图集分类")
            
            # 重新获取分类
            result = await db.execute(select(GalleryCategory))
            categories = result.scalars().all()
        
        # 检查是否已有图集
        result = await db.execute(select(Gallery))
        galleries = result.scalars().all()
        
        if not galleries:
            # 添加测试图集
            test_images = [
                "https://picsum.photos/400/600?random=1",
                "https://picsum.photos/400/600?random=2",
                "https://picsum.photos/400/600?random=3",
                "https://picsum.photos/400/600?random=4",
                "https://picsum.photos/400/600?random=5",
                "https://picsum.photos/400/600?random=6",
                "https://picsum.photos/400/600?random=7",
                "https://picsum.photos/400/600?random=8",
                "https://picsum.photos/400/600?random=9",
                "https://picsum.photos/400/600?random=10",
            ]
            
            gallery = Gallery(
                category_id=categories[0].id if categories else None,
                title="濑亚美莉",
                cover="https://picsum.photos/400/600?random=1",
                images=test_images,
                description="测试图集描述",
                image_count=len(test_images),
                view_count=1100,
                like_count=11000,
                status="completed"
            )
            db.add(gallery)
            
            # 添加更多测试图集
            for i in range(2, 6):
                g = Gallery(
                    category_id=categories[i % len(categories)].id if categories else None,
                    title=f"测试图集{i}",
                    cover=f"https://picsum.photos/400/600?random={i*10}",
                    images=[f"https://picsum.photos/400/600?random={i*10+j}" for j in range(1, 20)],
                    description=f"测试图集{i}描述",
                    image_count=19,
                    view_count=100 * i,
                    like_count=50 * i,
                    status="ongoing" if i % 2 == 0 else "completed"
                )
                db.add(g)
            
            await db.commit()
            print("已添加测试图集数据")
        else:
            print(f"已有 {len(galleries)} 个图集")
            for g in galleries:
                print(f"  - {g.id}: {g.title}, 图片数: {len(g.images) if g.images else 0}")

if __name__ == "__main__":
    asyncio.run(add_test_data())
