"""
Script to seed the PostgreSQL database with interview questions.

Run with:
  python scripts/seed_questions.py
"""

import asyncio
import json
import logging
import os
import sys

from sqlalchemy.future import select

# Ensure the backend directory is in the path to import app modules
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import app.db.postgres as pg
from app.models.question import Question

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def seed():
    """Seed questions from JSON to PostgreSQL."""
    # 1. Initialize DB
    await pg.init_db()
    if pg._session_factory is None:
        logger.error("Failed to initialize database connection. Cannot seed.")
        return

    # 2. Read JSON
    seed_file = os.path.join(os.path.dirname(__file__), "..", "data", "questions", "seed_questions.json")
    if not os.path.exists(seed_file):
        logger.error(f"Seed file not found at {seed_file}")
        return

    with open(seed_file, "r") as f:
        questions_data = json.load(f)

    logger.info(f"Loaded {len(questions_data)} questions from JSON.")

    # 3. Insert avoiding duplicates
    inserted_count = 0
    duplicate_count = 0

    async with pg._session_factory() as session:
        for q_data in questions_data:
            # Check if exists by title
            stmt = select(Question).where(Question.title == q_data["title"])
            result = await session.execute(stmt)
            existing = result.scalar_one_or_none()
            
            if existing:
                duplicate_count += 1
                continue
                
            # Create new question
            new_q = Question(
                title=q_data["title"],
                question=q_data["question"],
                topic=q_data["topic"],
                difficulty=q_data["difficulty"],
                concepts=q_data["concepts"],
                tags=q_data["tags"],
                expected_answer=q_data["expected_answer"],
                sample_code=q_data["sample_code"],
                language=q_data["language"],
                hints=q_data["hints"]
            )
            session.add(new_q)
            inserted_count += 1

        await session.commit()

    logger.info(f"Seeding complete! Inserted: {inserted_count}, Skipped (Duplicates): {duplicate_count}")

    # 4. Close DB
    await pg.close_db()


if __name__ == "__main__":
    asyncio.run(seed())
