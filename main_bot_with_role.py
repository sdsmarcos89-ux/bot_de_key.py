import discord
from discord.ext import commands
from discord.ui import Button, View
from flask import Flask
from threading import Thread
import os

# ==========================================
# SERVIDOR WEB PARA O RENDER (KEEP ALIVE)
# ==========================================
app = Flask('')

@app.route('/')
def home():
    return "Bot está online!"

def run():
    app.run(host='0.0.0.0', port=8080)

def keep_alive():
    t = Thread(target=run)
    t.start()

# ==========================================
# CONFIGURAÇÕES DO BOT (SUBSTITUA AQUI)
# ==========================================

# 1. PEGUE UM NOVO TOKEN NO DISCORD DEVELOPER PORTAL (O ANTERIOR FOI DESATIVADO)
TOKEN = "COLOQUE_O_NOVO_TOKEN_AQUI"

# 2. ID DO SEU SERVIDOR
GUILD_ID = 1499640893806870639

# 3. ID DO CARGO @Heulper
HELPER_ROLE_ID = 1499649343374753902

# 4. ID DA CATEGORIA DE TICKETS
TICKET_CATEGORY_ID = 0  # <--- VOCÊ AINDA PRECISA COLOCAR ESTE ID

# ==========================================

intents = discord.Intents.default()
intents.message_content = True
intents.guilds = True
intents.members = True 

bot = commands.Bot(command_prefix="", intents=intents)

@bot.event
async def on_ready():
    print(f"Bot conectado como {bot.user}")

@bot.event
async def on_guild_channel_create(channel):
    if isinstance(channel, discord.TextChannel) and channel.category_id == TICKET_CATEGORY_ID:
        
        button_wait = Button(label="Aguardar Suporte", style=discord.ButtonStyle.primary)
        button_helper = Button(label="Chamar Helper", style=discord.ButtonStyle.success)

        async def wait_callback(interaction: discord.Interaction):
            await interaction.response.send_message("Entendido! Por favor, aguarde.", ephemeral=True)

        async def helper_callback(interaction: discord.Interaction):
            guild = bot.get_guild(GUILD_ID)
            if guild:
                helper_role = guild.get_role(HELPER_ROLE_ID)
                if helper_role:
                    await interaction.response.send_message(f"O cargo {helper_role.mention} foi notificado!")
                else:
                    await interaction.response.send_message("Cargo não encontrado.", ephemeral=True)

        button_wait.callback = wait_callback
        button_helper.callback = helper_callback

        view = View()
        view.add_item(button_wait)
        view.add_item(button_helper)

        await channel.send(
            "Olá! Bem-vindo ao seu ticket.\nComo podemos ajudar?",
            view=view
        )

if __name__ == "__main__":
    keep_alive() # Inicia o servidor web para o Render não dar erro de porta
    bot.run(TOKEN)
