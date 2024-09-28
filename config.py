from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from selenium.common.exceptions import TimeoutException, NoSuchElementException

def get_driver():
    # Configura opciones del navegador
    chrome_options = Options()

    chrome_options.add_argument("--headless=new") # Comenta esta línea para ver el navegador
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-gpu")  # Deshabilita la aceleración por GPU
    chrome_options.add_argument("--disable-extensions")  # Deshabilita las extensiones
    chrome_options.add_argument("--disable-dev-shm-usage")
    
    chrome_options.add_argument("--user-data-dir=C:/Users/kenny/AppData/Local/Google/Chrome/User Data")
    chrome_options.add_argument("--profile-directory=Default")
    
    chrome_options.add_argument("--disable-logging")
    chrome_options.add_argument("--log-level=3")  # Minimiza los logs
    
    chrome_options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                                "AppleWebKit/537.36 (KHTML, like Gecko) "
                                "Chrome/115.0.0.0 Safari/537.36")
    
    prefs = {"profile.managed_default_content_settings.images": 2}
    chrome_options.add_experimental_option("prefs", prefs)
    
    # Inicializa el controlador de Chrome
    driver_path = 'C:/Users/kenny/Downloads/chromedriver-win64/chromedriver-win64/chromedriver.exe'
    service = Service(driver_path)
    service.log_path = 'chromedriver.log'
    service.log_level = 'DEBUG'
    driver = webdriver.Chrome(service=service, options=chrome_options)

    try:
        # Abre la página
        driver.get('https://web.whatsapp.com/')

        # Espera hasta que el elemento sea visible
        try:
            element = WebDriverWait(driver, 20).until(
                EC.visibility_of_element_located((By.CSS_SELECTOR, "div[contenteditable='true']"))
            )
            print("Elemento encontrado y visible")
        except TimeoutException:
            print("Tiempo de espera agotado: El elemento no está visible")
            raise TimeoutException
        except NoSuchElementException:
            print("No se pudo encontrar el elemento con el selector proporcionado")
            raise NoSuchElementException

        # Tomar una captura de pantalla
        driver.save_screenshot('screenshot.png')
        print("Captura de pantalla tomada")

    except Exception as e:
        print(f"An error occurred: {e}")
        try:
            driver.refresh()
            print("Page refreshed.")
            WebDriverWait(driver, 20).until(
                EC.visibility_of_element_located((By.CSS_SELECTOR, "div[contenteditable='true']"))
            )
        except Exception as refresh_error:
            print(f"Error refreshing page: {refresh_error}")
            
            # If refresh fails, restart the browser
            try:
                driver.quit()
                driver = get_driver()  # Re-initialize the browser
                print("Browser restarted.")
            except Exception as restart_error:
                print(f"Error restarting browser: {restart_error}")



    return driver