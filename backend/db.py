import json
import os
import uuid
from datetime import datetime, timezone

import asyncpg

_pool: asyncpg.Pool | None = None


async def get_pool() -> asyncpg.Pool:
    global _pool
    if _pool is None:
        database_url = os.getenv("DATABASE_URL")
        if not database_url:
            raise RuntimeError(
                "DATABASE_URL environment variable is not set. "
                "Add it to your .env file and restart the server."
            )
        _pool = await asyncpg.create_pool(database_url, min_size=1, max_size=10)
    return _pool


async def close_pool() -> None:
    global _pool
    if _pool:
        await _pool.close()
        _pool = None


async def init_db() -> None:
    pool = await get_pool()
    async with pool.acquire() as conn:
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                email       TEXT UNIQUE NOT NULL,
                password_hash TEXT NOT NULL,
                created_at  TIMESTAMPTZ NOT NULL DEFAULT NOW()
            )
        """)
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS analyses (
                id                UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                user_id           UUID REFERENCES users(id) ON DELETE CASCADE,
                region            TEXT NOT NULL,
                resources_scanned INT NOT NULL DEFAULT 0,
                issues_found      INT NOT NULL DEFAULT 0,
                estimated_savings TEXT,
                analysis_result   JSONB,
                status            TEXT NOT NULL DEFAULT 'pending',
                created_at        TIMESTAMPTZ NOT NULL DEFAULT NOW()
            )
        """)


async def create_analysis(user_id: str | None, region: str) -> str:
    pool = await get_pool()
    async with pool.acquire() as conn:
        row = await conn.fetchrow(
            """
            INSERT INTO analyses (user_id, region, status)
            VALUES ($1, $2, 'running')
            RETURNING id
            """,
            uuid.UUID(user_id) if user_id else None,
            region,
        )
        return str(row["id"])


async def update_analysis(
    analysis_id: str,
    *,
    status: str,
    resources_scanned: int = 0,
    issues_found: int = 0,
    estimated_savings: str | None = None,
    analysis_result: dict | None = None,
) -> None:
    pool = await get_pool()
    async with pool.acquire() as conn:
        await conn.execute(
            """
            UPDATE analyses
            SET status            = $1,
                resources_scanned = $2,
                issues_found      = $3,
                estimated_savings = $4,
                analysis_result   = $5
            WHERE id = $6
            """,
            status,
            resources_scanned,
            issues_found,
            estimated_savings,
            json.dumps(analysis_result) if analysis_result else None,
            uuid.UUID(analysis_id),
        )


async def get_history(user_id: str | None, limit: int = 20) -> list[dict]:
    pool = await get_pool()
    async with pool.acquire() as conn:
        if user_id:
            rows = await conn.fetch(
                """
                SELECT id, user_id, region, resources_scanned, issues_found,
                       estimated_savings, analysis_result, status, created_at
                FROM analyses
                WHERE user_id = $1
                ORDER BY created_at DESC
                LIMIT $2
                """,
                uuid.UUID(user_id),
                limit,
            )
        else:
            rows = await conn.fetch(
                """
                SELECT id, user_id, region, resources_scanned, issues_found,
                       estimated_savings, analysis_result, status, created_at
                FROM analyses
                ORDER BY created_at DESC
                LIMIT $1
                """,
                limit,
            )

    results = []
    for row in rows:
        r = dict(row)
        r["id"] = str(r["id"])
        r["user_id"] = str(r["user_id"]) if r["user_id"] else None
        r["created_at"] = r["created_at"].isoformat()
        if isinstance(r["analysis_result"], str):
            r["analysis_result"] = json.loads(r["analysis_result"])
        results.append(r)
    return results
