from typing import Annotated

import requests
from langchain_core.tools import tool

from langgraph_course.agents.cafe.models import Customer, DailyMenu, MenuOptions, Order, OrderDetail
from log import logger
from utils.request import get_json

_MENU = DailyMenu(
    date="2026-06-23",
    options=[
        MenuOptions(
            name="Espresso", price=3.50, description="Classic espresso shot",
            category="coffee", tags=["vegan", "gluten-free"],
            variations=["double shot", "decaf"],
            image_url="https://images.unsplash.com/photo-1510707577719-ae7c14805e3a?w=400&h=250&fit=crop",
        ),
        MenuOptions(
            name="Latte", price=4.50, description="Steamed milk espresso",
            category="coffee", tags=["vegetarian"],
            variations=["oat milk", "soy milk", "almond milk"],
            image_url="https://images.unsplash.com/photo-1570968915860-54d5c301fa9f?w=400&h=250&fit=crop",
        ),
        MenuOptions(
            name="Croissant", price=3.00, description="Buttery croissant",
            category="pastry", tags=["vegetarian"],
            variations=["gluten-free option", "stuffed with ham & cheese"],
            image_url="https://images.unsplash.com/photo-1509363542-6e2f3c0b1b0e?w=400&h=250&fit=crop",
        ),
        MenuOptions(
            name="Avocado Toast", price=7.50, description="Smashed avocado on sourdough",
            category="breakfast", tags=["vegan", "vegetarian"],
            variations=["add egg", "add bacon", "no onions"],
            image_url="https://images.unsplash.com/photo-1541519227354-08fa5d50c44d?w=400&h=250&fit=crop",
        ),
        MenuOptions(
            name="Cold Brew", price=4.00, description="24-hour steeped cold brew",
            category="coffee", tags=["vegan", "gluten-free"],
            variations=["vanilla syrup", "with cream"],
            image_url="https://images.unsplash.com/photo-1461023058943-07fcbe16d735?w=400&h=250&fit=crop",
        ),
    ],
)

_CATEGORY_KEYWORDS = {
    "coffee": ["coffee", "espresso", "latte", "cappuccino", "mocha", "cold brew", "drink"],
    "pastry": ["pastry", "croissant", "donut", "muffin", "bagel", "bread", "cake"],
    "breakfast": ["burger", "hamburger", "toast", "sandwich", "eggs", "bacon", "breakfast"],
}

_PRICE_MAP: dict[str, float] = {opt.name.lower(): opt.price for opt in _MENU.options}

_orders: list[OrderDetail] = []
_customer: Customer | None = None


def _clear() -> None:
    _orders.clear()
    global _customer
    _customer = None


@tool
def get_daily_menu() -> str:
    """Return today's daily menu with item names, prices, and food categories."""
    logger.info("Fetching cafe menu...")

    url = 'http://localhost:3000/api/v1/daily-menu'
    try:
        return get_json(url)
    except requests.RequestException as e:
        return f"Error fetching cafe menu: {e}"


@tool
def get_recommendations() -> str:
    """Return today's featured recommendations from the menu."""
    lines = ["Today's Recommendations:"]
    for item in _MENU.options:
        lines.append(f"- {item.name}: ${item.price:.2f} — {item.description}")
        lines.append(f"  Image: {item.image_url}")
    return "\n".join(lines)


@tool
def recommend_by_preference(
    preference: Annotated[str, "Dietary preference or food category, e.g. vegetarian, vegan, gluten-free, coffee, pastry, breakfast"],
) -> str:
    """Recommend menu items matching a dietary preference or food category."""
    pref = preference.lower()
    matching = [
        opt for opt in _MENU.options
        if pref == opt.category.lower() or any(pref == t.lower() for t in opt.tags)
    ]
    if not matching:
        return f"No items found for '{preference}'."
    lines = [f"Items matching '{preference}':"]
    for opt in matching:
        lines.append(f"- {opt.name}: ${opt.price:.2f} — {opt.description}")
        lines.append(f"  Image: {opt.image_url}")
        if opt.variations:
            lines.append(f"  Variations: {', '.join(opt.variations)}")
    return "\n".join(lines)


@tool
def create_order(
    item_name: Annotated[str, "Name of the menu item to order"],
    quantity: Annotated[int, "Number of items"] = 1,
) -> str:
    """Add a menu item to the current order. Call this when the user wants to order an item."""
    price = _PRICE_MAP.get(item_name.lower())
    if price is None:
        name_lower = item_name.lower()
        guessed_cat = next(
            (cat for cat, kws in _CATEGORY_KEYWORDS.items()
             if any(kw in name_lower for kw in kws)),
            None,
        )
        matching = [opt for opt in _MENU.options
                    if opt.category == guessed_cat] if guessed_cat else []
        lines = [f"Sorry, '{item_name}' is not on the menu."]
        if matching:
            lines.append(f"From our {guessed_cat} options, you might like:")
            lines.extend(f"- {opt.name}: ${opt.price:.2f} — {opt.description}" for opt in matching)
        else:
            lines.append("Would you like to see our full menu or recommendations?")
        return "\n".join(lines)
    _orders.append(OrderDetail(product=item_name, quantity=quantity, price=price))
    return f"Added {quantity} x {item_name} (${price:.2f} each) to your order."


@tool
def get_orders() -> str:
    """Return all items currently in the user's order with quantities, line totals, and grand total."""
    if not _orders:
        return "You have no orders yet."
    lines = ["Your Orders:"]
    total = 0.0
    for o in _orders:
        line_total = o.price * o.quantity
        total += line_total
        if o.quantity > 1:
            lines.append(f"- {o.product} x{o.quantity}: ${line_total:.2f}")
        else:
            lines.append(f"- {o.product}: ${line_total:.2f}")
    lines.append(f"\nTotal: ${total:.2f}")
    return "\n".join(lines)


@tool
def set_customer_info(
    name: Annotated[str, "Customer's full name"],
    address: Annotated[str, "Customer's delivery address"],
    phone: Annotated[str, "Customer's phone number"],
    email: Annotated[str, "Customer's email address"],
) -> str:
    """Store customer details for the order. Call this before send_order."""
    global _customer
    _customer = Customer(name=name, address=address, phone=phone, email=email)
    return f"Customer details saved for {name}."


@tool
def send_order() -> str:
    """Finalize and submit the order. Requires customer info and at least one item to be set first."""
    global _customer
    if _customer is None:
        return "Please provide your name, address, phone, and email first."
    if not _orders:
        return "No items to order. Please add items to your order first."
    order = Order(customer=_customer, date="2026-06-23", details=list(_orders))
    total = sum(d.price * d.quantity for d in _orders)
    _orders.clear()
    _customer = None
    lines = [f"Order confirmed for {order.customer.name}! Thank you for your order!"]
    for d in order.details:
        lines.append(f"- {d.product} x{d.quantity}: ${d.price * d.quantity:.2f}")
    lines.append(f"\nTotal: ${total:.2f}")
    lines.append(f"Delivery to: {order.customer.address}")
    return "\n".join(lines)
