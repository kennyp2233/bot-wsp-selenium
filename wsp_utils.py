from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.common.keys import Keys  # Add this import
import time
from datetime import datetime
import re

def scroll_into_view(driver, element):
    driver.execute_script("arguments[0].scrollIntoView(true);", element)

def parse_time(time_string):
    # Lista de formatos posibles
    formats = ["%I:%M %p", "%H:%M"]
    for fmt in formats:
        try:
            time_obj = datetime.strptime(time_string, fmt)
            return time_obj.hour * 60 + time_obj.minute  # Convierte a minutos
        except ValueError:
            continue
    return -1  # Valor por defecto en caso de error de parsing

def get_last_contacts_from_messages(driver, max_contacts=10):
    contacts = []
    
    try:
        # Encuentra el contenedor de chats
        print("Esperando que el contenedor de chats sea visible...")
        chat_list = WebDriverWait(driver, 20).until(
            EC.visibility_of_element_located((By.CSS_SELECTOR, 'div[aria-label="Lista de chats"]'))
        )
        print("Contenedor de chats encontrado y visible.")
        
        # Encuentra todos los elementos de chat dentro del contenedor
        chat_elements = chat_list.find_elements(By.CSS_SELECTOR, 'div[role="listitem"]')
        print(f"Se encontraron {len(chat_elements)} chats.")
        
        if len(chat_elements) == 0:
            print("No se encontraron elementos de chat dentro del contenedor.")
        
        contact_times = []

        for chat in chat_elements:
            try:
                # Obtener el nombre del contacto
                contact_name_element = chat.find_element(By.CSS_SELECTOR, 'span[dir="auto"]')
                contact_name = contact_name_element.text
                
                # Obtener la hora del último mensaje
                time_element = chat.find_element(By.CSS_SELECTOR, 'div._ak8i')  # Ajusta el selector según tu estructura HTML
                time_text = time_element.text.strip()
                contact_time = parse_time(time_text)
                
                if contact_time != -1:  # Solo incluir si el tiempo es válido
                    contact_times.append((contact_name, contact_time))
                    print(f"Contacto encontrado: {contact_name} a las {time_text}")
                else:
                    print(f"Hora no válida para el contacto: {contact_name}")

            except Exception as e:
                print(f"Error al obtener el nombre del contacto o la hora del mensaje: {e}")

        # Ordena los contactos por la hora del último mensaje en orden descendente
        contact_times.sort(key=lambda x: x[1], reverse=True)

        # Extrae solo los nombres de los contactos más recientes
        contacts = [contact_name for contact_name, _ in contact_times[:max_contacts]]
        print("Contactos ordenados por hora del último mensaje:", contact_times)
    
    except Exception as e:
        print(f"Error al obtener los contactos: {e}")
    
    return contacts

def select_contact(driver, contact_name):
    try:
        print(f"Selecting contact: {contact_name}")

        # Encuentra el cuadro de búsqueda y limpia su contenido
        search_box = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "div[contenteditable='true']"))
        )
        search_box.clear()
        search_box.send_keys(contact_name)
        time.sleep(1)  # Espera a que los resultados de búsqueda se actualicen

        # Espera a que los resultados de búsqueda sean visibles
        search_results = WebDriverWait(driver, 10).until(
            EC.visibility_of_element_located((By.CSS_SELECTOR, "div[aria-label='Resultados de la búsqueda.']"))
        )

        # Encuentra el primer contacto en la lista de resultados
        first_contact = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.XPATH, "//div[@aria-label='Resultados de la búsqueda.']//div[@role='listitem'][1]"))
        )

        # Desplázate al primer contacto para asegurarte de que esté en el viewport
        driver.execute_script("arguments[0].scrollIntoView(true);", first_contact)
        time.sleep(0.5)  # Espera para asegurarte de que el desplazamiento haya terminado

        # Haz clic en el primer contacto
        first_contact.click()
        print(f"Contact {contact_name} selected.")

        # Espera a que el chat se cargue completamente
        WebDriverWait(driver, 20).until(
            EC.presence_of_element_located((By.XPATH, "//div[@aria-placeholder='Escribe un mensaje']"))  # Actualiza según el atributo aria o otro identificador específico
        )
        print(f"Chat for contact {contact_name} is now open.")

        # Opcional: Puedes agregar un pequeño retraso aquí para asegurarte de que todo esté completamente cargado
        time.sleep(0.5)

    except Exception as e:
        print(f"Error in select_contact: {e}")

        # Opcional: Toma una captura de pantalla para ayudar a depurar
        driver.save_screenshot('error_screenshot.png')




def clean_message(message):
    """Elimina las marcas de tiempo y otros elementos no deseados del mensaje."""
    # Elimina las marcas de tiempo al final del mensaje
    cleaned_message = re.sub(r'\s*\d{1,2}:\d{2}\s*(?:a\.m\.|p\.m\.)?\s*$', '', message, flags=re.IGNORECASE)
    # Elimina cualquier espacio en blanco extra al principio o al final
    cleaned_message = cleaned_message.strip()
    return cleaned_message

def is_outbound_message(message_element):
    """Determina si un mensaje es saliente (enviado por el bot)."""
    return "message-out" in message_element.get_attribute("class")

def read_last_message(driver):
    try:
        print("Reading last message...")
        # Selecciona todos los mensajes (entrantes y salientes)
        messages = WebDriverWait(driver, 10).until(
            EC.presence_of_all_elements_located((By.CSS_SELECTOR, "div.message-in, div.message-out"))
        )
        
        if messages:
            # Obtén el último mensaje
            last_message_element = messages[-1]
            last_message = last_message_element.text
            print(f"Last message (raw): {last_message}")
            
            # Limpia el mensaje
            cleaned_message = clean_message(last_message)
            print(f"Last message (cleaned): {cleaned_message}")
            
            # Determina si el mensaje es saliente
            is_outbound = is_outbound_message(last_message_element)
            print(f"Is outbound: {is_outbound}")

            try:
                close_button = WebDriverWait(driver, 5).until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, 'span[data-icon="x-alt"]'))
                )
                close_button.click()
                print("Close button clicked.")
            except Exception as e:
                print(f"Error in closing button: {e}")
            
            return cleaned_message, is_outbound
        else:
            print("No messages found.")
            return None, False
    
    except Exception as e:
        print(f"Error in read_last_message: {e}")
        return None, False
    

def send_message(driver, message):
    try:
        print(f"Sending message: {message}")

        # Encuentra la caja de mensajes usando el placeholder
        message_box = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.XPATH, "//div[@aria-placeholder='Escribe un mensaje']"))
        )

        # Asegúrate de que la caja de mensajes esté visible
        driver.execute_script("arguments[0].scrollIntoView(true);", message_box)
        time.sleep(1)  # Espera para asegurarte de que el desplazamiento haya terminado

        # Borra cualquier texto previo en el campo de mensajes (opcional)
        message_box.click()  # Click en el campo para enfocarlo
        message_box.send_keys(Keys.CONTROL + "a")  # Selecciona todo el texto
        message_box.send_keys(Keys.BACKSPACE)  # Borra el texto

        # Limpia el mensaje de marcas de tiempo
        message = clean_message(message)

        # Usa JavaScript para copiar el mensaje al portapapeles
        driver.execute_script("navigator.clipboard.writeText(arguments[0]);", message)

        # Pega el mensaje usando CTRL + V
        message_box.send_keys(Keys.CONTROL + "v")
        
        # Envía el mensaje final
        message_box.send_keys(Keys.RETURN)  # Utiliza RETURN para enviar el mensaje
        print("Message sent.")
    
    except Exception as e:
        print(f"Error in send_message: {e}")
        # Opcional: Toma una captura de pantalla para ayudar a depurar
        driver.save_screenshot('error_screenshot.png')

def clean_message(message):
    # Implementa aquí cualquier limpieza necesaria del mensaje
    return message.strip()