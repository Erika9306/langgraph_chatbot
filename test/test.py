
import sys
import os
from pathlib import Path


_ROOT = Path(__file__).resolve().parent.parent
if str(_ROOT) not in sys.path:
    sys.path.append(str(_ROOT))

from langgraph.graph import START, END
from langgraph.grafo import builder  

def ejecutar_test(nombre_test, estado_inicial):
    print(f"\n Ejecutando: {nombre_test}")
    print(f" Contador Tools: {estado_inicial.get('tool_calls_count', 0)}")
    
    # Compilamos el grafo para que esté listo para ejecutarse
    graph_test = builder.compile()
    
    try:
        # Probamos directamente el enrutador continuar pasando el estado simulado
        # Esto verifica los límites y fallos de forma local y gratuita
        from langgraph.chatbot import continuar
        proximo_paso = continuar(estado_inicial)
        print(f" Decisión del Enrutador: El grafo irá hacia -> [{proximo_paso}]")
        
        if proximo_paso == "__end__":
            print(" ÉXITO: El flujo terminó de forma controlada sin caer en bucles.")
        else:
            print(" INFO: El flujo requiere pasar por el nodo de herramientas.")
            
    except Exception as e:
        print(f" FALLO CAPTURADO: {str(e)}")

if __name__ == "__main__":
    print("Simulador de pruebas de flujo y límites del grafo de soporte técnico.")
   

    # COMPROBACIÓN: Agotamiento del límite de llamadas a herramientas
    # Simulamos que el bot ya ha llamado 2 veces a las herramientas en este turno
    from langchain_core.messages import AIMessage
    msg_con_tool_call = AIMessage(content="Necesito usar una herramienta", tool_calls=[{"name": "consultar_ticket", "args": {"ticket_id": "T-100"}, "id": "1"}])
    
    estado_limite_agotado = {
        "messages": [msg_con_tool_call],
        "tool_calls_count": 2,  
        "errors": []
    }
    ejecutar_test("Test de Agotamiento del Límite (Contador >= 2)", estado_limite_agotado)

    # Argumentos Inválidos 
    print("\n Ejecutando: Test de Argumentos Inválidos en Herramientas")
    from app.soporte.tools import consultar_ticket, buscar_articulo
    
    res_ticket_invalido = consultar_ticket.invoke({"ticket_id": "T-999"})
    print(f" Enviando ID inexistente 'T-999' a consultar_ticket...")
    print(f" Respuesta de la herramienta: {res_ticket_invalido}")
    if "Error" in res_ticket_invalido or "no existe" in res_ticket_invalido:
        print(" ÉXITO: La herramienta capturó el argumento inválido de forma controlada sin romperse.")

    res_articulo_invalido = buscar_articulo.invoke({"articulo_id": "A-99"})
    print(f" Enviando ID inexistente 'A-99' a buscar_articulo...")
    print(f" Respuesta de la herramienta: {res_articulo_invalido}")
    if "Error" in res_articulo_invalido or "no existe" in res_articulo_invalido:
        print(" ÉXITO: La herramienta capturó el artículo inválido de forma controlada.")
