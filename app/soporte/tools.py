
import os
import json
import time
from langchain_core.tools import tool

# Buscamos el archivo JSON único en la carpeta app/datos/.json  y lo cargamos
BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
DB_PATH = os.path.join(BASE_DIR, "app", "datos", "datos.json")

# Cargamos el archivo completo una sola vez solo lectura
with open(DB_PATH, "r", encoding="utf-8") as f:
    DATABASE_COMPLETA = json.load(f)

# Separamos las colecciones 
TICKETS_DB = DATABASE_COMPLETA.get("tickets", {})
ARTICULOS_DB = DATABASE_COMPLETA.get("knowledge_base", {})

@tool
def consultar_ticket(ticket_id: str) -> str:
    """Consulta el estado y actualización de un ticket usando su ID (ej. T-100)."""
    clean_id = ticket_id.strip().upper()
    if clean_id in TICKETS_DB:
        t = TICKETS_DB[clean_id]
        return f"Ticket {clean_id}: Estado: {t['estado']}. Asunto: {t['asunto']}. Actualización: {t['actualizacion']}."
    return f"Error: El ticket {clean_id} no existe."

@tool
def buscar_articulo(articulo_id: str) -> str:
    """Busca la ayuda de un artículo usando su ID exacto (ej. A-10)."""
    clean_id = articulo_id.strip().upper()
    if clean_id in ARTICULOS_DB:
        a = ARTICULOS_DB[clean_id]
        return f"Artículo {clean_id} [{a['titulo']}]: {a['texto']}"
    return f"Error: El artículo {clean_id} no existe."

# indicamos al modelo que estas son las herramientas disponibles para usar, 
# y que no puede inventar otras herramientas
HERRAMIENTAS_LISTA = [consultar_ticket, buscar_articulo]
TOOLS_MAP = {"consultar_ticket": consultar_ticket, "buscar_articulo": buscar_articulo}
