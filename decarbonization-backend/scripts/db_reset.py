import asyncio
import os
import sys
from sqlalchemy import text

# Add current directory to path
sys.path.append(os.getcwd())

from app.database import engine, drop_all_tables, init_db

async def reset_db():
    print("⚠️  WARNING: This will wipe all data in the database!")
    print("Starting database reset...")
    
    try:
        # Drop everything
        await drop_all_tables()
        print("✅ All tables dropped successfully.")
        
        # Create everything
        await init_db()
        print("✅ Database re-initialized with new schema.")
        
    except Exception as e:
        print(f"❌ Error during database reset: {str(e)}")
        # Fallback manual drop if drop_all_tables fails due to schema mismatch
        print("Attempting manual drop...")
        async with engine.begin() as conn:
            await conn.execute(text("DROP SCHEMA public CASCADE"))
            await conn.execute(text("CREATE SCHEMA public"))
            await conn.execute(text("GRANT ALL ON SCHEMA public TO public"))
            await conn.execute(text("CREATE EXTENSION IF NOT EXISTS postgis"))
        await init_db()
        print("✅ Database re-initialized via manual fallback.")

if __name__ == "__main__":
    asyncio.run(reset_db())
