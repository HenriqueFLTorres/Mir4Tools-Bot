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
import asyncio
import os

PlayerInventory = {}
GLOBAL_SCALE = 1.42
leftTopPadding = 30
bottomRightPadding = 62

load_dotenv()
intents = discord.Intents.all()

my_guild = discord.Object(id=1127618095687671909)
ROLES_CHANNEL = 1129159066086801578
ROLES_MESSAGE = 1140727328322879608

allowedChannels = [1128338314877997177, 1129154483268632636]

class MyClient(discord.Client):
    def __init__(self, *, intents: Intents):
        super().__init__(intents=intents)
        self.tree = discord.app_commands.CommandTree(self)

    async def setup_hook(self):
        self.tree.copy_global_to(guild=my_guild)
        await self.tree.sync(guild=my_guild)
        self.add_view(BotReportView())

client = MyClient(intents=intents)

@client.event
async def on_ready():
    channel = client.get_channel(ROLES_CHANNEL)
    message = await channel.fetch_message(ROLES_MESSAGE)

    await message.add_reaction("🇺🇸")
    await message.add_reaction("🇧🇷")
    await message.add_reaction("📢")

    print(f"{client.user} is ready and online!")

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
            trade = cv2.imread(os.path.join(os.path.dirname(__file__),"./items/trade.png"), cv2.IMREAD_UNCHANGED)

            for item in utils.items:
                itemTemplate = cv2.imread(os.path.join(os.path.dirname(__file__), f"./items/{item}.png"), cv2.IMREAD_UNCHANGED)
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

@client.event
async def on_raw_reaction_add(event: discord.RawReactionActionEvent):
    if event.message_id != 1140727328322879608:
        return
    
    emoji = str(event.emoji)
    if emoji == "🇺🇸":
        await addRole(1129148272309702756, event.user_id)
    if emoji == "🇧🇷":
        await addRole(1129148360591425596, event.user_id)
    if emoji == "📢":
        await addRole(1129148508721647657, event.user_id)


@client.tree.command(name="prepare_report", guild=my_guild)
async def prepare_report(interaction: discord.Interaction):
    embed = discord.Embed(title=f"Contact us", color=0x2C2542, type="rich", description="Interact with the buttons bellow to either make a suggestion or a bug report, the bot will send you a private message after the interaction so you can describe the issue.")
    embed.set_thumbnail(url=client.user.avatar)

    await interaction.response.send_message(embed=embed, view=BotReportView())


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

class BotReportView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)
        self.ongoing = []

    def removeId(self, id: int):
        self.ongoing.remove(id)
    
    def addId(self, id: int):
        self.ongoing.append(id)

    @discord.ui.button(label="Make a suggestion", style=discord.ButtonStyle.primary, emoji="🔮", custom_id='persistent_view:suggestion')
    async def suggestion_callback(self, interaction: discord.Interaction, _):
        if (interaction.user.id in self.ongoing): return
        self.addId(interaction.user.id)

        embed = discord.Embed(title=f"Suggestion creation", color=0x2C2542, type="rich", description="Type your suggestion in only one message. If you want to cancel this interaction, click on the Cancel button.\n\nThis interaction will expire after 15 minutes.")
        embed.set_thumbnail(url=client.user.avatar)

        await interaction.user.send(embed=embed, view=BotReportResponseView(trigger=self.removeId))

        def check(message: discord.Message):
            return message.channel.type == discord.ChannelType.private and message.author == interaction.user

        try:
            message = await client.wait_for("message", timeout=60.0*15.0, check=check)
            await interaction.user.send(f"Your suggestion was successfully submitted, and our team will soon review it!")
            
            reportEmbed = discord.Embed(title="Suggestion", color=0x2C2542, type="rich", description=message.content)
            reportEmbed.set_author(name=message.author)
            await client.get_channel(1141774925552689153).send(embed=reportEmbed)
            self.ongoing.remove(interaction.user.id)
        except asyncio.TimeoutError:
            self.ongoing.remove(interaction.user.id)
            await interaction.user.send("Message timeout.")

    @discord.ui.button(label="Report a bug", style=discord.ButtonStyle.primary, emoji="🐛", custom_id='persistent_view:report')
    async def bug_callback(self, interaction: discord.Interaction, _):
        if (interaction.user.id in self.ongoing): return
        self.addId(interaction.user.id)

        embed = discord.Embed(title=f"Bug report", color=0x2C2542, type="rich", description="Type your report in only one message as the following template:\n\n Page name: Constitution \n Feature name: Tier selection \n How to reproduce: ... \n\n If you want to cancel this interaction, click on the Cancel button.\n\nThis interaction will expire after 15 minutes.")
        embed.set_thumbnail(url=client.user.avatar)

        await interaction.user.send(embed=embed, view=BotReportResponseView(trigger=self.removeId))
        
        def check(message: discord.Message):
            return message.channel.type == discord.ChannelType.private and message.author == interaction.user

        try:
            message = await client.wait_for("message", timeout=60.0*15.0, check=check)
            await interaction.user.send(f"Your bug was successfully reported, and our team will soon resolve it!")

            reportEmbed = discord.Embed(title="Bug report", color=0x2C2542, type="rich", description=message.content)
            reportEmbed.set_author(name=message.author)
            await client.get_channel(1141774925552689153).send(embed=reportEmbed)
            self.ongoing.remove(interaction.user.id)
        except asyncio.TimeoutError:
            self.ongoing.remove(interaction.user.id)
            await interaction.user.send("Message timeout.")

class BotReportResponseView(discord.ui.View):
    def __init__(self, trigger):
        super().__init__()
        self.trigger = trigger

    @discord.ui.button(label="Cancel", style=discord.ButtonStyle.danger)
    async def cancel_callback(self, interaction: discord.Interaction, _):
        self.trigger(interaction.user.id)
        await interaction.user.send(content="Interaction canceled.")

async def addRole(roleId: int, userId: int):
    role = discord.Object(roleId)
    guild = await client.fetch_guild(1127618095687671909)
    user = await guild.fetch_member(userId)

    return await user.add_roles(role)

client.run(os.getenv('DISCORD_TOKEN'))