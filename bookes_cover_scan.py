import os
import shutil
import pandas as pd
import easyocr

# ---------- CONFIG ----------
IMAGES_FOLDER = "output/nonscaned"
CSV_FILE = "output/library_catalog.csv"
OUTPUT_FOLDER = "covers"

VALID_EXTENSIONS = (".png", ".jpg", ".jpeg", ".bmp", ".tiff")

os.makedirs(OUTPUT_FOLDER, exist_ok=True)

# ---------- OCR ----------
reader = easyocr.Reader(['fr', 'en'], gpu=False)

def normalize(text):
    return (
        text.lower()
        .replace("’", "'")
        .replace("é", "e")
        .replace("è", "e")
        .replace("ê", "e")
        .replace("à", "a")
        .replace("ù", "u")
        .replace("î", "i")
        .replace("ô", "o")
        .strip()
    )

def image_contains_title(image_path, title):
    try:
        results = reader.readtext(image_path)
        full_text = " ".join([text for _, text, _ in results])
        return normalize(title) in normalize(full_text)
    except Exception as e:
        print(f"OCR error on {image_path}: {e}")
        return False

# ---------- MAIN ----------
def main():
    df = pd.read_csv(CSV_FILE)

    print("Scanning images with EasyOCR...")

    for filename in os.listdir(IMAGES_FOLDER):
        if not filename.lower().endswith(VALID_EXTENSIONS):
            continue

        image_path = os.path.join(IMAGES_FOLDER, filename)

        for _, row in df.iterrows():
            barcode = str(row["code_barre"])
            title = str(row["Titre"])

            if image_contains_title(image_path, title):
                new_name = f"{barcode}_{filename}"
                shutil.copy2(image_path, os.path.join(OUTPUT_FOLDER, new_name))
                print(f"[MATCH] {filename} → {new_name}")
                break
            else:
                print(f"No match found for {barcode}")

    print("Done.")

if __name__ == "__main__":
    main()
