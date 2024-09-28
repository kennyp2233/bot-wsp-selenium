import os
import re
import asyncio
import logging
from datetime import datetime
from selenium.common.exceptions import NoSuchElementException, TimeoutException, WebDriverException
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait

from config import get_driver
from wsp_utils import (
    get_last_contacts_from_messages,
    select_contact,
    send_message,
    read_last_message
)
from db_utils import get_user_state, save_user_state
from huggingface_utils import get_bot_response

# Configuración del logging
logging.basicConfig(
    filename='bot_log.log',
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

# Configuraciones y constantes
AUTHORIZED_NUMBERS = {"+593 98 237 2511", "betzili gomez"}
BOT_ACTIVE_STATE = "ACTIVO"
BOT_PAUSED_STATE = "PAUSADO"
MAX_CONTACTS = 2
CHECK_INTERVAL = 4  # segundos

class WhatsAppBot:
    def __init__(self):
        self.driver = get_driver()
        self.bot_state = BOT_ACTIVE_STATE

    async def process_message(self, message, user, is_outbound):
        """Procesa el mensaje recibido del usuario o enviado por el bot."""
        message = re.sub(r'\s*\d{2}:\d{2}$', '', message).strip()
        normalized_message = message.lower().strip()
        user_state = await get_user_state(user)
        logging.info(f"Processing {'outbound' if is_outbound else 'inbound'} message from {user}: {message}")
        logging.info(f"User state: {user_state}, Bot state: {self.bot_state}")

        if is_outbound:
            if normalized_message.upper() == "ATIENDO":
                await save_user_state(user, "ATENDIDO")
                logging.info(f"User {user} is now being attended to.")
                return "Un agente humano está atendiendo ahora. El bot no intervendrá."
            return None  # No procesar otros mensajes salientes

        if user in AUTHORIZED_NUMBERS:
            if normalized_message == "pausar bot":
                self.bot_state = BOT_PAUSED_STATE
                await save_user_state(user, BOT_PAUSED_STATE)
                logging.info(f"Bot paused by user {user}.")
                return "El bot ha sido pausado."

            if normalized_message == "reanudar bot":
                self.bot_state = BOT_ACTIVE_STATE
                await save_user_state(user, BOT_ACTIVE_STATE)
                logging.info(f"Bot resumed by user {user}.")
                return "El bot ha sido reanudado."

        if self.bot_state == BOT_ACTIVE_STATE:
            if normalized_message == "reservar":
                await save_user_state(user, "RESERVAR")
                logging.info(f"User {user} is in reservation mode.")
                return "Estás en modo reserva. Un agente te contactará pronto."
            elif normalized_message == "hola bot":
                await save_user_state(user, "HOLA BOT")
                return "Ahora estás en modo bot. ¿En qué puedo ayudarte?"

            if user_state == "RESERVAR":
                return ("Estás en modo reserva. Un agente te contactará pronto. "
                        "Si deseas volver a hablar con el bot, escribe 'hola bot'.")

            if user_state == "ATENDIDO":
                logging.info(f"User {user} is being attended by a human agent.")
                return None  # El bot no responde, pero sí procesa el mensaje

            response = await get_bot_response(message, user)
            logging.info(f"Bot response to {user}: {response}")
            return response

        return None

    async def load_whatsapp_web(self):
        max_retries = 3
        retry_count = 0

        while retry_count < max_retries:
            try:
                logging.info("Loading WhatsApp Web...")
                self.driver.get('https://web.whatsapp.com/')
                # Espera hasta que el elemento sea visible
                WebDriverWait(self.driver, 20).until(
                    EC.visibility_of_element_located((By.CSS_SELECTOR, "div[contenteditable='true']"))
                )
                logging.info("WhatsApp Web loaded successfully.")
                return  # Éxito, salir de la función
            except (TimeoutException, WebDriverException) as e:
                logging.error(f"Error loading WhatsApp Web (attempt {retry_count + 1}): {e}")
                retry_count += 1

                if retry_count < max_retries:
                    logging.info("Retrying to load WhatsApp Web...")
                    await asyncio.sleep(5)  # Esperar antes de reintentar
                else:
                    logging.error("Max retries reached. Restarting browser.")
                    try:
                        self.driver.quit()
                        self.driver = get_driver()  # Re-inicializar el navegador
                    except Exception as restart_error:
                        logging.error(f"Error restarting browser: {restart_error}")
                        # Si no podemos reiniciar el navegador, esperamos un tiempo antes de continuar
                        await asyncio.sleep(60)

    async def close_details_panel(self):
        try:
            close_button = WebDriverWait(self.driver, 5).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, 'span[data-icon="x"], span[data-icon="x-alt"]'))
            )
            self.driver.execute_script("arguments[0].click();", close_button)
            logging.info("Details panel closed.")
        except Exception as e:
            logging.error(f"Error closing details panel: {e}")

    async def is_group_chat(self):
        try:
            logging.info("Checking if chat is a group...")
            header = WebDriverWait(self.driver, 10).until(
                EC.element_to_be_clickable((By.CSS_SELECTOR, 'header._amid._aqbz'))
            )
            header.click()


            WebDriverWait(self.driver, 5).until(
                EC.visibility_of_element_located((By.CSS_SELECTOR, 'span.x1jchvi3.x1fcty0u.x40yjcy'))
            )

            group_element = self.driver.find_element(By.CSS_SELECTOR, 'span.x1jchvi3.x1fcty0u.x40yjcy')
            group_text = group_element.text            
            await self.close_details_panel()
            return "Grupo" in group_text or "miembros" in group_text
        except Exception as e:
            logging.error(f"Error determining if chat is group: {e}")
            await self.close_details_panel()
            return False

    async def main_loop(self):
        """Ciclo principal del bot."""
        while True:
            try:
                logging.info("Retrieving contacts...")
                contacts = get_last_contacts_from_messages(self.driver, max_contacts=MAX_CONTACTS)
                logging.info(f"Contacts retrieved: {contacts}")

                if not contacts:
                    logging.info("No contacts found.")

                for contact_name in contacts:
                    self.driver.find_element(By.TAG_NAME, 'body').send_keys(Keys.ESCAPE)
                    logging.info(f"Selecting contact: {contact_name}")
                    select_contact(self.driver, contact_name)
                    logging.info(f"Reading last message for contact: {contact_name}")

                    is_group = await self.is_group_chat()
                    if is_group:
                        logging.info(f"Contact {contact_name} is a group chat. Skipping...")
                        continue

                    last_message, is_outbound = read_last_message(self.driver)

                    if last_message:
                        logging.info(f"Last message from {contact_name}: {last_message} (Outbound: {is_outbound})")
                        response = await self.process_message(last_message, contact_name, is_outbound)

                        if response is not None:
                            logging.info(f"Sending response to {contact_name}: {response}")
                            send_message(self.driver, response)
                        else:
                            logging.info(f"No response sent to {contact_name}.")
                    else:
                        logging.info(f"No new message to process for contact: {contact_name}")

            except Exception as e:
                logging.error(f"Error in main loop: {e}")
                self.driver.save_screenshot('error_screenshot.png')
                await self.load_whatsapp_web()

            await asyncio.sleep(CHECK_INTERVAL)

# Ejecuta el loop asincrónico
if __name__ == "__main__":
    bot = WhatsAppBot()
    asyncio.run(bot.main_loop())
