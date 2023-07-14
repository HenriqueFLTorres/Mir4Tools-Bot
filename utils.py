import cv2
import numpy as np
import pytesseract

pytesseract.pytesseract.tesseract_cmd = r"C:\Program Files\Tesseract-OCR\tesseract"

GLOBAL_SCALE = 1.42
threshold = 0.85
frameOffset = int(np.round(33 * GLOBAL_SCALE))
smallFrameOffset = int(np.round(25 * GLOBAL_SCALE))

def vconcat_resize(img_list, interpolation=cv2.INTER_CUBIC):
    w_min = min(img.shape[1] for img in img_list)

    im_list_resize = [
        cv2.resize(
            img,
            (w_min, int(img.shape[0] * w_min / img.shape[1])),
            interpolation=interpolation,
        )
        for img in img_list
    ]

    return cv2.vconcat(im_list_resize)


def addAlphaChannels(image):
    if len(image[0][0]) > 3:
        return image
    b, g, r = cv2.split(image)
    a = np.ones(b.shape, dtype=b.dtype) * 255  # creating a dummy alpha channel image.
    image = cv2.merge((b, g, r, a))

    return image


def checkItemRarity(top, bottom, left, right, originalImage, inventoryImage):
    colorFrame = originalImage.copy()[top + 20 : bottom, left : right + 5]
    rarity = None

    if np.any(np.all(colorFrame == (13, 210, 237, 255), axis=-1)):
        rarity = "Legendary"
    elif np.any(np.all(colorFrame == (42, 49, 183, 255), axis=-1)):
        rarity = "Epic"
    elif np.any(np.all(colorFrame == (199, 122, 66, 255), axis=-1)):
        rarity = "Rare"
    elif np.any(np.all(colorFrame == (146, 186, 72, 255), axis=-1)):
        rarity = "Uncommon"
    elif np.any(np.all(colorFrame == (122, 120, 117, 255), axis=-1)):
        rarity = "Common"

    cv2.putText(
        inventoryImage,
        rarity,
        (left + 5, bottom - 6),
        2,
        0.5,
        (255, 255, 255, 255),
        1,
        cv2.LINE_AA,
        False,
    )

    return rarity


def checkItemAmount(top, bottom, left, right, originalImage, inventoryImage, item, rarity):
    matchedValue = originalImage.copy()
    matchedValue = originalImage[top:bottom, left:right]
    matchedValue[np.all(matchedValue <= (210, 210, 210, 255), axis=-1)] = (0, 0, 0, 255)

    # Epic item tweak
    if rarity == "Epic":
        EpicMin = np.array([0, 0, 0, 255], np.uint8)
        EpicMax = np.array([120, 200, 255, 255], np.uint8)
        matchedValue[cv2.inRange(matchedValue, EpicMin, EpicMax) > 0] = [0, 0, 0, 255]
    
    # Exorcism bauble tweak
    if item == "exorcism_bauble":
        GreenMin = np.array([94, 200, 120, 255], np.uint8)
        GreenMax = np.array([167, 251, 167, 255], np.uint8)
        matchedValue[cv2.inRange(matchedValue, GreenMin, GreenMax) > 0] = [0, 0, 0, 255]

    denoise = cv2.fastNlMeansDenoisingColored(matchedValue, None, 44, 10, 4, 21)
    blur = cv2.GaussianBlur(denoise, (1, 1), 0)
    _, binary_image = cv2.threshold(blur, 120, 255, cv2.THRESH_BINARY)

    txt = pytesseract.image_to_string(
        binary_image, config="--psm 6 -c tessedit_char_whitelist=0123456789"
    )

    try:
        number = str(int(txt))
        cv2.putText(
            inventoryImage,
            number,
            (left + 5, bottom - 20),
            2,
            0.5,
            (255, 255, 255, 255),
            1,
            cv2.LINE_AA,
            False,
        )
    except:
        return txt

    return txt


def searchItem(
    template, item, originalImage, tradeIcon, inventoryImage, PlayerInventory
):
    result = cv2.matchTemplate(originalImage, template, cv2.TM_CCOEFF_NORMED)

    w = template.shape[1]
    h = template.shape[0]
    localThreshold = 0.95 if item == "blue_devil_stone" else threshold

    yloc, xloc = np.where(result >= localThreshold)

    rectangles = []
    for x, y in zip(xloc, yloc):
        pl = 0  # padding left for exceptions

        if item == "illuminating_fragment":
            pl = 1

        width = int(x + w - pl)
        height = int(y + h)
        left, top = int(x - pl - frameOffset), int(y - frameOffset)
        right, bottom = width + frameOffset, height + frameOffset

        if top < 0:
            top = 0
        if left < 0:
            left = 0

        rectangles.append([int(left), int(top), int(right), int(bottom)])
        rectangles.append([int(left), int(top), int(right), int(bottom)])

        cv2.rectangle(
            inventoryImage,
            (left, top),
            (right, bottom),
            (101, 62, 71, 255),
            2,
        )

    rectangles, _ = cv2.groupRectangles(rectangles, 1, 0.2)

    for left, top, right, bottom in rectangles:
        frame = originalImage.copy()
        frame = frame[top:bottom, left:right]

        itemRarity = checkItemRarity(
            bottom - frameOffset, bottom, left, left, originalImage, inventoryImage
        )
        itemAmount = checkItemAmount(
            bottom - smallFrameOffset,
            bottom,
            left,
            right,
            originalImage,
            inventoryImage,
            item,
            itemRarity
        )
        isTraddable = findTraddables(frame, top, left, tradeIcon, inventoryImage)
        hasProperty = (
            PlayerInventory.get(item)
            and PlayerInventory.get(item).get(itemRarity) is not None
        )

        try:
            itemAmount = int(itemAmount)
            if hasProperty:
                if isTraddable:
                    PlayerInventory[item][itemRarity]["traddable"] = itemAmount
                else:
                    PlayerInventory[item][itemRarity]["nonTraddable"] = itemAmount
            else:
                if isTraddable:
                    PlayerInventory[item] = {itemRarity: {"traddable": itemAmount}}
                else:
                    PlayerInventory[item] = {itemRarity: {"nonTraddable": itemAmount}}
        except:
            continue


def findTraddables(image, top, left, tradeIcon, inventoryImage):
    result = cv2.matchTemplate(image, tradeIcon, cv2.TM_CCOEFF_NORMED)
    yloc, xloc = np.where(result >= 0.65)

    for _ in zip(xloc, yloc):
        cv2.rectangle(
            inventoryImage,
            (int(left), int(top)),
            (left + 40, top + 40),
            (110, 141, 54, 255),
            2,
        )

    return len(yloc) > 0
