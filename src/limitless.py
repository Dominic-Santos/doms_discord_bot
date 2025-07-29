from seleniumbase import Driver


def get_decklist_from_url(link):
    pokemon = []
    trainers = {}
    energies = {}

    sb = Driver(uc=True, locale_code="en", ad_block=True)

    sb.uc_activate_cdp_mode(link)
    sb.sleep(1)
    sb.cdp.find_visible_elements("button.svelte-c276fa")[3].click()
    sb.sleep(1)
    sb.cdp.find_visible_elements("button.svelte-c276fa")[4].click()
    sb.sleep(1)
    table = sb.cdp.find_visible_elements("table.svelte-1sps4x1")[0]

    mode = "pokemon"
    for row in table.children:
        card = {}

        for i, cell in enumerate(row.children):
            if cell.tag_name == "th":
                cell_text = cell.text.lower()
                if cell_text in ["pokemon", "trainer", "energy"]:
                    mode = cell_text
                break
        
            if len(row.children) < 2:
                break
            
            if mode == "pokemon":
                if i == 0:
                    card["quantity"] = int(cell.text)
                elif i == 1:
                    card["name"] = cell.text
                elif i == 2:
                    card["set"] = cell.text
                elif i == 3:
                    card["number"] = int(cell.text)
                elif i == 4:
                    card["letter"] = cell.text.upper()
                    pokemon.append(card)
            elif mode == "trainer":
                if i == 0:
                    card["quantity"] = int(cell.text)
                elif i == 1:
                    card_name = cell.text
                    if card_name not in trainers:
                        trainers[card_name] = {"quantity": 0}
                    trainers[card_name]["quantity"] += card["quantity"]
            elif mode == "energy":
                if i == 0:
                    card["quantity"] = int(cell.text)
                elif i == 1:
                    card_name = cell.text
                    if card_name not in energies:
                        energies[card_name] = {"quantity": 0}
                    energies[card_name]["quantity"] += card["quantity"]
    sb.quit()
    return {"pokemon": pokemon, "trainers": trainers, "energies": energies}

