import asyncio
import os
from sqlalchemy import text
from app.database import async_session, engine

async def init_db():
    print("Starting database initialization...")
    schema_path = os.path.join(os.path.dirname(__file__), "../../schema.sql")
    
    if not os.path.exists(schema_path):
        print(f"Error: schema.sql not found at {schema_path}")
        return

    with open(schema_path, "r") as f:
        schema_sql = f.read()

    async with engine.begin() as conn:
        # Split by semicolon to execute one by one (simplified)
        # Note: This might be brittle if there are semicolons inside strings/functions
        # But for standard schema.sql it should work
        for statement in schema_sql.split(";"):
            statement = statement.strip()
            if statement:
                try:
                    await conn.execute(text(statement))
                except Exception as e:
                    print(f"Warning/Error executing statement: {e}")
    
    print("Database initialization complete.")

if __name__ == "__main__":
    asyncio.run(init_db())
