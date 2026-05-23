import discord
from discord.ext import commands
from discord.ui import Button, View

# ==========================================
# CONFIGURAÇÕES DO BOT
# ==========================================

# Token do seu bot Discord (Recomendado resetar após o uso)
TOKEN = "MTUwNzIzOTMwMTE1Nzc1MjkyMg.GrB2Zq.w2urPvVNgPgdqYqSOaIztSeApnyPdLoAkm92uk"

# ID do seu servidor (Guild ID)
GUILD_ID = 1499640893806870639

# ID do cargo @Heulper
HELPER_ROLE_ID = 1499649343374753902

# ID da CATEGORIA onde os tickets são abertos (IMPORTANTE: Você deve preencher este ID)
# Para pegar o ID, clique com o botão direito na categoria de tickets e "Copiar ID"
TICKET_CATEGORY_ID = 0  # <--- COLOQUE O ID DA CATEGORIA AQUI

# ==========================================

# Intents necessários para o bot
intents = discord.Intents.default()
intents.message_content = True
intents.guilds = True
intents.members = True 

bot = commands.Bot(command_prefix="", intents=intents)

@bot.event
async def on_ready():
    print(f"Bot conectado como {bot.user}")
    print("------")

@bot.event
async def on_guild_channel_create(channel):
    # Verifica se o canal criado está na categoria de tickets correta
    if isinstance(channel, discord.TextChannel) and channel.category_id == TICKET_CATEGORY_ID:
        
        # Criação dos botões
        button_wait = Button(label="Aguardar Suporte", style=discord.ButtonStyle.primary)
        button_helper = Button(label="Chamar Helper", style=discord.ButtonStyle.success)

        # Ação: Aguardar Suporte
        async def wait_callback(interaction: discord.Interaction):
            await interaction.response.send_message("Entendido! Por favor, aguarde um momento.", ephemeral=True)

        # Ação: Chamar Helper
        async def helper_callback(interaction: discord.Interaction):
            guild = bot.get_guild(GUILD_ID)
            if guild:
                helper_role = guild.get_role(HELPER_ROLE_ID)
                if helper_role:
                    await interaction.response.send_message(f"O cargo {helper_role.mention} foi notificado!")
                else:
                    await interaction.response.send_message("Cargo @Heulper não encontrado.", ephemeral=True)

        button_wait.callback = wait_callback
        button_helper.callback = helper_callback

        view = View()
        view.add_item(button_wait)
        view.add_item(button_helper)

        # Mensagem automática ao abrir o ticket
        await channel.send(
            "Olá! Bem-vindo ao seu ticket.\n\n"
            "Como podemos ajudar? Escolha uma opção abaixo:",
            view=view
        )

# Inicia o bot
if TOKEN == "" or TOKEN.startswith("MTU"): # Verificação simples do token
    bot.run(TOKEN)
else:
    print("Erro: Verifique o Token no código.")
