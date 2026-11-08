import sys
import os
from pathlib import Path
from dotenv import load_dotenv

# Ruta para importar módulos de la carpeta raíz del proyecto
_ROOT = Path(__file__).parents[1]
if str(_ROOT) not in sys.path:
    sys.path.append(str(_ROOT))

load_dotenv()
BASE_DIR = Path(__file__).resolve().parent.parent
load_dotenv(BASE_DIR / ".env")

from typing import Annotated, Sequence, Literal
from typing_extensions import TypedDict
from langchain_core.messages import BaseMessage, SystemMessage, ToolMessage
from langchain_ollama import ChatOllama
from langgraph.graph import START, END, StateGraph
from langgraph.graph.message import add_messages
from langgraph.checkpoint.sqlite import SqliteSaver


# importamos las herramientas 
from app.soporte.tools import HERRAMIENTAS_LISTA, TOOLS_MAP

# Define la estructura del estado del Grafo
class State(TypedDict):
    messages: Annotated[Sequence[BaseMessage], add_messages]
    tool_calls_count: int
    errors: list[str]

SYSTEM_PROMPT = SystemMessage(
    content="Eres un asistente ficticio de soporte técnico de solo lectura. "
            "Usa tus herramientas para responder dudas sobre tickets (T-100) o artículos (A-10). "
            "No puedes borrar ni modificar datos. Responde con textos descriptivos claros.\n\n"
            "REGLAS CRÍTICAS DE SEGURIDAD:\n"
            "1. Si el usuario menciona un ticket o número pero NO proporciona el código exacto (ej. T-100), "
            "NO inventes, supongas ni alucines ningún número. Pregúntale directamente al usuario cuál es su código.\n"
            "2. SOLO ejecuta una herramienta si tienes el ID exacto proporcionado explícitamente por el usuario."
)


# configuramos el modelo LLM con Ollama 
llm = ChatOllama(model="llama3.2", temperature=0)
llm_tools = llm.bind_tools(HERRAMIENTAS_LISTA)

def chatbot(state: State) -> dict:
    historial = [SYSTEM_PROMPT] + list(state["messages"])
    respuesta = llm_tools.invoke(historial)
    
    ultimo_mensaje_previo = state["messages"][-1] if state["messages"] else None

    # Validamos correctamente el índice [0] si es una tupla
    if ultimo_mensaje_previo and (
        getattr(ultimo_mensaje_previo, "type", None) == "human" or 
        (isinstance(ultimo_mensaje_previo, tuple) and ultimo_mensaje_previo[0] == "human")
    ):
        contador_actual = 0  # Reinicia con éxito el contador en cada nueva pregunta
    else:
        contador_actual = state.get("tool_calls_count", 0)

    return {
        "messages": [respuesta],
        "tool_calls_count": contador_actual,
        "errors": state.get("errors", [])
    }
def ejecutor_nodos(state: State) -> dict:
    """Nodo simplificado que ejecuta las herramientas con un escudo protector básico."""
    ultimo_mensaje = state["messages"][-1]
    nuevos_mensajes = []
    contador = state.get("tool_calls_count", 0)
    
    # Comprobamos si la IA ha solicitado usar alguna herramienta
    if hasattr(ultimo_mensaje, "tool_calls") and ultimo_mensaje.tool_calls:
        for call in ultimo_mensaje.tool_calls:
            name = call["name"]
            args = call["args"]
            
            # Validamos si la herramienta existe en nuestro mapa
            if name in TOOLS_MAP:
                contador += 1
                try:
                    # Intentamos ejecutar la función con sus argumentos
                    res = TOOLS_MAP[name].invoke(args)
                except Exception:
                    # Si algo falla (argumentos vacíos, error de lectura, etc.), evitamos que se rompa el programa
                    res = f"Error: No se pudo ejecutar '{name}'. Revisa si pusiste los datos correctos."
            else:
                res = "Error: Herramienta no autorizada."
                
            # Guardamos el resultado en el formato que LangGraph exige
            nuevos_mensajes.append(ToolMessage(content=str(res), tool_call_id=call["id"]))
            
    return {"messages": nuevos_mensajes, "tool_calls_count": contador}

def continuar(state: State) -> Literal["execute_tools", "__end__"]:
    ultimo_mensaje = state["messages"][-1]
    contador = state.get("tool_calls_count", 0)
    
    # Si el modelo NO quiere llamar a ninguna herramienta, terminamos el flujo de forma limpia.
    if not hasattr(ultimo_mensaje, "tool_calls") or not ultimo_mensaje.tool_calls:
        return "__end__"
        
    # 2. Si el modelo SÍ quiere usar herramientas, RECIÉN AHÍ comprobamos si superó el límite permitido.
    if contador >= 2:  
        print(f"\n Límite de llamadas alcanzado.")
        return "__end__"
        
    #  Si quiere usar herramientas y no ha superado el límite, avanza al nodo de herramientas.
    return "execute_tools"


# Construcción del grafo de estados
builder = StateGraph(State)
builder.add_node("chatbot", chatbot)
builder.add_node("tools", ejecutor_nodos)

builder.add_edge(START, "chatbot")
builder.add_conditional_edges("chatbot", continuar, {"execute_tools": "tools", "__end__": END})
builder.add_edge("tools", "chatbot")

# Instanciación del gestor de contexto de persistencia
memory_saver = SqliteSaver.from_conn_string("soporte_memoria.db")

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--pregunta", default="Consulta el estado del ticket T-100")
    parser.add_argument("--hilo", default="chat_defecto")
    args = parser.parse_args()

    with memory_saver as saver:
        graph = builder.compile(checkpointer=saver)
        config = {"configurable": {"thread_id": args.hilo}}
        
        # inicialicazion de historial de mensajes con la pregunta del usuario
        estado_inicial = {"messages": [("human", args.pregunta)]}
        
        # Invocamos la ejecución del grafo
        resultado = graph.invoke(estado_inicial, config)
        
        # Filtrado de respuesta limpia
        respuesta = resultado["messages"][-1].content
        texto_limpio = ""

        if isinstance(respuesta, list):
            for bloque in respuesta:
                if isinstance(bloque, dict) and "text" in bloque:
                    texto_limpio += bloque["text"]
                else:
                    texto_limpio += str(bloque)
        elif isinstance(respuesta, str):
            texto_limpio = respuesta
        else:
            texto_limpio = str(respuesta)

        print("\n Asistente:", texto_limpio.strip())
