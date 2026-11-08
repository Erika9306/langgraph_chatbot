import sys
from pathlib import Path

# Buscamos la carpeta raíz para que Python no se pierda al importar
_ROOT = Path(__file__).parents[1]
if str(_ROOT) not in sys.path:
    sys.path.append(str(_ROOT))

from typing import Annotated, Sequence
from typing_extensions import TypedDict
from langchain_core.messages import BaseMessage, AIMessage, HumanMessage
from langgraph.graph import START, END, StateGraph
from langgraph.graph.message import add_messages

# el estado del grafo, el historial, numero de llamadas al tools y listado de errores

class State(TypedDict):
    messages: Annotated[Sequence[BaseMessage], add_messages]  
    tool_calls_count: int                                    
    errors: list[str]                                         

# nodo con respuesta fija para pruebas de la etapa 1
def chatbot_fijo(state: State) -> dict:
    print("Generando una respuesta fija")
    
    # Escribimos a mano la respuesta fija simulando ser el soporte técnico
    respuesta_estatica = AIMessage(
        content="Hola, soy el asistente de soporte técnico en modo de RESPUESTA FIJA. "
                "Todo funciona correctamente en el estado de grafo."
    )
    
    # Devolvemos la actualización del estado manteniendo los contadores limpios
    return {
        "messages": [respuesta_estatica],
        "tool_calls_count": state.get("tool_calls_count", 0),
        "errors": state.get("errors", [])
    }

# creacion del grafo con la clase StateGraph y el estado definido 
builder = StateGraph(State)

# Registramos la función 'chatbot_fijo' como nuestra casilla del mapa
builder.add_node("chatbot", chatbot_fijo)

# Añadimos las conexiones (Aristas fijas) start y end
builder.add_edge(START, "chatbot") 
builder.add_edge("chatbot", END)  

# Compilamos el grafo para que esté listo para ejecutarse
graph = builder.compile()


if __name__ == "__main__":
    print("ejecutando el grafo con respuesta fija desde la terminal")
 

    # Preparamos el estado inicial del grafo usando la pregunta del usuario
    estado_inicial = {
        "messages": [HumanMessage(content="Hola, ¿qué sabes hacer?")],
        "tool_calls_count": 0,
        "errors": []
    }

    # invocamos el grafo con el estado inicial y mostramos el resultado en la terminal
    resultado = graph.invoke(estado_inicial)
    
    print("\n Resultado obtenido en la pantalla:")
    print(resultado["messages"][-1].content)

    
