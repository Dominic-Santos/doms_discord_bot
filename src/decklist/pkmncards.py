from seleniumbase import SB
import json

CARD_LIST_ULR = "https://pkmncards.com/?s=format%3A{current_format}&sort=date&ord=auto&display=list"

CURRENT_FORMAT = CARD_LIST_ULR.format(current_format="g-on-standard-2026")

REPLACE_CHARACTERS = {
    "’": "'",
    "›": ">",
}

def get_legal_card_list():
    legal_cards = []
    with SB(uc=True, test=False, locale_code="en", ad_block=True) as sb:
        sb.activate_cdp_mode(CURRENT_FORMAT)
        sb.sleep(1)
        
        headers = ["set", "number", "name", "type", "color", "rarity"]

        while True:
            card_elements = sb.cdp.find_visible_elements("article.type-pkmn_card")
            for card in card_elements:
                card_details = {}
                card_base = card.children[0].children[0].children
                for i, header in enumerate(headers):
                    card_details[header] = card_base[i].text.strip()
                card_details["link"] = card_base[2].children[0]["href"]
                legal_cards.append(card_details)
            
            try:
                next_link_element = sb.cdp.find_visible_elements("li.next-link a")
            except Exception as e:
                break
            next_link_element[0].click()
            sb.sleep(1)
    return legal_cards


def save_cards_to_file(cards, filename="legal_cards.json"):
    final_cards = {}
    for card in cards:
        for k in card.keys():
            if k == "link":
                continue
            for old, new in REPLACE_CHARACTERS.items():
                card[k] = card[k].replace(old, new)
        
        final_cards.setdefault(card["set"], {})[card["number"]] = {
            "name": card["name"],
            "type": card["type"],
            "color": card["color"],
            "rarity": card["rarity"],
            "link": card["link"]
        }
    json.dump(final_cards, open(filename, "w"), indent=4)


def get_legal_cards(filename="legal_cards.json"):
    legal_cards = get_legal_card_list()
    save_cards_to_file(legal_cards, filename)


def get_card_text(card_link):
    with SB(uc=True, test=False, locale_code="en", ad_block=True) as sb:
        sb.activate_cdp_mode(card_link)
        sb.sleep(1)
        card_text = sb.cdp.find_visible_elements('div.card-text-area div.card-tabs div.tab div.text')[0].text.strip()
    return card_text.strip()


if __name__ == "__main__":
    card_text = get_card_text("https://pkmncards.com/card/abomasnow-paldea-evolved-pal-011/")
    card_text2 = get_card_text("https://pkmncards.com/card/abomasnow-paldean-fates-paf-101/")
    print(card_text)
    print(card_text2)
    print("Same" if card_text == card_text2 else "Different")