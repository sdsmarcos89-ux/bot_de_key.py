import discord
import pyotp
import os
import threading
import json
from http.server import HTTPServer, BaseHTTPRequestHandler
from dotenv import load_dotenv

# --- SERVIDOR PARA O RENDER NÃO DORMIR ---
class HealthCheckHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b"Bot 2FA Online")

def run_health_check():
    port = int(os.environ.get("PORT", 10000))
    server = HTTPServer(("0.0.0.0", port), HealthCheckHandler)
    server.serve_forever()

threading.Thread(target=run_health_check, daemon=True).start()
# ------------------------------------------

load_dotenv()
token = os.getenv("DISCORD_BOT_TOKEN")

CONFIG_FILE = "config_panel.json"
CLIENT_ROLE_NAME = "Client" # Nome do cargo que terá acesso

def load_config():
    if os.path.exists(CONFIG_FILE):
        with open(CONFIG_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return {
        "title": "🛡️ Rockstar Games e Autenticação de Dois Fatores (2FA)",
        "description": "A segurança da sua conta Rockstar Games é primordial. A Autenticação de Dois Fatores (2FA) adiciona uma camada extra de proteção.",
        "color": 0x5865F2,
        "image_url": "https://upload.wikimedia.org/wikipedia/commons/thumb/5/52/Rockstar_Games_Logo.svg/1200px-Rockstar_Games_Logo.svg.png",
        "thumbnail_url": "https://upload.wikimedia.org/wikipedia/commons/thumb/5/52/Rockstar_Games_Logo.svg/1200px-Rockstar_Games_Logo.svg.png"
    }

def save_config(config):
    with open(CONFIG_FILE, "w", encoding="utf-8") as f:
        json.dump(config, f, indent=4, ensure_ascii=False)

class SecretInputModal(discord.ui.Modal):
    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self.add_item(discord.ui.InputText(
            label="Sua Chave Secreta 2FA", 
            placeholder="Cole sua chave secreta aqui...", 
            style=discord.InputTextStyle.short
        ))

    async def callback(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True)
        secret = self.children[0].value
        try:
            totp = pyotp.TOTP(secret.replace(" ", "").upper())
            code = totp.now()
            config = load_config()
            embed = discord.Embed(
                title="🔑 Seu Código 2FA",
                description=f"```\n{code}\n```\n\nEste código é válido por **30 segundos**. Gere um novo se expirar.",
                color=config["color"]
            )
            embed.set_footer(text="Rockstar 2FA Bot")
            await interaction.followup.send(embed=embed, ephemeral=True)
        except pyotp.otp.OTPError:
            await interaction.followup.send("❌ Chave Inválida! Verifique se a SECRET está correta.", ephemeral=True)
        except Exception as e:
            await interaction.followup.send(f"❌ Erro inesperado: {e}", ephemeral=True)

class Generate2FAButton(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(
        label="Gere 2fa code", 
        style=discord.ButtonStyle.primary, 
        custom_id="generate_2fa_button",
        emoji="🔑"
    )
    async def button_callback(self, button: discord.ui.Button, interaction: discord.Interaction):
        # VERIFICAÇÃO DE CARGO: Verifica se o usuário tem o cargo "Client" ou é Admin
        has_role = discord.utils.get(interaction.user.roles, name=CLIENT_ROLE_NAME)
        is_admin = interaction.user.guild_permissions.administrator
        
        if not (has_role or is_admin):
            return await interaction.response.send_message(
                f"❌ Acesso Negado! Você precisa do cargo **{CLIENT_ROLE_NAME}** para gerar códigos 2FA.", 
                ephemeral=True
            )
            
        modal = SecretInputModal(title="Insira sua Chave Secreta 2FA")
        await interaction.response.send_modal(modal)

bot = discord.Bot()

# --- COMANDOS DE ADMINISTRAÇÃO ---
admin_group = bot.create_group("admin", "Comandos de administração do painel")

@admin_group.command(name="set_visual", description="Configura o visual do painel 2FA")
async def set_visual(
    ctx: discord.ApplicationContext,
    titulo: discord.Option(str, "Novo título do painel", required=False),
    descricao: discord.Option(str, "Nova descrição do painel", required=False),
    cor_hex: discord.Option(str, "Cor em Hex (ex: 5865F2)", required=False),
    imagem_url: discord.Option(str, "URL da imagem grande", required=False),
    thumbnail_url: discord.Option(str, "URL da imagem pequena (thumbnail)", required=False)
):
    if not ctx.author.guild_permissions.administrator:
        return await ctx.respond("❌ Apenas administradores podem usar este comando.", ephemeral=True)
    
    config = load_config()
    if titulo: config["title"] = titulo
    if descricao: config["description"] = descricao.replace("\\n", "\n")
    if cor_hex:
        try:
            config["color"] = int(cor_hex.lstrip("#"), 16)
        except ValueError:
            return await ctx.respond("❌ Formato de cor inválido! Use Hexadecimal.", ephemeral=True)
    if imagem_url: config["image_url"] = imagem_url
    if thumbnail_url: config["thumbnail_url"] = thumbnail_url
    
    save_config(config)
    await ctx.respond("✅ Configurações visuais atualizadas!", ephemeral=True)

@bot.slash_command(name="setup2fa", description="Configura o painel interativo de 2FA")
async def setup2fa(ctx: discord.ApplicationContext):
    if not ctx.author.guild_permissions.administrator:
        return await ctx.respond("❌ Apenas administradores podem configurar o painel.", ephemeral=True)
    
    config = load_config()
    embed = discord.Embed(title=config["title"], description=config["description"], color=config["color"])
    if config.get("image_url"): embed.set_image(url=config["image_url"])
    if config.get("thumbnail_url"): embed.set_thumbnail(url=config["thumbnail_url"])
    embed.set_footer(text="Rockstar 2FA Bot | Segurança Máxima")
    
    view = Generate2FAButton()
    await ctx.respond("Painel configurado com sucesso!", ephemeral=True)
    await ctx.channel.send(embed=embed, view=view)

@bot.event
async def on_ready():
    bot.add_view(Generate2FAButton())
    print(f"✅ Bot 2FA Online como {bot.user}")

if token:
    bot.run(token)
else:
    print("❌ Erro: DISCORD_BOT_TOKEN não encontrado.")
