import asyncio
import logging
from maim_db.maimconfig_models.connection import get_db, init_database
from maim_db.maimconfig_models.models import User
from sqlalchemy import select

logging.basicConfig(level=logging.INFO)

async def main():
    print("Testing DB connection...")
    try:
        await init_database()
        print("Init success.")
    except Exception as e:
        print(f"Init failed: {e}")
        return

    print("Testing Session...")
    async for session in get_db():
        try:
            print("Session acquired.")
            result = await session.execute(select(1))
            print(f"Select 1 result: {result.scalar()}")
            
            # Check User table
            try:
                result = await session.execute(select(User).limit(1))
                print("Select User table: Success (table exists)")
            except Exception as e:
                print(f"Select User table failed: {e}")
                
        except Exception as e:
            print(f"Session usage failed: {e}")
        finally:
            print("Session closed.")
        break # get_db is generator

if __name__ == "__main__":
    asyncio.run(main())
