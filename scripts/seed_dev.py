#!/usr/bin/env python3
"""Seed script: creates admin user and sample data for development."""
import asyncio
import sys, os
sys.path.insert(0, "/app")

from app.core.database import AsyncSessionLocal
from app.services.auth_service import create_user
from app.schemas.auth import UserCreateRequest


async def main():
    async with AsyncSessionLocal() as db:
        try:
            admin = await create_user(db, UserCreateRequest(
                email="admin@sigtpi.local",
                password="Admin1234!@",
                full_name="Administrador SIGTPI",
            ))
            admin.is_superuser = True
            await db.commit()
            print(f"✓ Admin created: admin@sigtpi.local / Admin1234!@")
        except Exception as e:
            print(f"  (admin may already exist: {e})")
            await db.rollback()


if __name__ == "__main__":
    asyncio.run(main())
