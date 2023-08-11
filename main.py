import discord
import os
from discord.flags import Intents
from dotenv import load_dotenv
from discord.ext import commands
import io
import utils
import cv2
import numpy as np
import imutils
import json
from translation import en, pt
import os
os.chdir("./items/trade.png")

items = [
    "anima_stone",
    "blue_devil_stone",
    
    # "copper",
    # "dark_steel",
    # "dragon_leather",
    # "energy",

    "evil_minded_orb",
    "exorcism_bauble",
    "glittering_powder",
    "illuminating_fragment",
    "moon_shadow_stone",
    "platinum",
    "quintessence",
    "steel",

    # "dragon_eye",
    # "dragon_scale",
    # "dragon_claw",
    # "dragon_horn",
]

PlayerInventory = {}
GLOBAL_SCALE = 1.42
leftTopPadding = 30
bottomRightPadding = 62

load_dotenv()

intents = discord.Intents.all()

my_guild = discord.Object(id=1127618095687671909)

class MyClient(discord.Client):
    def __init__(self, *, intents: Intents):
        super().__init__(intents=intents)
        self.tree = discord.app_commands.CommandTree(self)

    async def setup_hook(self):
        self.tree.copy_global_to(guild=my_guild)
        await self.tree.sync(guild=my_guild)

client = MyClient(intents=intents)

allowedChannels = [1128338314877997177, 1129154483268632636]


@client.event
async def on_message(message):
    if message.author == client.user:
        return

    if not message.channel.id in allowedChannels or len(message.attachments) == 0:
        return
    
    language = None
    translation = {}

    if message.channel.id == 1129154483268632636:
        language = "pt"
        translation = pt
    else:
        language = "en"
        translation = en
    
    await message.add_reaction("🕓")
    
    try:
        finalImages = []

        for file in message.attachments:
            imageReady = await file.read()
            arr = np.asarray(bytearray(imageReady), dtype=np.uint8)
            inventoryImage = cv2.imdecode(arr, -1) # 'Load it as it is'
            originalImage = utils.addAlphaChannels(inventoryImage)

            inventoryImage = originalImage.copy()
            trade = cv2.imread("./items/trade.png", cv2.IMREAD_UNCHANGED)

            for item in items:
                itemTemplate = cv2.imread(f"./items/{item}.png", cv2.IMREAD_UNCHANGED)
                itemTemplate = itemTemplate[leftTopPadding:bottomRightPadding, leftTopPadding:bottomRightPadding]
                itemTemplate = imutils.resize(
                    itemTemplate, width=int(itemTemplate.shape[1] * GLOBAL_SCALE)
                )
                tradeIcon = imutils.resize(trade, width=int(trade.shape[1] * 0.90526))

                utils.searchItem(itemTemplate, item, originalImage, tradeIcon, inventoryImage, PlayerInventory)

            finalImages.append(inventoryImage)
        
        title = translation["'s inventory matching result"]
        embed = discord.Embed(title=f"{message.author.global_name}{title}", color=0x2C2542, type="rich", description=translation["Recently added feature - please be patient as this is a new feature which still being worked on. If you have any trouble, please report issues to the Mir4Tools administrators."])
        embed.set_thumbnail(url=client.user.avatar)
        embed.set_footer(text=translation["Click on the button bellow to get a JSON from your inventory match"])

        _, buffer = cv2.imencode(".png", utils.vconcat_resize(finalImages))
        io_buf = io.BytesIO(buffer)
        finalResult = discord.File(io_buf, filename="mir4-inventory-matching.png")

        view = BotView(inventory=PlayerInventory) if language == "en" else BotViewPT(inventory=PlayerInventory)

        await message.reply(embed=embed, view=view, files=[finalResult])
        await message.clear_reaction("🕓")
        await message.add_reaction("✅")
    except Exception as error:
        print(error)
        await message.clear_reaction("🕓")
        await message.add_reaction("❌")

class BotView(discord.ui.View):
    def __init__(self,inventory):
        super().__init__()
        self.inventory = inventory

    @discord.ui.button(label="Click to see the results in JSON", style=discord.ButtonStyle.primary, emoji="👀")
    async def button_callback(self, interaction, _):
        await interaction.response.send_message(f"This is a JSON object, copy it and paste on your inventory of https://www.mir4tools.com/ \n\n```json\n{json.dumps(self.inventory, indent=2)}\n```\n", ephemeral=True)

class BotViewPT(discord.ui.View):
    def __init__(self,inventory):
        super().__init__()
        self.inventory = inventory

    @discord.ui.button(label="Clique para ver os resultados em JSON", style=discord.ButtonStyle.primary, emoji="👀")
    async def button_callback(self, interaction, _):
        await interaction.response.send_message(f"Este é um objeto JSON, copie e cole em seu inventário de https://www.mir4tools.com/ \n\n```json\n{json.dumps(self.inventory, indent=2)}\n```\n", ephemeral=True)

@client.event
async def on_reaction_add(reaction: discord.Reaction, user: discord.Member):
    if reaction.message.channel.id != 1129159066086801578:
        return

    emoji = str(reaction.emoji)
    if emoji == "🇺🇸":
        await toggleRole(1129148272309702756, user, True)
    if emoji == "🇧🇷":
        await toggleRole(1129148360591425596, user, True)
    if emoji == "📢":
        await toggleRole(1129148508721647657, user, True)
        
@client.event
async def on_reaction_remove(reaction: discord.Reaction, user: discord.Member):
    if reaction.message.channel.id != 1129159066086801578:
        return
    
    emoji = str(reaction.emoji)
    if emoji == "🇺🇸":
        await toggleRole(1129148272309702756, user, False)
    if emoji == "🇧🇷":
        await toggleRole(1129148360591425596, user, False)
    if emoji == "📢":
        await toggleRole(1129148508721647657, user, False)

async def toggleRole(id: int, user: discord.Member, add: bool):
    role = discord.Object(id)

    if (add):
        return await user.add_roles(role)
    else:
        return await user.remove_roles(role)

@client.event
async def on_ready():
    channel = client.get_channel(1129159066086801578)
    async for message in channel.history(limit=5):
        await message.delete()

    message = await channel.send(content="# Select your role\n\n:loudspeaker:  Get pinged when a new update came out.\n:loudspeaker:  Receba um ping quando uma nova atualização for lançada.\n\n:flag_us:  English (US)\n:flag_br:  Português (PT-BR)")

    await message.add_reaction("🇺🇸")
    await message.add_reaction("🇧🇷")
    await message.add_reaction("📢")

    print(f"{client.user} is ready and online!")

client.run(os.getenv('DISCORD_TOKEN'))