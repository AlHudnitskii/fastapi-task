"""Script to seed the database with test data."""

import asyncio
import random
from decimal import Decimal

from faker import Faker
from loguru import logger
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from app.config import settings
from app.models.enums import CurrencyEnumDB
from app.models.schemas.transaction import RequestTransactionModel
from app.models.schemas.user import UserCreateRequest
from app.services.transaction_service import TransactionService
from app.services.user_service import UserService

fake = Faker()


async def seed_database(num_users: int = 10, num_transactions_per_user: int = 5) -> None:
    """Seed database with test users and transactions."""
    logger.info(f"Starting database seeding: {num_users} users, {num_transactions_per_user} transactions each")

    engine = create_async_engine(settings.database_url, echo=False)
    async_session_maker = async_sessionmaker(engine, expire_on_commit=False)

    async with async_session_maker() as session:
        user_service = UserService(session)
        transaction_service = TransactionService(session)

        created_users = []

        logger.info(f"Creating {num_users} users...")
        for i in range(num_users):
            try:
                email = fake.unique.email()
                user = await user_service.create_user(UserCreateRequest(email=email))
                created_users.append(user)
                logger.debug(f"Created user {i + 1}/{num_users}: {email} (ID: {user.id})")
            except Exception as e:
                logger.error(f"Failed to create user {i + 1}: {e}")

        logger.success(f"Successfully created {len(created_users)} users")

        logger.info("Creating transactions...")
        total_transactions = 0

        for user in created_users:
            user_transactions = 0

            for _ in range(num_transactions_per_user):
                try:
                    currency = random.choice(list(CurrencyEnumDB))

                    is_deposit = random.random() < 0.7

                    if is_deposit:
                        amount = Decimal(str(round(random.uniform(10, 1000), 2)))
                    else:
                        user_detail = await user_service.get_user_by_id(user.id)
                        balance = next(
                            (b.amount for b in user_detail.balances if b.currency == currency),
                            Decimal(0),
                        )

                        if balance > 0:
                            max_withdrawal = min(balance, Decimal("500"))
                            amount = -Decimal(str(round(random.uniform(1, float(max_withdrawal)), 2)))
                        else:
                            amount = Decimal(str(round(random.uniform(10, 500), 2)))

                    transaction = await transaction_service.create_transaction(
                        user_id=user.id,
                        transaction_data=RequestTransactionModel(currency=currency, amount=amount),
                    )

                    user_transactions += 1
                    total_transactions += 1

                    if random.random() < 0.1:
                        try:
                            await transaction_service.rollback_transaction(user.id, transaction.id)
                            logger.debug(f"Rolled back transaction {transaction.id}")
                        except Exception as e:
                            logger.debug(f"Could not rollback transaction {transaction.id}: {e}")

                except Exception as e:
                    logger.warning(f"Failed to create transaction for user {user.id}: {e}")

            logger.debug(f"Created {user_transactions} transactions for user {user.id}")

        logger.success(f"Successfully created {total_transactions} transactions")

        logger.info("=== Database Seeding Summary ===")
        logger.info(f"Users created: {len(created_users)}")
        logger.info(f"Transactions created: {total_transactions}")
        logger.info(
            f"Average transactions per user: {total_transactions / len(created_users) if created_users else 0:.2f}"
        )

    await engine.dispose()
    logger.success("Database seeding completed successfully!")


async def clear_database() -> None:
    """Clear all data from database (for testing purposes)."""
    logger.warning("Clearing database...")

    engine = create_async_engine(settings.database_url, echo=False)

    async with engine.begin() as conn:
        await conn.execute("DELETE FROM journal_entries")
        await conn.execute("DELETE FROM outbox_events")
        await conn.execute("DELETE FROM transactions")
        await conn.execute("DELETE FROM user_balances")
        await conn.execute("DELETE FROM users")
        await conn.execute("DELETE FROM accounts")

    await engine.dispose()
    logger.success("Database cleared successfully!")


async def main() -> None:
    """Run the script."""
    import sys

    if len(sys.argv) > 1 and sys.argv[1] == "--clear":
        await clear_database()
        return

    num_users = int(sys.argv[1]) if len(sys.argv) > 1 else 10
    num_transactions = int(sys.argv[2]) if len(sys.argv) > 2 else 5

    await seed_database(num_users=num_users, num_transactions_per_user=num_transactions)


if __name__ == "__main__":
    asyncio.run(main())
