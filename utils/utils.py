import random
import json
from PIL import Image, ImageDraw, ImageFont
from colormath.color_conversions import convert_color
from colormath.color_diff import delta_e_cie1976, delta_e_cie2000
from colormath.color_objects import LabColor, sRGBColor


def get_adjective() -> str:
    adj = [
        "alluring",
        "appealing",
        "charming",
        "dazzling",
        "delightful",
        "elegant",
        "exquisite",
        "fascinating",
        "gorgeous",
        "handsome",
        "lovely",
        "magnificent",
        "marvelous",
        "pleasing",
        "splendid",
        "stunning",
        "superb",
        "wonderful",
        "angelic",
        "bewitching",
        "divine",
        "enticing",
        "pulchritudinous",
        "ravishing",
        "resplendent",
        "sublime",
        "delectable",
        "luscious",
        "titillating",
        "ambrosial",
        "captivating",
    ]
    return random.choice(adj)


def get_color_name(srgb_color: sRGBColor) -> str:
    lab_color = convert_color(srgb_color, LabColor)
    lowest = (999, {})
    with open("colornames.json", encoding="utf-8") as colornames:
        colornames = json.loads(colornames.read())
    for color in colornames:
        srgb = sRGBColor.new_from_rgb_hex(color["hex"])
        lab = convert_color(srgb, LabColor)
        delta_e = delta_e_cie1976(lab_color, lab)
        if delta_e < lowest[0]:
            lowest = (delta_e, color)
    return lowest[1]["name"]


def generate_color_swatch(color: sRGBColor):
    img = Image.new("RGB", (175, 175), color=color.get_rgb_hex())
    d = ImageDraw.Draw(img)
    d.text((130, 163), color.get_rgb_hex(), fill="black")
    img.save("./appdata/color.png")
