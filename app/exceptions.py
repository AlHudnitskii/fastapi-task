from sre_parse import SRE_FLAG_ASCII
from stat import ST_SIZE

from fastapi import HTTPException, status


class UserAlreadyExistsException(HTTPException):
    """Raised when attempting to create user with existing email"""

    def __init__(self, email: str) -> None:
        super().__init__(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"User with email {email} already exists",
        )


class UserNotExistsException(HTTPException):
    """Raised when user is not found"""

    def __init__(self, user_id: int) -> None:
        super().__init__(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"User with id '{user_id}' not found",
        )


class UserAlreadyBlockedException(HTTPException):
    """Raised when attempting to block an already blocked user"""

    def __init__(self, user_id: int) -> None:
        super().__init__(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"User with id '{user_id}' is already blocked",
        )


class UserAlreadyActiveException(HTTPException):
    """Raised when attempting to activate an already active user"""

    def __init__(self, user_id: int) -> None:
        super().__init__(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"User with id '{user_id}' is already active",
        )


class UserBlockedException(HTTPException):
    """Raised when attempting operations on a blocked user"""

    def __init__(self, user_id: int, operation: str = "operation") -> None:
        super().__init__(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"Cannot perform {operation} for blocked user with id '{user_id}'",
        )


class NegativeBalanceException(HTTPException):
    """Raised when operation would result in negative balance"""

    def __init__(
        self, currency: str, current_balance: float, requested_amount: float
    ) -> None:
        super().__init__(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=(
                f"Insufficient balance in {currency}. "
                f"Current: {current_balance}, Requested: {abs(requested_amount)}"
            ),
        )


class TransactionNotFound(HTTPException):
    """Raised when transaction is not found"""

    def __init__(self, transaction_id: int) -> None:
        super().__init__(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Transaction with id '{transaction_id}' not found",
        )


class TransactionDoesNotBelongToUserException(HTTPException):
    """Raised when transaction doesn't belong to the specified user"""

    def __init__(self, transaction_id: int, user_id: int) -> None:
        super().__init__(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"Transaction with id '{transaction_id}' does not belong to user with id '{user_id}'",
        )


class TransactionAlreadyRollbackedException(HTTPException): ...
