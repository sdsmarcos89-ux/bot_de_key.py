import discord
import os
import json
import random
import string
import threading
from http.server import HTTPServer, BaseHTTPRequestHandler
from dotenv import load_dotenv

# --- SERVIDOR PARA O RENDER NÃO DORMIR ---
class HealthCheckHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b"Key Generator Bot Online")

def run_health_check():
    port = int(os.environ.get("PORT", 10000))
    server = HTTPServer(("0.0.0.0", port), HealthCheckHandler)
    server.serve_forever()

threading.Thread(target=run_health_check, daemon=True).start()
# ------------------------------------------

load_dotenv()
token = os.getenv("DISCORD_BOT_TOKEN")

DATABASE_FILE = "keys_database.json"

def load_db():
    if os.path.exists(DATABASE_FILE):
        with open(DATABASE_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return {"keys": {}}

def save_db(db):
    with open(DATABASE_FILE, "w", encoding="utf-8") as f:
        json.dump(db, f, indent=4, ensure_ascii=False)

def generate_key(prefix="ZASKZ"):
    # Gera uma key aleatória formato: ZASKZ-XXXX-XXXX-XXXX
    chars = string.ascii_uppercase + string.digits
    part1 = ''.join(random.choice(chars) for _ in range(4))
    part2 = ''.join(random.choice(chars) for _ in range(4))
    part3 = ''.join(random.choice(chars) for _ in range(4))
    return f"{prefix}-{part1}-{part2}-{part3}"

bot = discord.Bot()

# Grupo de comandos para Administradores
admin = bot.create_group("key", "Gerenciamento de chaves de produto")

@admin.command(name="gerar", description="Gera chaves aleatórias para um produto")
async def gerar(
    ctx: discord.ApplicationContext,
    produto: discord.Option(str, "Nome do produto"),
    quantidade: discord.Option(int, "Quantidade de chaves", default=1),
    prefixo: discord.Option(str, "Prefixo da key (ex: ZASKZ)", default="ZASKZ")
):
    if not ctx.author.guild_permissions.administrator:
        return await ctx.respond("❌ Apenas administradores podem gerar chaves.", ephemeral=True)
    
    db = load_db()
    novas_keys = []
    
    for _ in range(quantidade):
        key = generate_key(prefixo.upper())
        while key in db["keys"]: # Evita duplicatas
            key = generate_key(prefixo.upper())
        
        db["keys"][key] = {
            "produto": produto,
            "status": "disponivel",
            "gerada_por": str(ctx.author),
            "usada_por": None
        }
        novas_keys.append(key)
    
    save_db(db)
    
    keys_formatadas = "\n".join([f"`{k}`" for k in novas_keys])
    embed = discord.Embed(
        title="🆕 Novas Keys Geradas",
        description=f"**Produto:** {produto}\n**Quantidade:** {quantidade}\n\n**Chaves:**\n{keys_formatadas}",
        color=0x5865F2
    )
    await ctx.respond(embed=embed, ephemeral=True)

@admin.command(name="validar", description="Valida uma key enviada pelo cliente no ticket")
async def validar(
    ctx: discord.ApplicationContext,
    key_do_cliente: discord.Option(str, "Cole a key que o cliente enviou")
):
    if not ctx.author.guild_permissions.administrator:
        return await ctx.respond("❌ Apenas administradores podem validar chaves.", ephemeral=True)
    
    db = load_db()
    key = key_do_cliente.upper().strip()
    
    if key not in db["keys"]:
        return await ctx.respond(f"❌ **Key Inválida!** Esta chave não existe no sistema.", ephemeral=False)
    
    info = db["keys"][key]
    
    if info["status"] == "usada":
        return await ctx.respond(f"⚠️ **Key Já Utilizada!**\nEsta chave foi usada por <@{info['usada_por']}> para o produto **{info['produto']}**.", ephemeral=False)
    
    # Se chegou aqui, a key é válida e está disponível
    embed = discord.Embed(
        title="✅ Key Válida!",
        description=f"A chave `{key}` é legítima.\n\n**Produto:** {info['produto']}\n**Status:** Disponível para liberação.",
        color=discord.Color.green()
    )
    
    # Botão para "Queimar" a key (marcar como usada)
    class ConfirmUse(discord.ui.View):
        @discord.ui.button(label="Liberar Produto e Queimar Key", style=discord.ButtonStyle.danger)
        async def confirm(self, button: discord.ui.Button, interaction: discord.Interaction):
            info["status"] = "usada"
            info["usada_por"] = str(ctx.author.id) # Registra quem validou no ticket
            save_db(db)
            await interaction.response.edit_message(content=f"✅ **Produto Liberado!** A key `{key}` foi marcada como usada e não pode mais ser validada.", embed=None, view=None)

    await ctx.respond(embed=embed, view=ConfirmUse())

@admin.command(name="estoque", description="Lista todas as chaves disponíveis")
async def estoque(ctx: discord.ApplicationContext):
    if not ctx.author.guild_permissions.administrator:
        return await ctx.respond("❌ Acesso negado.", ephemeral=True)
    
    db = load_db()
    disponiveis = [f"`{k}` | {v['produto']}" for k, v in db["keys"].items() if v["status"] == "disponivel"]
    
    if not disponiveis:
        return await ctx.respond("📭 Não há chaves disponíveis no estoque.", ephemeral=True)
    
    lista = "\n".join(disponiveis)
    if len(lista) > 2000: lista = lista[:1900] + "\n... (lista muito longa)"
    
    embed = discord.Embed(title="📦 Estoque de Keys Disponíveis", description=lista, color=0x5865F2)
    await ctx.respond(embed=embed, ephemeral=True)

@bot.event
async def on_ready():
    print(f"✅ Key Generator para Tickets Online: {bot.user}")

if token:
    bot.run(token)
else:
    print("❌ Erro: DISCORD_BOT_TOKEN não encontrado.")
