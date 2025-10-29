"""Utility script to align the database schema with the current ORM models."""

import asyncio
from sqlalchemy import text

from app.core.database import AsyncSessionLocal


async def column_exists(session, table: str, column: str) -> bool:
    """Check if a column exists on a table."""

    result = await session.execute(
        text(
            """
            SELECT 1
            FROM information_schema.columns
            WHERE table_name = :table
              AND column_name = :column
            LIMIT 1
            """
        ),
        {"table": table, "column": column},
    )
    return result.scalar() is not None


async def create_index(session, name: str, table: str, columns: str) -> None:
    """Create an index if it does not already exist."""

    await session.execute(
        text(
            f"""
            CREATE INDEX IF NOT EXISTS {name}
            ON {table}({columns})
            """
        )
    )


async def fix_database_issues() -> None:
    """Ensure required columns and indexes exist for the current ORM schema."""

    print("=" * 80)
    print("DATABASE ISSUE FIXER")
    print("=" * 80)
    print()

    async with AsyncSessionLocal() as session:
        fixes_applied: list[str] = []

        # ------------------------------------------------------------------
        # Users table adjustments
        # ------------------------------------------------------------------
        print("Checking users table...")

        if not await column_exists(session, "users", "gemini_api_key"):
            print("❌ gemini_api_key column missing, adding...")
            try:
                await session.execute(
                    text("ALTER TABLE users ADD COLUMN gemini_api_key VARCHAR(512)")
                )
                await session.commit()
                fixes_applied.append("Added users.gemini_api_key column")
                print("✓ Added gemini_api_key column")
            except Exception as exc:
                await session.rollback()
                print(f"❌ Failed to add gemini_api_key: {exc}")
        else:
            print("✓ gemini_api_key column exists")

        # Ensure Boolean columns default to False/True where appropriate
        print("Ensuring default flags on users table...")
        try:
            await session.execute(
                text(
                    """
                    UPDATE users
                    SET is_active = COALESCE(is_active, TRUE),
                        is_verified = COALESCE(is_verified, FALSE),
                        oauth_email_verified = COALESCE(oauth_email_verified, FALSE)
                    """
                )
            )
            await session.commit()
            print("✓ Normalized boolean flags on users")
        except Exception as exc:
            await session.rollback()
            print(f"⚠️  Could not normalize user flags: {exc}")

        # ------------------------------------------------------------------
        # Issues table adjustments
        # ------------------------------------------------------------------
        print("\nChecking issues table...")

        required_issue_columns = {
            "analysis_id": "UUID or matching direct_analyses.id",
            "pattern_type": "classification string",
            "location": "JSON payload with code location data",
            "suggestion_text": "primary suggestion text",
            "code_context": "code excerpt for context",
        }

        for column, description in required_issue_columns.items():
            if not await column_exists(session, "issues", column):
                print(
                    f"❌ Column '{column}' is missing on issues (expected: {description}). "
                    "Please add it manually to match the ORM model."
                )
                fixes_applied.append(f"Missing issues.{column} column (manual action required)")
            else:
                print(f"✓ '{column}' column present")

        # Ensure status defaults to 'active' when null
        print("Updating NULL issue status values to 'active'...")
        try:
            result = await session.execute(
                text(
                    """
                    UPDATE issues
                    SET status = 'active'
                    WHERE status IS NULL
                    """
                )
            )
            await session.commit()
            if result.rowcount:
                fixes_applied.append(f"Updated {result.rowcount} issue records without status")
                print(f"✓ Updated {result.rowcount} records")
            else:
                print("✓ No NULL status values found")
        except Exception as exc:
            await session.rollback()
            print(f"⚠️  Could not update issue status values: {exc}")

        # ------------------------------------------------------------------
        # Direct analyses table adjustments
        # ------------------------------------------------------------------
        print("\nChecking direct_analyses table...")

        direct_analysis_columns = {
            "ast_metadata": "JSON",
            "code_patterns": "JSON",
            "issue_ids": "JSON",
            "ast_processing_time": "FLOAT",
        }

        for column_name, column_type in direct_analysis_columns.items():
            if not await column_exists(session, "direct_analyses", column_name):
                print(
                    f"❌ Column '{column_name}' missing on direct_analyses, adding as {column_type}..."
                )
                try:
                    await session.execute(
                        text(
                            f"ALTER TABLE direct_analyses ADD COLUMN {column_name} {column_type}"
                        )
                    )
                    await session.commit()
                    fixes_applied.append(
                        f"Added direct_analyses.{column_name}"
                    )
                    print(f"✓ Added {column_name} column")
                except Exception as exc:
                    await session.rollback()
                    fixes_applied.append(
                        f"Failed to add direct_analyses.{column_name} ({exc})"
                    )
                    print(f"⚠️  Could not add {column_name}: {exc}")
            else:
                print(f"✓ '{column_name}' column present")

        # ------------------------------------------------------------------
        # PR analysis table adjustments
        # ------------------------------------------------------------------
        print("\nChecking pr_analyses table...")

        for column in ("issues_created", "comments_posted"):
            if not await column_exists(session, "pr_analyses", column):
                print(
                    f"❌ Column '{column}' is missing on pr_analyses. Add a JSON column "
                    "with default [] to match the ORM model."
                )
                fixes_applied.append(f"Missing pr_analyses.{column} column (manual action required)")
            else:
                print(f"✓ '{column}' column present")

        # ------------------------------------------------------------------
        # Index maintenance
        # ------------------------------------------------------------------
        print("\nEnsuring core indexes exist...")

        try:
            await create_index(session, "idx_issues_analysis_pattern", "issues", "analysis_id, pattern_type")
            await create_index(session, "idx_issues_severity_status", "issues", "severity, status")
            await create_index(session, "idx_issues_created_at", "issues", "created_at")
            await create_index(session, "idx_pr_analyses_status", "pr_analyses", "status")
            await create_index(session, "idx_pr_analyses_repository", "pr_analyses", "repository_id")
            await session.commit()
            print("✓ Core indexes created/verified")
        except Exception as exc:
            await session.rollback()
            print(f"⚠️  Could not create one or more indexes: {exc}")

        # ------------------------------------------------------------------
        # Summary
        # ------------------------------------------------------------------
        print(f"\n\n{'=' * 80}")
        print("FIX SUMMARY")
        print(f"{'=' * 80}\n")

        if fixes_applied:
            print(f"Applied {len(fixes_applied)} change(s):\n")
            for idx, message in enumerate(fixes_applied, 1):
                print(f"{idx}. {message}")
        else:
            print("No automatic fixes were required – schema already matches the ORM definitions.")

        print(f"\n{'=' * 80}\n")


if __name__ == "__main__":
    asyncio.run(fix_database_issues())
