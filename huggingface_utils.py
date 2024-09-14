from huggingface_hub import InferenceClient
from db_utils import get_user_state
import re
from collections import defaultdict, deque

# Diccionario para almacenar el historial de mensajes por usuario
chat_history = defaultdict(lambda: deque(maxlen=10))

def replace_non_bmp_emojis(text):
    # Reemplaza emojis fuera del BMP con una versión segura o los elimina
    return re.sub(r'[\U00010000-\U0010FFFF]', '', text)

def update_chat_history(user_id, message):
    chat_history[user_id].append(message)
    print(f"Updated chat history for {user_id}: {chat_history[user_id]}")


# Configura el cliente de Hugging Face
client = InferenceClient(
    model="meta-llama/Meta-Llama-3-8B-Instruct",
    token="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"  # Reemplaza con tu token real
)

async def get_bot_response(message, user_id):
    
    response_text = ""

    # Verifica el estado del usuario desde la base de datos
    user_state = get_user_state(user_id)

    if user_state != "RESERVAR":
        history = list(chat_history[user_id])  # Obtiene el historial de mensajes
        system_message = """
        🌟 **Bienvenido a Gallery Spa** 🌟

        Ofrecemos servicios de bienestar:

        1. **Masajes**:
           - Relajante 💆‍♂️: $30/hora.
           - Deportivo 🏋️‍♂️: $35/hora.
           - Espalda + jacuzzi 🛁: $35/hora.
           - Chocolate Spa 🍫: $60/2.5h (o $100 para dos).

        2. **Taller Cierre de Costillas Colombiano** 🎓:
           - Incluye: cierre de costillas, vaciado de colon, maderoterapia, introducción a aparatología estética.
           - Valor: $50.
           - Comienza la primera semana de septiembre.

        3. **Cauterización de Lunares y Verrugas** 🩺:
           - Desde $5.
           - Incluye consulta inicial y seguimiento.

        4. **Lipo sin Cirugía**:
           - Intralipoterapia, sin bisturí ni anestesia general.
           - PROMOCIÓN: $120 por sesión en 4 zonas (incluye drenajes, no incluye faja).
           - Puedes pagar con tarjeta, efectivo o transferencia.

        5. **Rejuvenecimiento con Plasma Rico en Plaquetas** 🩸:
           - Incluye limpieza facial, dermaplaning, dermaroller, anestesia en crema, aplicación de plasma, máscara LED.
           - Valor: $60/sesión o $140/3 sesiones.

        6. **Botox** 💉:
           - Refresca y rejuvenece hasta 10 años.
           - Valor: $250 (promoción $230 si reservas hoy).
           - Incluye retoque a los 8 días y limpieza facial.

        **Ubicación**: Valle de los Chillos.
        **Horario Comercial**:
        - Lunes a Viernes: 08:30–19:00
        - Sábado: 08:30–14:30
        - Domingo: Cerrado

        **Reserva o consultas**: Escribe "RESERVAR" para que un agente se comunique contigo. Si tienes alguna duda o deseas información adicional, simplemente di "Hola bot".

        📍 [Ubicación en Google Maps](https://maps.google.com/maps/search/Gallery%20Spa.%20Centro%20de%20Est%C3%A9tica%20y%20Salud/@-0.3166,-78.4652,17z?hl=es)
        """

        # Agrega el historial y el mensaje actual
        messages = [
            {"role": "system", "content": system_message},
            *[{"role": "user", "content": msg} for msg in history],
            {"role": "user", "content": message}
        ]
        try:
            response = client.chat_completion(
                messages=messages,
                max_tokens=500
            )
            response_text = replace_non_bmp_emojis(response['choices'][0]['message']['content'])
            update_chat_history(user_id, message)
        except Exception as e:
            print(f"Error al enviar la solicitud: {e}")
            response_text = "Error: La solicitud falló."
       

    return response_text
