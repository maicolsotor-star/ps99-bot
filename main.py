import requests
import json
import os
import time
import threading
from flask import Flask
import google.generativeai as genai

# Crear app básica de Flask para Render (Plan Gratuito)
app = Flask(__name__)

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
DISCORD_WEBHOOK_URL = os.getenv("DISCORD_WEBHOOK_URL")
PS99_API_URL = "https://ps99.biggamesapi.io/api/collection/pets"

def enviar_alerta_discord(mensaje):
    payload = {"content": mensaje}
    try:
        requests.post(DISCORD_WEBHOOK_URL, json=payload)
    except Exception as e:
        print(f"Error enviando a Discord: {e}")

def obtener_datos_mercado():
    try:
        response = requests.get(PS99_API_URL)
        if response.status_code == 200:
            return response.json().get("data", [])
    except Exception as e:
        print(f"Error obteniendo mercado: {e}")
    return []

def analizar_con_ia(datos_mercado):
    mascotas_interesantes = []
    for item in datos_mercado:
        rap = item.get("rap", 0)
        exists = item.get("exists", 0)
        name = item.get("configName", "Desconocido")
        category = item.get("category", "")
        
        if rap > 10_000_000:
            mascotas_interesantes.append({
                "nombre": name,
                "categoria": category,
                "rap": rap,
                "existencias": exists
            })
    
    if not mascotas_interesantes:
        return "No se encontraron mascotas relevantes en este momento."

    genai.configure(api_key=GEMINI_API_KEY)
    model = genai.GenerativeModel('gemini-1.5-flash')

    prompt = f"""
    Eres un analista experto en la economía y trading de Pet Simulator 99 en Roblox.
    Analiza la lista de mascotas con su precio promedio reciente (RAP) y existencias totales en el juego:

    {json.dumps(mascotas_interesantes[:100], indent=2)}

    Tu objetivo:
    1. Identifica las 2 o 3 mejores oportunidades de compra/inversión (mascotas raras o con pocas existencias pero valor RAP atractivo).
    2. Da una breve recomendación de compra y precio de venta objetivo.
    3. Responde de forma muy concisa, clara y amigable en español con emoticones para Discord.
    """

    try:
        respuesta = model.generate_content(prompt)
        return respuesta.text
    except Exception as e:
        return f"Error procesando con Gemini: {e}"

def bucle_analisis():
    """Se ejecuta solo cada 2 horas en segundo plano."""
    while True:
        print("Iniciando escaneo del mercado PS99...")
        datos = obtener_datos_mercado()
        if datos:
            analisis = analizar_con_ia(datos)
            enviar_alerta_discord(f"📊 **Informe de Mercado PS99 - Analista IA**\n\n{analisis}")
            print("Informe enviado a Discord.")
        else:
            print("No se pudieron obtener datos.")
        
        # Esperar 2 horas (7200 segundos) antes de volver a analizar
        time.sleep(7200)

# Iniciar el hilo del bot de PS99
hilo = threading.Thread(target=bucle_analisis, daemon=True)
hilo.start()

@app.route('/')
def home():
    return "El Bot Analista de PS99 está funcionando 24/7 de forma gratuita."

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)
