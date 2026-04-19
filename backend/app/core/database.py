from neo4j import AsyncGraphDatabase
from app.core.config import settings

_driver = None


async def get_driver():
    global _driver
    if _driver is None:
        _driver = AsyncGraphDatabase.driver(
            settings.NEO4J_URI,
            auth=(settings.NEO4J_USER, settings.NEO4J_PASSWORD),
        )
    return _driver


async def init_db():
    driver = await get_driver()
    async with driver.session() as session:
        # Indexes
        await session.run("CREATE INDEX user_samaccountname IF NOT EXISTS FOR (u:User) ON (u.samAccountName)")
        await session.run("CREATE INDEX computer_name IF NOT EXISTS FOR (c:Computer) ON (c.name)")
        await session.run("CREATE INDEX group_name IF NOT EXISTS FOR (g:Group) ON (g.name)")
        await session.run("CREATE INDEX ou_dn IF NOT EXISTS FOR (o:OU) ON (o.distinguishedName)")


async def get_session():
    driver = await get_driver()
    async with driver.session() as session:
        yield session
