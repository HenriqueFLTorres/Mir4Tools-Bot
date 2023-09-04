import os
from utils import addAlphaChannels, items, searchItem
import cv2
import imutils

GLOBAL_SCALE = 1.42
leftTopPadding = 30
bottomRightPadding = 62

result = [
    {'evil_minded_orb': {'Rare': {'traddable': 97, 'nonTraddable': 1412}}, 'exorcism_bauble': {'Rare': {'traddable': 35, 'nonTraddable': 811}}, 'illuminating_fragment': {'Rare': {'traddable': 66, 'nonTraddable': 294}}, 'moon_shadow_stone': {'Rare': {'traddable': 74, 'nonTraddable': 1470}}, 'platinum': {'Rare': {'traddable': 45, 'nonTraddable': 2}}, 'quintessence': {'Rare': {'traddable': 37, 'nonTraddable': 891}}, 'steel': {'Rare': {'traddable': 228, 'nonTraddable': 2561}}},
    {'blue_devil_stone': {'Rare': {'traddable': 2, 'nonTraddable': 23}}},
    {'anima_stone': {'Epic': {'traddable': 22, 'nonTraddable': 78}}, 'illuminating_fragment': {'Epic': {'nonTraddable': 13}}, 'platinum': {'Epic': {'traddable': 43, 'nonTraddable': 257}}},
    {'anima_stone': {'Uncommon': {'traddable': 6209}}, 'evil_minded_orb': {'Uncommon': {'traddable': 12799, 'nonTraddable': 330}}, 'exorcism_bauble': {'Uncommon': {'traddable': 5457, 'nonTraddable': 170}}, 'illuminating_fragment': {'Uncommon': {'traddable': 10056, 'nonTraddable': 237}}, 'moon_shadow_stone': {'Uncommon': {'traddable': 12579, 'nonTraddable': 357}}, 'platinum': {'Uncommon': {'traddable': 38627, 'nonTraddable': 123}}, 'quintessence': {'Uncommon': {'traddable': 5757, 'nonTraddable': 243}}, 'steel': {'Uncommon': {'traddable': 44555, 'nonTraddable': 5593}}},
]

def testMatching():
    for index, file in enumerate(["./test/1.png", "./test/2.png", "./test/3.png", "./test/4.png"]):
        PlayerInventory = {}
        
        inventoryImage = cv2.imread(os.path.join(os.path.dirname(__file__), file), -1) # 'Load it as it is'
        originalImage = addAlphaChannels(inventoryImage)

        inventoryImage = originalImage.copy()
        trade = cv2.imread(os.path.join(os.path.dirname(__file__), "./items/trade.png"), cv2.IMREAD_UNCHANGED)

        for item in items:
            itemTemplate = cv2.imread(os.path.join(os.path.dirname(__file__), f"./items/{item}.png"), cv2.IMREAD_UNCHANGED)
            itemTemplate = itemTemplate[leftTopPadding:bottomRightPadding, leftTopPadding:bottomRightPadding]
            itemTemplate = imutils.resize(
                itemTemplate, width=int(itemTemplate.shape[1] * GLOBAL_SCALE)
            )
            tradeIcon = imutils.resize(trade, width=int(trade.shape[1] * 0.90526))

            searchItem(itemTemplate, item, originalImage, tradeIcon, inventoryImage, PlayerInventory)

        assert PlayerInventory == result[index]

        cv2.imshow("result", inventoryImage)
        cv2.waitKey(0)
        cv2.destroyAllWindows()
        
testMatching()