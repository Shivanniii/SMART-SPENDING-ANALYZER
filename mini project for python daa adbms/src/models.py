from dataclasses import dataclass


@dataclass
class User:
    user_id: int
    username: str
    role: str


@dataclass
class Transaction:
    user_id: int
    expense_date: str
    amount: float
    category: str
    payment_method: str
    description: str = ""
    transaction_id: int | None = None


@dataclass
class Budget:
    user_id: int
    budget_month: str
    category: str
    amount: float
    budget_id: int | None = None