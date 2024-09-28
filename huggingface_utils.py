import os
import re
from collections import defaultdict
from gradio_client import Client  # Cambiado de InferenceClient a gradio_client.Client
from db_utils import get_user_state
import asyncio
import traceback
# Configuración y constantes
TOKEN = "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"  # Asegúrate de mantener tu token seguro
MODEL_NAME = "Qwen/Qwen2.5-72B-Instruct"
MAX_HISTORY_LENGTH = 5

# Inicialización del cliente de Gradio
client = Client(MODEL_NAME)

# Mensaje del sistema (puedes moverlo a un archivo separado si es muy largo)
SYSTEM_MESSAGE = """
🌟 **Bienvenido a Gallery Spa** 🌟

**Servicios de Bienestar:**

1. **Masajes**:
   - **Relajante** 💆‍♂️: $30/hora
   - **Deportivo** 🏋️‍♂️: $35/hora
   - **Espalda + Jacuzzi** 🛁: $35/hora
   - **Chocolate Spa** 🍫: $60 (2.5 horas) / $100 (para dos personas)

2. **Tratamiento Cierre de Costillas Colombiano** 🎓:
   - **Beneficios**:
     - Reduce medidas en espalda y cintura
     - Mejora la postura
     - Acelera digestión y metabolismo
   - **Precio**: $50/sesión
   - **Promoción**: 8 sesiones por $160
   - **Incluye**:
     - Maderoterapia
     - Cierre de Costillas Colombiano
     - Vacunoterapia
     - Electrodos
     - Ultracavitación
     - Lipo láser
   - **Nota**: Faja no incluida ($45 - $100 según modelo)

3. **Cauterización de Lunares y Verrugas** 🩺:
   - **Precio**: Desde $5, según evaluación médica
   - **Opciones**:
     - Envío de foto para presupuesto aproximado
     - Agendar cita con especialista
   - **Incluye**: Consulta inicial y seguimiento

4. **Lipo sin Cirugía**:
   - **Intralipoterapia**: Sin bisturí ni anestesia general
   - **Promoción**: $120/sesión (4 zonas)
   - **Incluye**: Drenajes
   - **Pago**: Tarjeta, efectivo, transferencia
   - **Nota**: Faja no incluida ($45 - $100 según modelo)

5. **Rejuvenecimiento con Plasma Rico en Plaquetas** 🩸:
   - **Incluye**:
     - Limpieza facial
     - Dermaplaning
     - Dermaroller
     - Anestesia en crema
     - Aplicación de plasma
     - Máscara LED
   - **Precio**:
     - $60/sesión
     - $140 por 3 sesiones

6. **Botox** 💉:
   - **Beneficios**: Refresca y rejuvenece hasta 10 años
   - **Precio**:
     - $250
     - **Promoción**: $230 si reservas hoy
   - **Incluye**:
     - Retoque a los 8 días
     - Limpieza facial

7. **Limpiezas Faciales**:
   - **Profunda** ($45):
     - Limpieza, exfoliación, tónico, contorno, extracción
     - Ácido según tipo de piel, alta frecuencia, punta de diamante
     - Mascarilla y máscara LED
   - **Profunda con Plasma Rico en Plaquetas** ($60):
     - Todos los pasos de la limpieza profunda
     - Plasma rico con vitamina C (jeringa o dermaroller)
   - **Junior** ($25):
     - Jabón espumoso, exfoliante suave, tónico suave
     - Mascarillas de arcilla suave y rosada, máscara LED
     - Ideal para piel sensible y tercera edad

**Ubicación**: Valle de los Chillos, sector de Capelo

**Horario Comercial**:
- **Lunes a Viernes**: 08:30–19:00
- **Sábado**: 08:30–14:30
- **Domingo**: Cerrado

**Reserva o Consultas**:
- Escribe **"RESERVAR"** para contactar con un agente.
- Para dudas o más información, escribe **"Hola bot"**.

📍 [Ubicación en Google Maps](https://maps.google.com/maps/search/Gallery%20Spa.%20Centro%20de%20Est%C3%A9tica%20y%20Salud/@-0.3166,-78.4652,17z?hl=es)
**Info bancaria**:/Banco Pichincha. Cuenta de Ahorros: 2208535833. Betzili Gomez Silva. Cédula 1761295243
---

**Instrucciones para el Bot**:

- **Precisión en la Información**:
  - Proporciona únicamente la información presente en este documento.
  - **No inventes** detalles adicionales como nombres, fechas, promociones no mencionadas o eventos personales.

- **Respuesta Específica a Consultas**:
  - Si el usuario pregunta sobre un servicio específico, proporciona información detallada solo sobre ese servicio.
  - **No mezcles** información de diferentes tratamientos o promociones.

- **Manejo de Información Desconocida**:
  - Si la consulta **no está relacionada** con los servicios ofrecidos, responde únicamente:
    - "Lo siento, no tengo información sobre eso. Por favor, escribe **'RESERVAR'** para que un agente se comunique contigo."
  - **No proporciones** información adicional ni especulativa fuera del contexto proporcionado.

- **Comunicación Clara y Concisa**:
  - Evita divagar o proporcionar información irrelevante.
  - Mantén las respuestas enfocadas y directamente relacionadas con las preguntas del usuario.

- **Lenguaje Profesional y Amable**:
  - Utiliza un tono cordial y profesional en todas las interacciones. Usa emojis con moderación y en contexto.
  - Evita suposiciones sobre el estado personal del usuario (por ejemplo, no asumir que está de cumpleaños).

---
"""

# Diccionario para almacenar el historial de mensajes por usuario
chat_history = defaultdict(list)

def update_chat_history(user_id, history):
    """
    Actualiza el historial de chat con el historial proporcionado.
    """
    chat_history[user_id] = history[-MAX_HISTORY_LENGTH:]
    print(f"Historial actualizado para {user_id}: {chat_history[user_id]}")

async def get_bot_response(user_message, user_id):
    """
    Procesa el mensaje del usuario y devuelve la respuesta del bot utilizando la API de Gradio.
    """
    try:
        # Prepara los parámetros para el endpoint /model_chat
        history = chat_history[user_id]  # Ya está en el formato correcto
        params = {
            "query": user_message,
            "history": history,
            "system": SYSTEM_MESSAGE,
            "api_name": "/model_chat"
        }

        # Llama al endpoint /model_chat
        result = client.predict(**params)
        print(f"Resultado de la solicitud: {result}")

        # 'result' es una tupla: (cadena_vacía, historial_actualizado, mensaje_sistema)
        updated_history = result[1]  # Extraemos el historial actualizado
        assistant_message = updated_history[-1][1]  # Última respuesta del asistente

        # Actualiza el historial de chat con el historial actualizado
        update_chat_history(user_id, updated_history)

        return assistant_message.strip()  # Asegúrate de que sea una cadena limpia

    except Exception as e:
        # Manejo de errores y retroalimentación al usuario
        print(f"Error al enviar la solicitud: {e}")
      
async def clear_session(user_id):
    """
    Limpia la sesión del usuario utilizando el endpoint /clear_session.
    """
    try:
        params = {
            "api_name": "/clear_session"
        }
        result = client.predict(**params)
        # Limpia el historial localmente
        chat_history[user_id] = []
        print(f"Sesión limpiada para {user_id}")
        return "Sesión limpiada exitosamente."
    except Exception as e:
        print(f"Error al limpiar la sesión: {e}")
        return "No se pudo limpiar la sesión."

async def modify_system_session(new_system_message):
    """
    Modifica el mensaje del sistema utilizando el endpoint /modify_system_session.
    """
    try:
        params = {
            "system": new_system_message,
            "api_name": "/modify_system_session"
        }
        result = client.predict(**params)
        global SYSTEM_MESSAGE
        SYSTEM_MESSAGE = new_system_message  # Actualiza el mensaje del sistema localmente
        print("Mensaje del sistema modificado.")
        return "Mensaje del sistema modificado exitosamente."
    except Exception as e:
        print(f"Error al modificar el mensaje del sistema: {e}")
        return "No se pudo modificar el mensaje del sistema."

async def main():
    try:
        # Prueba de la función get_bot_response
        user_message = """
       Me quiero sacar un lunar
        """
        user_id = "123456"
        respuesta = await get_bot_response(user_message, user_id)
        print(f"Respuesta del bot: {respuesta}")

        # Opcional: Prueba de limpiar la sesión
        # clear_response = await clear_session(user_id)
        # print(clear_response)

        # Opcional: Prueba de modificar el mensaje del sistema
        # new_system = "Eres un asistente actualizado para Gallery Spa."
        # modify_response = await modify_system_session(new_system)
        # print(modify_response)

    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    asyncio.run(main())
