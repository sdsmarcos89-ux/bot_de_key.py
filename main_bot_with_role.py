import discord
import os
import json
import random
import string
import threading
import time
from http.server import HTTPServer, BaseHTTPRequestHandler
from dotenv import load_dotenv

# --- SERVIDOR PARA O RENDER NÃO DORMIR ---
class HealthCheckHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b"Interactive Key Bot Online")

def run_health_check():
    port = int(os.environ.get("PORT", 10000))
    server = HTTPServer(("0.0.0.0", port), HealthCheckHandler)
    server.serve_forever()

threading.Thread(target=run_health_check, daemon=True).start()
# ------------------------------------------

load_dotenv()
token = os.getenv("DISCORD_BOT_TOKEN")

DATABASE_FILE = "interactive_keys.json"
CLIENT_ROLE_NAME = "Client" # Nome do cargo necessário

def load_db():
    if os.path.exists(DATABASE_FILE):
        with open(DATABASE_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return {"keys": {}, "log_channel": None, "panel_config": {
        "title": "🎁 Gerador de Keys - Zaskz Store",
        "description": "Se você possui o cargo **Client**, clique no botão abaixo para gerar sua chave de acesso e envie-a no seu Ticket!",
        "image": "https://i.imgur.com/uG9XN9p.png" # Exemplo de imagem
    }}

def save_db(db):
    with open(DATABASE_FILE, "w", encoding="utf-8") as f:
        json.dump(db, f, indent=4, ensure_ascii=False)

def generate_key(prefix="ZASKZ"):
    chars = string.ascii_uppercase + string.digits
    return f"{prefix}-{''.join(random.choice(chars) for _ in range(4))}-{''.join(random.choice(chars) for _ in range(4))}"

# --- COMPONENTES INTERATIVOS ---

class GenerateKeyView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label="Gerar Minha Key", style=discord.ButtonStyle.primary, custom_id="btn_gen_key", emoji="🔑")
    async def generate_callback(self, button: discord.ui.Button, interaction: discord.Interaction):
        # Verifica se o usuário tem o cargo "Client"
        role = discord.utils.get(interaction.user.roles, name=CLIENT_ROLE_NAME)
        if not role and not interaction.user.guild_permissions.administrator:
            return await interaction.response.send_message(f"❌ Você precisa do cargo **{CLIENT_ROLE_NAME}** para gerar uma chave!", ephemeral=True)
        
        db = load_db()
        key = generate_key()
        while key in db["keys"]:
            key = generate_key()
            
        db["keys"][key] = {
            "produto": "Produto Cliente",
            "status": "disponivel",
            "gerada_por": str(interaction.user.id),
            "gerada_em": time.time()
        }
        save_db(db)
        
        embed = discord.Embed(
            title="🔑 Sua Key foi Gerada!",
            description=f"Aqui está sua chave única:\n\n`{key}`\n\n**Instruções:**\n1. Copie esta chave.\n2. Vá até o seu **Ticket**.\n3. Envie a chave para o administrador validar.",
            color=0x5865F2
        )
        await interaction.response.send_message(embed=embed, ephemeral=True)

# --- BOT E COMANDOS ---

bot = discord.Bot()

@bot.slash_command(name="setup_painel", description="Envia o painel interativo de geração de keys")
async def setup_painel(ctx: discord.ApplicationContext):
    if not ctx.author.guild_permissions.administrator:
        return await ctx.respond("❌ Apenas admins.", ephemeral=True)
    
    db = load_db()
    config = db["panel_config"]
    
    embed = discord.Embed(title=config["title"], description=config["description"], color=0x5865F2)
    if config.get("image"): embed.set_image(url=config["image"])
    
    await ctx.respond("Painel enviado!", ephemeral=True)
    await ctx.channel.send(embed=embed, view=GenerateKeyView())

@bot.slash_command(name="validar", description="Valida a key enviada pelo cliente no ticket")
async def validar(ctx: discord.ApplicationContext, key: str):
    if not ctx.author.guild_permissions.administrator:
        return await ctx.respond("❌ Apenas admins.", ephemeral=True)
    
    db = load_db()
    key = key.upper().strip()
    
    if key not in db["keys"]:
        return await ctx.respond("❌ **Key Inválida!**", ephemeral=False)
    
    info = db["keys"][key]
    if info["status"] == "usada":
        return await ctx.respond(f"⚠️ **Key Já Utilizada!** por <@{info['usada_por']}>", ephemeral=False)
    
    embed = discord.Embed(
        title="✅ Key Legítima!",
        description=f"Key: `{key}`\nGerada por: <@{info['gerada_por']}>\n\nDeseja liberar o produto?",
        color=discord.Color.green()
    )
    
    class ConfirmAction(discord.ui.View):
        @discord.ui.button(label="Liberar e Queimar Key", style=discord.ButtonStyle.danger)
        async def confirm(self, button: discord.ui.Button, interaction: discord.Interaction):
            info["status"] = "usada"
            info["usada_por"] = str(info['gerada_por']) # Registra o dono original
            info["validada_por"] = str(ctx.author.id)
            save_db(db)
            
            await interaction.response.edit_message(content="✅ **Produto Liberado e Key Queimada!**", embed=None, view=None)
            
            # Log de Notificação
            log_id = db.get("log_channel")
            if log_id:
                channel = bot.get_channel(log_id)
                if channel:
                    log_embed = discord.Embed(title="🛒 Venda Validada", color=0x2ECC71)
                    log_embed.add_field(name="👤 Cliente", value=f"<@{info['gerada_por']}>")
                    log_embed.add_field(name="🔑 Key", value=f"`{key}`")
                    log_embed.add_field(name="🛠️ Staff", value=f"<@{ctx.author.id}>")
                    await channel.send(embed=log_embed)

    await ctx.respond(embed=embed, view=ConfirmAction())

@bot.slash_command(name="set_logs", description="Define o canal de logs")
async def set_logs(ctx: discord.ApplicationContext, canal: discord.TextChannel):
    if not ctx.author.guild_permissions.administrator: return
    db = load_db()
    db["log_channel"] = canal.id
    save_db(db)
    await ctx.respond(f"Logs configurados em {canal.mention}", ephemeral=True)

@bot.event
async def on_ready():
    bot.add_view(GenerateKeyView())
    print(f"✅ Sistema Interativo Online: {bot.user}")

if token:
    bot.run(token)
else:
    print("❌ Token não encontrado.")
