import requests
import json
import os
import threading
from http.server import HTTPServer, BaseHTTPRequestHandler
import discord
from discord.ext import commands
import google.generativeai as genai

# 1. Servidor web liviano en segundo plano para engañar a Render
class DummyServer(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b"Bot activo")

def run_dummy_server():
    port = int(os.environ.get("PORT", 8080))
    server = HTTPServer(("0.0.0.0", port), DummyServer)
    server.serve_forever()

# Iniciar servidor web en un hilo secundario
threading.Thread(target=run_dummy_server, daemon=True).start()

# 2. Configuración de Gemini y Discord
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
DISCORD_BOT_TOKEN = os.getenv("DISCORD_BOT_TOKEN")
PS99_API_URL = "https://ps99.biggamesapi.io/api/collection/pets"

genai.configure(api_key=GEMINI_API_KEY)
model = genai.GenerativeModel('gemini-2.5-flash')

intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix="!", intents=intents)

def obtener_datos_mercado():
    try:
        response = requests.get(PS99_API_URL)
        if response.status_code == 200:
            return response.json().get("data", [])
    except Exception as e:
        print(f"Error obteniendo mercado: {e}")
    return []

@bot.event
async def on_ready():
    print(f'¡Bot conectado como {bot.user}!')

@bot.command(name="analizar")
async def analizar(ctx, *, consulta: str = None):
    await ctx.send("🔍 Escaneando el mercado de PS99 y consultando a la IA...")
    
    datos = obtener_datos_mercado()
    if not datos:
        await ctx.send("❌ No se pudieron obtener los datos de la API de PS99.")
        return

    mascotas = []
    for item in datos:
        rap = item.get("rap", 0)
        exists = item.get("exists", 0)
        name = item.get("configName", "Desconocido")
        if rap > 100_000:
            mascotas.append({"nombre": name, "rap": rap, "existencias": exists})

    prompt_base = f"""
    Eres un analista experto en la economía de Pet Simulator 99 en Roblox.
    Datos del mercado actual:
    {json.dumps(mascotas[:150], indent=2)}
    """

    if consulta:
        prompt = f"{prompt_base}\n\nEl usuario pregunta específicamente: '{consulta}'. Responde basándote en los datos con consejos prácticos de trading."
    else:
        prompt = f"{prompt_base}\n\nDame un resumen general del mercado: las 3 mejores oportunidades de compra y qué vender hoy."

    try:
        respuesta = model.generate_content(prompt)
        await ctx.send(f"📊 **Análisis del Mercado PS99**\n\n{respuesta.text[:1900]}")
    except Exception as e:
        await ctx.send(f"❌ Error al consultar la IA: {e}")

if __name__ == "__main__":
    bot.run(DISCORD_BOT_TOKEN)
