from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.models.books import Book

from .base import BaseModel

"""
У продавца есть обязательные поля:
- id
- first_name
- last_name
- e_mail
- password
"""
class Seller(BaseModel):
    __tablename__ = "sellers_table"

    id: Mapped[int] = mapped_column(primary_key=True)
    first_name: Mapped[str] = mapped_column(String(100), nullable=False)
    last_name: Mapped[str] = mapped_column(String(100), nullable=False)
    e_mail: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)
    password: Mapped[str] = mapped_column(String(100), nullable=False)

    seller_books: Mapped[list["Book"]] = relationship(
        back_populates="seller", 
        cascade="all, delete-orphan",
        passive_deletes=True,
        single_parent=True,
        lazy="selectin"
    )