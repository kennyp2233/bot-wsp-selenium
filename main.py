import time
import asyncio
from config import get_driver
from wsp_utils import get_last_contacts_from_messages, select_contact, send_message, read_last_message
from db_utils import get_user_state, save_user_state
from huggingface_utils import get_bot_response
import re
# Configura el navegador
driver = get_driver()

# Número(s) autorizado(s) para pausar o reanudar el bot
AUTHORIZED_NUMBERS = {"+1234567890"}  # Reemplaza con tu número o el número autorizado

# Estado del bot
bot_state = "ACTIVO"  # Puedes inicializar esto desde la base de datos si es necesario

async def process_message(message, user, is_outbound):
    """Procesa el mensaje recibido del usuario o enviado por el bot."""
    global bot_state
    user_state = await get_user_state(user)
    print(f"Processing {'outbound' if is_outbound else 'inbound'} message from {user}: {message}")
    print(f"--------------------------MODO DEL USUARIO: {user_state}--------------------------")
    print(f"Current bot state: {bot_state}")

    if is_outbound:
        if message.strip().upper() == "ATIENDO":
            await save_user_state(user, "ATENDIDO")
            print(f"User {user} is now being attended to.")
            return "Un agente humano está atendiendo ahora. El bot no intervendrá."
        return None  # No procesar otros mensajes salientes

    if user in AUTHORIZED_NUMBERS:  # Número(s) autorizado(s) para controlar el bot
        if message.lower().strip() == "pausar bot":
            bot_state = "PAUSADO"
            await save_user_state(user, "PAUSADO")
            print(f"Bot paused by user {user}.")
            return "El bot ha sido pausado."
        
        if message.lower().strip() == "reanudar bot":
            bot_state = "ACTIVO"
            await save_user_state(user, "ACTIVO")
            print(f"Bot resumed by user {user}.")
            return "El bot ha sido reanudado."

    if bot_state == "ACTIVO":
        message = re.sub(r'\s*\d{2}:\d{2}$', '', message).strip()
        normalized_message = message.lower().strip()
        print(f"!!!!!!!!!!!!!!!!!!!!!!!Normalized message: '{normalized_message}'")
        print(f"User state for comparison: '{user_state}'")
        
        if normalized_message == "reservar":
            print("Message matches 'reservar'")
            await save_user_state(user, "RESERVAR")
            print(f"||||||||||||||||||||||||||||||||||||||User {user} is in reservation mode.")
            return "Estás en modo reserva. Un agente te contactará pronto."
        elif normalized_message == "hola bot":
            print("Message matches 'hola bot'")
            await save_user_state(user, "HOLA BOT")
            return "Ahora estás en modo bot. ¿En qué puedo ayudarte?"

        if user_state == "RESERVAR":
            print("User state matches 'RESERVAR'")
            return "Estás en modo reserva. Un agente te contactará pronto."
        
        if user_state == "ATENDIDO":
            print("User is being attended by a human agent.")
            return None  # El bot no responde, pero sí procesa el mensaje
        
        response = await get_bot_response(message, user_state)
        print(f"Bot response: {response}")
        return response
    
    return None

async def main_loop():
    """Ciclo principal del bot."""
    while True:
        try:
            print("Retrieving contacts...")
            contacts = get_last_contacts_from_messages(driver, max_contacts=2)
            print(f"Contacts retrieved: {contacts}")
            
            if not contacts:
                print("No contacts found.")
            
            for contact_name in contacts:
                print(f"Selecting contact: {contact_name}")
                select_contact(driver, contact_name)
                print(f"Reading last message for contact: {contact_name}")
                last_message, is_outbound = read_last_message(driver)
                
                if last_message:
                    print(f"Last message from {contact_name}: {last_message}")
                    print(f"Is outbound: {is_outbound}")

                    response = await process_message(last_message, contact_name, is_outbound)
                    
                    if response is not None:  # Envía la respuesta solo si no es None
                        print(f"Sending response to {contact_name}: {response}")
                        send_message(driver, response)
                    else:
                        print(f"No response sent to {contact_name}.")
                else:
                    print(f"No new message to process for contact: {contact_name}")
                    
        except Exception as e:
            print(f"Error: {e}")
            driver.save_screenshot('error_screenshot.png')  # Opcional: Toma una captura de pantalla en caso de error
        
        await asyncio.sleep(5)  # Usa asyncio.sleep en lugar de time.sleep en funciones async

# Ejecuta el loop asincrónico
asyncio.run(main_loop())