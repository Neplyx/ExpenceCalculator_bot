from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker
from src.database.models import Base
from src.config import Config

engine = create_async_engine(
    Config.DB_URL, 
    echo=True,
    connect_args={
        "server_settings": {
            "client_encoding": "UTF8"
        }
    }
)
async_session = async_sessionmaker(engine, expire_on_commit=False)

async def init_db():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)