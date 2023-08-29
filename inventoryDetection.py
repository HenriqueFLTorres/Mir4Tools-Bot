import io
import utils
import cv2
import numpy as np
import imutils
from translation import en, pt
import os
import discord
import json

allowedChannels = [1128338314877997177, 1129154483268632636]

PlayerInventory = {}
GLOBAL_SCALE = 1.42
leftTopPadding = 30
bottomRightPadding = 62

async def handleImageDetection(message: str, clientId: int, avatar: discord.Asset):
    if message.author == clientId:
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
        embed.set_thumbnail(url=avatar)

        _, buffer = cv2.imencode(".png", utils.vconcat_resize(finalImages))
        io_buf = io.BytesIO(buffer)
        finalResult = discord.File(io_buf, filename="mir4-inventory-matching.png")
        
        await message.reply(embed=embed, files=[finalResult, discord.File(io.StringIO(json.dumps(PlayerInventory, indent=2)), filename="inventory.json")])
        await message.clear_reaction("🕓")
        await message.add_reaction("✅")
    except Exception as error:
        print(error)
        await message.clear_reaction("🕓")
        await message.add_reaction("❌")
