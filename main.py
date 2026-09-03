import requests
import json
import os
import google.generativeai as genai

# Configuración desde variables del entorno
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
DISCORD_WEBHOOK_URL = os.getenv("DISCORD_WEBHOOK_URL")

# API pública de Pet Simulator 99
PS99_API_URL = "https://ps99.biggamesapi.io/api/collection/pets"

def enviar_alerta_discord(mensaje):
    """Envía un mensaje a tu canal de Discord."""
    payload = {"content": mensaje}
    try:
        requests.post(DISCORD_WEBHOOK_URL, json=payload)
    except Exception as e:
        print(f"Error enviando a Discord: {e}")

def obtener_datos_mercado():
    """Descarga los datos completos de mascotas de PS99."""
    try:
        response = requests.get(PS99_API_URL)
        if response.status_code == 200:
            return response.json().get("data", [])
    except Exception as e:
        print(f"Error obteniendo mercado: {e}")
    return []

def analizar_con_ia(datos_mercado):
    """Filtra y envía el mercado completo a Gemini para encontrar ofertas."""
    # Filtramos mascotas relevantes (con RAP y Existencias registradas) para no sobrecargar
    mascotas_interesantes = []
    for item in datos_mercado:
        rap = item.get("rap", 0)
        exists = item.get("exists", 0)
        name = item.get("configName", "Desconocido")
        category = item.get("category", "")
        
        # Consideramos únicamente mascotas con cierto valor
        if rap > 10_000_000:
            mascotas_interesantes.append({
                "nombre": name,
                "categoria": category,
                "rap": rap,
                "existencias": exists
            })
    
    # Si no hay datos suficientes
    if not mascotas_interesantes:
        return "No se encontraron mascotas con valor alto registrado en este momento."

    # Configurar la API de Gemini
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

def ejecucion_principal():
    print("Iniciando escaneo del mercado PS99...")
    datos = obtener_datos_mercado()
    if datos:
        analisis = analizar_con_ia(datos)
        enviar_alerta_discord(f"📊 **Informe de Mercado PS99 - Analista IA**\n\n{analisis}")
        print("Informe enviado a Discord con éxito.")
    else:
        print("No se pudieron obtener datos del mercado.")

if __name__ == "__main__":
    ejecucion_principal()
