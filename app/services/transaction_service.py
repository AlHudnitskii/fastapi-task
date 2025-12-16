"""Transaction service module."""

from typing import List, Optional

from loguru import logger
from sqlalchemy.ext.asyncio import AsyncSession

from app.exceptions import (
    NegativeBalanceException,
    TransactionAlreadyRollbackedException,
    TransactionDoesNotBelongToUserException,
    TransactionNotFound,
    UserBlockedException,
    UserNotExistsException,
)
from app.models.enums import TransactionStatusEnumDB, UserStatusEnumDB
from app.models.schemas.transaction import RequestTransactionModel, TransactionModel
from app.repositories.balance_repository import BalanceRepository
from app.repositories.transaction_repository import TransactionRepository
from app.repositories.user_repository import UserRepository


class TransactionService:
    """Transaction service class."""

    def __init__(self, session: AsyncSession):
        """Initialize transaction service."""
        self.session = session
        self.balance_repository = BalanceRepository(session)
        self.transaction_repository = TransactionRepository(session)
        self.user_repository = UserRepository(session)

    async def create_transaction(
        self,
        user_id: int,
        transaction_data: RequestTransactionModel,
    ) -> TransactionModel:
        """Create a new transaction for the specified user."""
        logger.info(
            "Attempting to create transaction",
            user_id=user_id,
            amount=float(transaction_data.amount),
            currency=str(transaction_data.currency),
        )

        user = await self.user_repository.get_user_by_id(user_id)
        if not user:
            logger.warning("User not found for transaction creation", user_id=user_id)
            raise UserNotExistsException(user_id)
        if user.status == UserStatusEnumDB.BLOCKED:
            logger.warning("Blocked user attempted transaction creation", user_id=user_id)
            raise UserBlockedException(user_id, "create transaction")

        balance = await self.balance_repository.get_by_user_and_currency(user_id, transaction_data.currency)

        if balance is None:
            logger.error(
                "Balance not found",
                user_id=user_id,
                currency=str(transaction_data.currency),
            )
            raise ValueError(f"Balance not found for currency {transaction_data.currency}")

        new_balance = balance.amount + transaction_data.amount
        if new_balance < 0:
            logger.warning(
                "Negative balance prevented transaction",
                user_id=user_id,
                current_balance=float(balance.amount),
                requested_amount=float(transaction_data.amount),
            )
            raise NegativeBalanceException(
                currency=str(transaction_data.currency),
                current_balance=float(balance.amount),
                requested_amount=float(transaction_data.amount),
            )

        async with self.transaction_repository.transaction():
            await self.balance_repository.update_balance(
                user_id=user_id,
                currency=transaction_data.currency,
                amount_delta=transaction_data.amount,
            )

            transaction = await self.transaction_repository.create(
                user_id=user_id,
                currency=transaction_data.currency,
                amount=transaction_data.amount,
                status=TransactionStatusEnumDB.POSTED,
            )

        logger.success(
            "Transaction successfully created and posted",
            transaction_id=transaction.id,
            user_id=user_id,
            final_balance=float(new_balance),
        )

        return TransactionModel(
            id=transaction.id,
            user_id=transaction.user_id,
            currency=transaction.currency,
            amount=transaction.amount,
            status=transaction.status,
            created=transaction.created,
        )

    async def get_transactions(
        self,
        user_id: Optional[int] = None,
        skip: int = 0,
        limit: int = 100,
    ) -> List[TransactionModel]:
        """Get transactions with optional user filter."""
        logger.info("Fetching transactions", user_id=user_id, skip=skip, limit=limit)

        if user_id is not None:
            transactions = await self.transaction_repository.get_user_transactions(
                user_id=user_id, skip=skip, limit=limit
            )
        else:
            transactions = await self.transaction_repository.get_all_transactions(skip=skip, limit=limit)

        logger.info(f"Found {len(transactions)} transactions")

        return [
            TransactionModel(
                id=t.id,
                user_id=t.user_id,
                currency=t.currency,
                amount=t.amount,
                status=t.status,
                created=t.created,
            )
            for t in transactions
        ]

    async def rollback_transaction(
        self,
        user_id: int,
        transaction_id: int,
    ) -> TransactionModel:
        """Rollback a transaction."""
        logger.info(
            "Attempting to rollback transaction",
            user_id=user_id,
            transaction_id=transaction_id,
        )

        user = await self.user_repository.get_by_id(user_id)
        if not user:
            logger.warning("User not found for rollback", user_id=user_id)
            raise UserNotExistsException(user_id)

        if user.status.name == UserStatusEnumDB.BLOCKED:
            logger.warning("Blocked user attempted rollback", user_id=user_id)
            raise UserBlockedException(user_id, "rollback transaction")

        transaction = await self.transaction_repository.get_by_id(transaction_id)
        if not transaction:
            logger.warning("Transaction not found for rollback", transaction_id=transaction_id)
            raise TransactionNotFound(transaction_id)

        if transaction.user_id != user_id:
            logger.error(
                "Access denied: Transaction does not belong to user",
                transaction_id=transaction_id,
                user_id=user_id,
                owner_id=transaction.user_id,
            )
            raise TransactionDoesNotBelongToUserException(transaction_id, user_id)

        if transaction.status.name == TransactionStatusEnumDB.REVERSED:
            logger.warning("Transaction already rolled back", transaction_id=transaction_id)
            raise TransactionAlreadyRollbackedException(transaction_id)

        reverse_amount = -transaction.amount

        balance = await self.balance_repository.get_by_user_and_currency(user_id, transaction.currency)
        new_balance = balance.amount + reverse_amount

        if new_balance < 0:
            logger.warning(
                "Negative balance prevented rollback",
                user_id=user_id,
                transaction_id=transaction_id,
                current_balance=float(balance.amount),
                reverse_amount=float(reverse_amount),
            )
            raise NegativeBalanceException(
                currency=str(transaction.currency),
                current_balance=float(balance.amount),
                requested_amount=float(reverse_amount),
            )

        async with self.transaction_repository.transaction():
            await self.balance_repository.update_balance(
                user_id=user_id,
                currency=transaction.currency,
                amount_delta=reverse_amount,
            )

            updated_transaction = await self.transaction_repository.update(
                transaction,
                status=TransactionStatusEnumDB.REVERSED,
            )

        logger.success(
            "Transaction successfully rolled back",
            transaction_id=updated_transaction.id,
            user_id=user_id,
            final_balance=float(new_balance),
        )

        return TransactionModel(
            id=updated_transaction.id,
            user_id=updated_transaction.user_id,
            currency=updated_transaction.currency,
            amount=updated_transaction.amount,
            status=updated_transaction.status,
            created=updated_transaction.created,
        )
