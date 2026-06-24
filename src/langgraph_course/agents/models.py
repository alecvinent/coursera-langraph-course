from typing import List

from pydantic import BaseModel


class Customer(BaseModel):
    name: str
    address: str
    phone: str
    email: str


class MenuOptions(BaseModel):
    name: str
    price: float
    description: str
    category: str = ""
    tags: list[str] = []
    variations: list[str] = []


class DailyMenu(BaseModel):
    date: str
    options: List[MenuOptions]


class OrderDetail(BaseModel):
    product: str
    quantity: int
    price: float


class Order(BaseModel):
    customer: Customer
    date: str
    details: List[OrderDetail]
