import fitz  # PyMuPDF
import os
from seleniumbase import Driver
import shutil


# location for the Pokémon Decklist sheet
POKEMON_RULES_URL = "https://www.pokemon.com/us/play-pokemon/about/tournaments-rules-and-resources"

def convert_pdf_to_png(in_file, out_file):
    doc = fitz.open(in_file)  # open document
    for page in doc:  # iterate through the pages
        pix = page.get_pixmap(matrix=fitz.Matrix(2.0, 2.0))  # render page to an image
        pix.save(out_file) 


def get_decklist_pdf(output_filename):
    # Here you would implement the logic to generate the decklist PDF
    sb = Driver(uc=True, locale_code="en", ad_block=True, external_pdf=True)
    sb.uc_activate_cdp_mode(POKEMON_RULES_URL)
    sb.sleep(5)
    a_elements = sb.cdp.find_visible_elements("a")

    for a in a_elements:
        if a.get_attribute("innerHTML").strip() == "Play! Pokémon Deck List (A4)":
            a.click()
            sb.sleep(5)
            break
    else:
        raise Exception("Couldn't find sheet in page")

    for file in os.listdir("downloaded_files"):
        if file.endswith(".pdf"):
            pdf_path = os.path.join("downloaded_files", file)
            if os.path.exists(pdf_path):
                if os.path.exists(output_filename):
                    os.remove(output_filename)  # Remove existing file if it exists
                os.rename(pdf_path, output_filename)
            break
    else:
        raise Exception("No pdf in downloaded files")
    
    sb.quit()
    shutil.rmtree('downloaded_files', ignore_errors=True)  # Clean up the directory

def get_decklist_png(output_filename="sign_up_sheet.png"):
    # Here you would implement the logic to generate the decklist PNG
    get_decklist_pdf("tmp.pdf")
    convert_pdf_to_png("tmp.pdf", output_filename)
    # Clean up temporary files if necessary
    os.remove("tmp.pdf")
