import random


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
