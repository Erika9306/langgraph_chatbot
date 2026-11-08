import argparse
from langchain_core.messages import HumanMessage
from langgraph.checkpoint.sqlite import SqliteSaver

# Importamos el grafo
from langgraph.grafo import builder

def main(chatbot_only=False, memory=True):
    
    parser = argparse.ArgumentParser(description="CLI Básico de Soporte")
    
    # Definimos qué parámetros va a entender la terminal
    parser.add_argument("--pregunta", default="Hola, ¿qué puedes hacer?", help="Tu consulta")
    
    
    # Guardamos lo que el usuario ha escrito en la terminal
    args = parser.parse_args()

    # Preparamos el estado inicial del grafo usando la pregunta del usuario
    estado_inicial = {
        "messages": [HumanMessage(content=args.pregunta)],
        "tool_calls_count": 0,
        "errors": []
    }

    # Control de Memoria Persistente con SQLite 
    if memory:
        # Se genera de forma automática un archivo de base de datos local
        checkpointer = SqliteSaver.from_conn_string("soporte_memoria.db")
        graph = builder.compile(checkpointer=checkpointer)
        config = {"configurable": {"thread_id": args.hilo}}
    else:
        # Si la etapa lo deshabilita (memory=False), corre de forma efímera en RAM
        graph = builder.compile()
        config = None

    # 6. Ejecutamos el grafo pasándole el estado y su configuración
    resultado = graph.invoke(estado_inicial, config)

    # 7. Mostramos el resultado final por la terminal
    print("\n Respuesta del Agente:")
    print(resultado["messages"][-1].content)
