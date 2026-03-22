'''
menymp 2026
For use with async IO environments
'''

import asyncio
import aiomysql
import logging

class AsyncDB:
    def __init__(self):
        self.pool = None

    async def connect(self, user, password, host, db, port=3306, minsize=1, maxsize=5, retries=5, delay=2):
        for attempt in range(1, retries+1):
            try:
                self.pool = await aiomysql.create_pool(
                    host=host, port=port, user=user, password=password, db=db,
                    minsize=minsize, maxsize=maxsize, autocommit=True
                )
                logging.info("aiomysql pool created on attempt %d", attempt)
                return
            except Exception as e:
                logging.warning("DB connect failed (%s), retrying in %ds...", e, delay)
                await asyncio.sleep(delay)
        raise RuntimeError("Could not connect to DB after retries")

    async def execute(self, query, args=None):
        async with self.pool.acquire() as conn:
            async with conn.cursor(aiomysql.DictCursor) as cur:
                await cur.execute(query, args)
                return await cur.fetchall()

    async def close(self):
        if self.pool:
            self.pool.close()
            await self.pool.wait_closed()