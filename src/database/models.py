from sqlalchemy import BigInteger, String, Float, ForeignKey, Date, DateTime, func
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
from datetime import datetime

class Base(DeclarativeBase):
    pass

class User(Base):
    __tablename__ = "users"
    id: Mapped[int] = mapped_column(primary_key=True)
    telegram_id: Mapped[int] = mapped_column(BigInteger, unique=True)
    username: Mapped[str | None] = mapped_column(String(128))
    registered_at: Mapped[datetime] = mapped_column(server_default=func.now())

class Expense(Base):
    __tablename__ = "expenses"
    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.telegram_id", ondelete="CASCADE"))
    amount: Mapped[float] = mapped_column(Float)
    category: Mapped[str] = mapped_column(String(64))
    # ВИПРАВЛЕНО: Використовуємо функцію бази даних для поточної дати
    date: Mapped[datetime] = mapped_column(Date, server_default=func.current_date())

class Goal(Base):
    __tablename__ = "goals"
    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.telegram_id", ondelete="CASCADE"))
    name: Mapped[str] = mapped_column(String(128))
    target_amount: Mapped[float] = mapped_column(Float)
    current_amount: Mapped[float] = mapped_column(Float, default=0.0)
    deadline: Mapped[datetime | None] = mapped_column(Date)

class Limit(Base):
    __tablename__ = "limits"
    user_id: Mapped[int] = mapped_column(ForeignKey("users.telegram_id", ondelete="CASCADE"), primary_key=True)
    category: Mapped[str] = mapped_column(String(64), primary_key=True)
    amount: Mapped[float] = mapped_column(Float)

class Subscription(Base):
    __tablename__ = "subscriptions"
    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.telegram_id", ondelete="CASCADE"))
    name: Mapped[str] = mapped_column(String(128))
    amount: Mapped[float] = mapped_column(Float)
    next_date: Mapped[datetime] = mapped_column(Date)