"""
Reflection Pattern — Yordan Bistro Coffee Bar Domain

Cafe-domain variant of the reflection pattern.  The generator and critic
fetch live data from the cafe management API and use it to craft responses.

Graph:
  entry -> fetch_cafe_data -> human_review -> generator -> critic -> generator (or END)
                                                          ↑         |
                                                          +---loop--+

API calls (all unauthenticated):
  - GET /config      — cafe name, address, schedule, contact info
  - GET /products    — product catalog with prices and categories
  - GET /daily-menu  — today's special offers and menu items
  - GET /health      — server health check (used as connectivity probe)

Reference: https://machinelearningmastery.com/7-must-know-agentic-ai-design-patterns/
"""

import json
import time
import urllib.request
import uuid
from typing import Annotated, Any, Dict, Sequence, TypedDict

from langchain_core.messages import BaseMessage
from langgraph.checkpoint.memory import MemorySaver
from langgraph.constants import END
from langgraph.graph import StateGraph, add_messages
from langgraph.graph.state import CompiledStateGraph
from langgraph.types import Command, interrupt

from log import logger
from utils import AgentBase
from utils import timed_node
from utils import LLMFactory


# ---------------------------------------------------------------------------
# API client
# ---------------------------------------------------------------------------
API_BASE = "http://localhost:3000/api/v1"
REQUEST_TIMEOUT = 5  # seconds


def _api_get(path: str) -> Any | None:
    """Make a GET request to the cafe API.  Returns parsed JSON or None."""
    url = f"{API_BASE}{path}"
    try:
        req = urllib.request.Request(url, method="GET")
        with urllib.request.urlopen(req, timeout=REQUEST_TIMEOUT) as resp:
            if 200 <= resp.status < 300:
                return json.loads(resp.read().decode())
    except Exception as exc:
        logger.warning("[API] GET {} failed: {}", path, exc)
    return None





# ---------------------------------------------------------------------------
# Helpers to extract data from API responses
# ---------------------------------------------------------------------------
def _schedule_str(data: Dict | None) -> str:
    if not data:
        return ""
    days = data.get("schedule", {}).get("days", [])
    if days:
        times = f"{days[0].get('open', '09:00')} - {days[0].get('close', '20:00')}"
        return f"Lunes a Domingo {times}"
    return ""


def _categories_str(data: Dict | None) -> str:
    if not data:
        return ""
    cats = data.get("categories", [])
    parts: list[str] = []
    known = {"bebidas": "☕", "dulces": "🥐"}
    for c in cats:
        emoji = known.get(c["name"], "•")
        parts.append(f"  • {emoji} {c['name'].capitalize()}")
    return "\n".join(parts)


def _contact_block(data: Dict | None) -> str:
    d = data or {}
    lines: list[str] = []
    if addr := d.get("address"):
        lines.append(f"📍 Dirección: {addr}")
    lines.append(f"🕐 Horario: {_schedule_str(data)}")
    if phone := d.get("phone"):
        lines.append(f"📞 Teléfono: {phone}")
    if wa := d.get("whatsapp"):
        lines.append(f"📱 WhatsApp: {wa}")
    if email := d.get("email"):
        lines.append(f"✉️ Email: {email}")
    return "\n".join(lines)


def _products_by_category(data: Dict | None) -> tuple[str, int]:
    """Return (formatted product listing, cheapest price) from API product data."""
    items: list[Dict] = []
    if data:
        items = data.get("products", data.get("items", []))
    if not items:
        return "", 0

    bebidas: list[str] = []
    dulces: list[str] = []
    min_price = 999999
    for p in items:
        price = int(p.get("price", 0))
        if price and price < min_price:
            min_price = price
        line = f"  • {p['name']} — $UY {price}"
        cat = p.get("category", "").lower()
        if "dulce" in cat:
            dulces.append(line)
        else:
            bebidas.append(line)

    parts: list[str] = ["☕ Bebidas calientes:"] + bebidas
    if dulces:
        parts += ["", "🥐 Dulces artesanales:"] + dulces

    return "\n".join(parts), min_price if min_price < 999999 else 100


def _offers_str(data: Dict | None) -> str:
    """Extract special offers from the daily menu API response."""
    if not data:
        return ""
    items = data.get("items", []) if isinstance(data, dict) else []
    offers = [i for i in items if i.get("type") == "oferta"]
    if not offers:
        return ""
    lines = ["", "🔥 Ofertas especiales del día:"]
    for o in offers:
        name = o.get("productName", o.get("name", "Producto"))
        price = o.get("price", "")
        lines.append(f"  • {name} — $UY {price}" if price else f"  • {name}")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Cafe topic constants
# ---------------------------------------------------------------------------
class CafeTopic:
    MENU = "menu"
    ORDER = "order"
    CUSTOMER = "customer"
    GENERAL = "general"


# ---------------------------------------------------------------------------
# State schema
# ---------------------------------------------------------------------------
class CafeData(TypedDict):
    config: Dict
    products: Dict
    daily_menu: Dict | None


class CafeReflectionState(TypedDict):
    messages: Annotated[Sequence[BaseMessage], add_messages]
    query: str
    topic: str
    draft: str
    feedback: str
    approved: bool
    response: str
    rounds: int
    total_processing_time: float
    latencies: Dict[str, float]
    paths_taken: list[str]
    human_decision: str
    cafe_data: CafeData | None


# ---------------------------------------------------------------------------
# Agent class
# ---------------------------------------------------------------------------
class CafeReflectionAgent(AgentBase):

    MAX_ROUNDS = 4

    def __init__(self, provider: str = "openrouter", llm=None) -> None:
        self.llm = llm or LLMFactory.create(provider=provider)
        super().__init__()

    # -- Classification ---------------------------------------------------
    @classmethod
    def _classify_topic(cls, query: str) -> str:
        topic = query.lower()
        if any(word in topic for word in (
            "menu", "menú", "specials", "offer", "carta", "promo",
            "recommendation", "available", "options", "pastry",
            "coffee", "café", "drink", "bebida", "what do you have",
            "dulce", "dulces",
        )):
            return CafeTopic.MENU
        if any(word in topic for word in (
            "order", "orden", "buy", "comprar", "purchase",
            "cart", "carrito", "checkout", "pagar", "pay",
            "total", "price", "precio", "cost", "cuesta",
        )):
            return CafeTopic.ORDER
        if any(word in topic for word in (
            "delivery", "envío", "info", "account", "cuenta",
            "loyalty", "puntos", "feedback", "complaint", "queja",
            "refund", "reembolso", "cancel", "cancelar",
            "horario", "schedule", "direction", "dirección",
        )):
            return CafeTopic.CUSTOMER
        return CafeTopic.GENERAL

    # -- Entry node -------------------------------------------------------
    @classmethod
    @timed_node('entry')
    def entry(cls, state: CafeReflectionState) -> Dict:
        query = state.get('query') or cls.get_last_message(state)
        logger.info("[Entry] Starting Cafe Reflection loop for: {}", query[:60])
        return {
            'query': query,
            'messages': [("assistant", "Entry: Starting Cafe Reflection loop")],
        }

    # -- Fetch API data node ----------------------------------------------
    @classmethod
    @timed_node('fetch_cafe_data')
    def fetch_cafe_data(cls, state: CafeReflectionState) -> Dict:
        logger.info("[Fetch] Fetching cafe data from API at {}", API_BASE)

        config = _api_get("/config")
        products = _api_get("/products")
        daily_menu = _api_get("/daily-menu")

        cafe_data: CafeData = {
            "config": config,
            "products": products,
            "daily_menu": daily_menu,
        }
        name = config.get("appName", "Yordan Bistro Coffee Bar")
        logger.info("[Fetch] Loaded data for {}", name)
        return {"cafe_data": cafe_data}

    # -- Human review gate ------------------------------------------------
    @classmethod
    @timed_node('human_review')
    def human_review(cls, state: CafeReflectionState) -> Dict:
        logger.info("[Human Review] Pending review for Cafe Reflection agent")
        decision = interrupt({"message": "Approve Cafe Reflection agent execution?"})
        logger.info("[Human Review] Decision: {}", decision)
        return {'human_decision': decision or 'approve'}

    @classmethod
    def human_router(cls, state: CafeReflectionState) -> str:
        decision = state.get('human_decision', 'approve')
        if decision == 'end':
            return END
        if decision == 'redirect':
            return 'entry'
        return 'generator'

    # -- Generator node ---------------------------------------------------
    @classmethod
    @timed_node('generator')
    def generator(cls, state: CafeReflectionState) -> Dict:
        rounds = state.get('rounds', 0)
        query = state.get('query', '')
        feedback = state.get('feedback', '')
        logger.info("[Generator] Drafting cafe response (round {})", rounds + 1)

        if rounds >= cls.MAX_ROUNDS:
            return {
                'response': state.get('draft', ''),
                'rounds': rounds + 1,
            }

        if not feedback:
            # First call: classify from the query, store both draft and topic.
            topic = cls._classify_topic(query)
            draft = cls._initial_draft(topic)
            return {
                'draft': draft,
                'topic': topic,
                'rounds': rounds + 1,
                'messages': [("assistant", f"Generator: Initial cafe draft (round {rounds + 1})")],
            }

        # Subsequent call: use the stored topic for dispatch.
        topic = state.get('topic', 'general')
        revised = cls._revise_draft(topic, feedback, state.get('cafe_data'))
        return {
            'draft': revised,
            'rounds': rounds + 1,
            'messages': [("assistant", f"Generator: Revised cafe draft (round {rounds + 1})")],
        }

    @classmethod
    def _initial_draft(cls, topic: str) -> str:
        if topic == CafeTopic.MENU:
            return "Tenemos una gran selección hoy. ¡Bienvenido a Yordan Bistro Coffee Bar!"
        if topic == CafeTopic.ORDER:
            return "Recibimos tu solicitud de pedido. La procesaremos en breve."
        if topic == CafeTopic.CUSTOMER:
            return "Gracias por contactarnos. Te responderemos pronto."
        return "Bienvenido a Yordan Bistro Coffee Bar. ¿Cómo podemos ayudarte?"

    @classmethod
    def _revise_draft(cls, topic: str, feedback: str, cafe_data: CafeData | None) -> str:
        conf = (cafe_data.get("config") if cafe_data else None) or {}
        prods = (cafe_data.get("products") if cafe_data else None) or {}
        daily = cafe_data.get("daily_menu") if cafe_data else None
        name = conf.get("appName", "Yordan Bistro Coffee Bar")
        welcome = conf.get("welcomeMessage", "Bienvenido")
        desc = conf.get("appDescription", "")

        # --- Menu topic ---
        if topic == CafeTopic.MENU:
            product_block, _ = _products_by_category(prods)
            offers = _offers_str(daily)
            return (
                f"¡{welcome} a {name}! 🌟\n\n"
                f"Hoy tenemos una variedad deliciosa:\n\n"
                f"{product_block}\n"
                f"{offers or ''}\n\n"
                "¿Te gustaría hacer un pedido? Aceptamos pedidos "
                "para retirar en local o con envío."
            )

        # --- Order topic ---
        if topic == CafeTopic.ORDER:
            contact = _contact_block(conf)
            return (
                f"¡Gracias por tu pedido en {name}!\n\n"
                "Resumen de tu orden:\n"
                "  • 1x Café Latte — $UY 120\n"
                "  • 1x Alfajor Artesanal — $UY 70\n"
                "  • Subtotal: $UY 190\n\n"
                "Estado actual: Pendiente\n"
                "Próximos pasos: Preparando → Listo → Entregado\n\n"
                "Por favor indicanos tu preferencia:\n"
                "  - Recoger en local\n"
                "  - Envío a domicilio\n\n"
                f"{contact}\n\n"
                "🪙 ¡Ganas puntos de fidelidad con cada compra! "
                "Acumula y sube de nivel: Bronce → Plata → Oro → Diamante."
            )

        # --- Customer topic ---
        if topic == CafeTopic.CUSTOMER:
            contact = _contact_block(conf)
            cats = _categories_str(conf)
            return (
                f"¡{welcome} a {name}! 🌟\n\n"
                f"{desc}\n\n"
                f"{contact}\n\n"
                "Nuestras categorías:\n"
                f"{cats}\n\n"
                "Pregunta por nuestras ofertas del día o "
                "haz tu pedido directamente. "
                "¡Te esperamos!"
            )

        # --- Fallback (general) ---
        return (
            f"Gracias por contactar a {name}. "
            "Un miembro de nuestro equipo te atenderá a la brevedad. "
            "Mientras tanto, puedes consultar nuestro menú "
            "o escribirnos por WhatsApp al 59896379476."
        )

    # -- Critic node ------------------------------------------------------
    @classmethod
    @timed_node('critic')
    def critic(cls, state: CafeReflectionState) -> Dict:
        rounds = state.get('rounds', 0)
        draft = state.get('draft', '')
        logger.info("[Critic] Evaluating cafe draft (round {})", rounds)

        if rounds >= cls.MAX_ROUNDS:
            return {'approved': True, 'response': draft}

        cafe_data = state.get('cafe_data')
        evaluation = cls._evaluate_draft(draft, rounds, cafe_data)
        if evaluation['approved']:
            logger.info("[Critic] Cafe draft approved")
            return {
                'approved': True,
                'feedback': '',
                'response': draft,
                'messages': [("assistant", "Critic: Cafe draft approved.")],
            }

        logger.info("[Critic] Feedback: {}", evaluation['feedback'][:60])
        return {
            'approved': False,
            'feedback': evaluation['feedback'],
            'messages': [("assistant", f"Critic: {evaluation['feedback']}")],
        }

    @classmethod
    def _evaluate_draft(cls, draft: str, rounds: int, cafe_data: CafeData | None) -> Dict:
        if rounds <= 1:
            if len(draft) < 120:
                return {
                    'approved': False,
                    'feedback': (
                        "La respuesta es demasiado genérica. Por favor amplíala "
                        "para incluir:\n"
                        "(1) productos específicos con sus precios en pesos uruguayos, "
                        "(2) el horario y dirección del local, "
                        "(3) opciones de envío o retiro, y "
                        "(4) un tono cálido y acogedor como el de nuestra cafetería. "
                        "Recuerda que somos Yordan Bistro Coffee Bar."
                    ),
                }

        # Check if daily menu offers exist but are not mentioned in the draft.
        daily = (cafe_data.get("daily_menu") if cafe_data else None)
        if daily:
            items = daily.get("items", []) if isinstance(daily, dict) else []
            offers = [i for i in items if i.get("type") == "oferta"]
            if offers:
                draft_lower = draft.lower()
                offer_keywords = ["oferta", "especial", "hoy", "daily special", "promo", "special"]
                if not any(kw in draft_lower for kw in offer_keywords):
                    names = [o.get("productName", o.get("name", "Producto")) for o in offers]
                    offers_list = "\n".join(f"  • {n}" for n in names)
                    return {
                        'approved': False,
                        'feedback': (
                            "El menú diario tiene ofertas especiales que no están "
                            "mencionadas en la respuesta. Por favor incluye las "
                            "ofertas del día para que los clientes conozcan "
                            "todas las opciones disponibles:\n"
                            f"{offers_list}\n\n"
                            "Agrega estas ofertas en la sección de ofertas especiales."
                        ),
                    }

        return {'approved': True}

    # -- Routers ----------------------------------------------------------
    @classmethod
    def generator_router(cls, state: CafeReflectionState) -> str:
        return 'critic'

    @classmethod
    def critic_router(cls, state: CafeReflectionState) -> str:
        if state.get('approved', False):
            return END
        if state.get('rounds', 0) >= cls.MAX_ROUNDS:
            return END
        return 'generator'

    # -- Graph construction -----------------------------------------------
    def _build_graph(self) -> CompiledStateGraph:
        workflow = StateGraph(CafeReflectionState)

        workflow.add_node('entry', self.entry)
        workflow.add_node('fetch_cafe_data', self.fetch_cafe_data)
        workflow.add_node('human_review', self.human_review)
        workflow.add_node('generator', self.generator)
        workflow.add_node('critic', self.critic)

        workflow.set_entry_point('entry')

        # entry → fetch API data → human review → ...
        workflow.add_edge('entry', 'fetch_cafe_data')
        workflow.add_edge('fetch_cafe_data', 'human_review')

        workflow.add_conditional_edges(
            'human_review',
            self.human_router,
            {END: END, 'entry': 'entry', 'generator': 'generator'},
        )

        workflow.add_conditional_edges(
            'generator',
            self.generator_router,
            {'critic': 'critic'},
        )

        workflow.add_conditional_edges(
            'critic',
            self.critic_router,
            {END: END, 'generator': 'generator'},
        )

        return workflow.compile(checkpointer=MemorySaver())

    # -- Entry point ------------------------------------------------------
    def run(self, question: str) -> Dict:
        logger.info("Processing Cafe Reflection request: {!r}", question)
        thread_id = str(uuid.uuid4())
        config = {"configurable": {"thread_id": thread_id}}
        initial_state: Dict = {
            "messages": [("user", question)],
            "query": question,
            "topic": "",
            "draft": "",
            "feedback": "",
            "approved": False,
            "response": "",
            "rounds": 0,
            "total_processing_time": time.time(),
            "latencies": {},
            "paths_taken": [],
            "human_decision": "",
            "cafe_data": None,
        }
        result = self.graph.invoke(initial_state, config)
        while '__interrupt__' in result:
            result = self.graph.invoke(Command(resume="approve"), config)
        logger.info("Result: {}", result.get("response", ""))
        return result


# ---------------------------------------------------------------------------
# Demo
# ---------------------------------------------------------------------------
if __name__ == '__main__':
    agent = CafeReflectionAgent()
    print(agent.graph.get_graph().draw_mermaid())
    samples = [
        "What's on the menu today?",
        "I'd like to order a latte and an alfajor",
        "¿Cuál es la dirección y el horario?",
        "hi",
    ]
    for q in samples:
        result = agent.run(q)
        print(f"\nQ: {q}")
        print(f"  Paths: {' → '.join(result.get('paths_taken'))}")
        print(f"  Drafts / rounds: {result.get('rounds')}")
        print(f"  Approved: {result.get('approved')}")
        print(f"  Response: {result.get('response')}")
