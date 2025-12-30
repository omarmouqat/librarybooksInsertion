import os
import shutil
import csv
import requests
from PIL import Image
from pyzbar.pyzbar import decode

# --- Configuration ---
SOURCE_FOLDER = 'book_images'
BACKUP_FOLDER = 'backup'

# Output Folders
SCANNED_FOLDER = 'output/scanned_books'  # Valid books (ISBN 978/979)
NON_SCANNED_FOLDER = 'output/nonscaned'  # Everything else (No barcode OR Non-book barcode)
COVERS_FOLDER = 'output/fetched_covers'

# Output File (CSV)
CSV_FILE = 'output/library_catalog.csv'

VALID_EXTENSIONS = ('.png', '.jpg', '.jpeg', '.bmp', '.tiff', '.gif')


def setup_directories():
    for folder in [SCANNED_FOLDER, NON_SCANNED_FOLDER, COVERS_FOLDER]:
        if not os.path.exists(folder):
            os.makedirs(folder)


def get_barcode_from_image(image_path):
    """Scans the image for any EAN-13 barcode."""
    try:
        img = Image.open(image_path)
        decoded_objects = decode(img)
        for obj in decoded_objects:
            return obj.data.decode('utf-8')
        return None
    except Exception as e:
        print(f"Error reading image {image_path}: {e}")
        return None


def is_book_barcode(code):
    """Checks if the barcode is a Bookland EAN (starts with 978 or 979)."""
    clean_code = code.replace('-', '').replace(' ', '')
    return clean_code.startswith(('978', '979'))


def fetch_google_books(isbn):
    """Queries Google Books API using the ISBN."""
    api_url = f"https://www.googleapis.com/books/v1/volumes?q=isbn:{isbn}"

    try:
        response = requests.get(api_url)
        if response.status_code == 200:
            data = response.json()

            if "items" in data and len(data["items"]) > 0:
                item = data["items"][0]
                info = item.get("volumeInfo", {})
                search_info = item.get("searchInfo", {})

                # Smart description fetch
                description = info.get("description")
                if not description:
                    description = search_info.get("textSnippet", "Pas de description disponible.")

                imgs = info.get("imageLinks", {})
                cover_url = imgs.get("thumbnail") or imgs.get("smallThumbnail")

                # Smart Publisher/Date fetch
                publisher = info.get("publisher", "Editeur Inconnu")
                pub_date = info.get("publishedDate", "")
                full_publisher = f"{publisher}, {pub_date}".strip(", ")

                return {
                    "code_barre": isbn,
                    "Titre": info.get("title", "Titre Inconnu"),
                    "Auteurs": ", ".join(info.get("authors", ["Auteur Inconnu"])),
                    "Editeur": full_publisher,
                    "Type de document": "Texte imprimé",
                    "Format": f"{info.get('pageCount', '?')} pages",
                    "Langues": info.get("language", "Inconnu"),
                    "Mots_cles": ", ".join(info.get("categories", [])),
                    "Note_generale": description,
                    "Cover_URL": cover_url,
                    "Local_Cover_File": None
                }
    except Exception as e:
        print(f"API Error: {e}")

    return None


def download_cover_image(url, barcode):
    if not url:
        return None
    try:
        response = requests.get(url, stream=True)
        if response.status_code == 200:
            file_name = f"{barcode}_cover.jpg"
            file_path = os.path.join(COVERS_FOLDER, file_name)
            with open(file_path, 'wb') as f:
                shutil.copyfileobj(response.raw, f)
            return file_name
    except Exception:
        pass
    return None


def save_to_csv(data_list):
    """Saves the list of dictionaries to a CSV file."""
    if not data_list:
        print("No valid book data to save.")
        return

    # Define the column headers (based on your requested fields)
    fieldnames = [
        "code_barre", "Titre", "Auteurs", "Editeur",
        "Type de document", "Format", "Langues",
        "Mots_cles", "Note_generale", "Cover_URL", "Local_Cover_File", "error"
    ]

    try:
        with open(CSV_FILE, 'w', newline='', encoding='utf-8') as csvfile:
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            writer.writeheader()
            for row in data_list:
                # Ensure every row has all fields to avoid errors
                writer.writerow(row)
        print(f"Data successfully saved to {CSV_FILE}")
    except Exception as e:
        print(f"Error saving CSV: {e}")


def main():
    setup_directories()
    catalog_data = []

    # Restore backup images (Safety check to ensure source folder exists)
    if not os.path.exists(SOURCE_FOLDER):
        os.makedirs(SOURCE_FOLDER)

    if os.path.exists(BACKUP_FOLDER):
        print("Restoring images from backup...")
        for filename in os.listdir(BACKUP_FOLDER):
            src_path = os.path.join(BACKUP_FOLDER, filename)
            shutil.copy2(src_path, os.path.join(SOURCE_FOLDER, filename))
        print("Finished copying images.")
    else:
        print(f"Warning: Backup folder '{BACKUP_FOLDER}' not found. Using existing images in source.")

    print(f"Scanning images in '{SOURCE_FOLDER}'...")

    for filename in os.listdir(SOURCE_FOLDER):
        if filename.lower().endswith(VALID_EXTENSIONS):
            src_path = os.path.join(SOURCE_FOLDER, filename)

            # 1. Scan Barcode
            barcode = get_barcode_from_image(src_path)

            # Default assumption: It's not a valid book until proven otherwise
            is_valid_book = False
            book_details = None

            if barcode:
                # 2. Check if it is a BOOK (starts with 978/979)
                if is_book_barcode(barcode):
                    print(f"[BOOK DETECTED] {barcode} in {filename}")

                    book_details = fetch_google_books(barcode)

                    if book_details:
                        # Success: Download Cover
                        cover_file = download_cover_image(book_details['Cover_URL'], barcode)
                        book_details['Local_Cover_File'] = cover_file
                        catalog_data.append(book_details)
                        print(f"   -> Info Fetched: {book_details['Titre']}")
                        is_valid_book = True
                    else:
                        # ISBN is valid format, but no data online.
                        # We still treat it as a book (just missing data)
                        print(f"   -> ISBN valid, but no metadata online.")
                        catalog_data.append({
                            "code_barre": barcode,
                            "error": "Metadata not found online"
                        })
                        is_valid_book = True
                else:
                    print(f"[IGNORED] Non-book barcode: {barcode} in {filename}")
            else:
                print(f"[SKIP] No barcode found in {filename}")

            # 3. Move files based on result
            if is_valid_book:
                shutil.move(src_path, os.path.join(SCANNED_FOLDER, filename))
            else:
                # Moves both 'No Barcode' AND 'Non-Book Barcode' images here
                shutil.move(src_path, os.path.join(NON_SCANNED_FOLDER, filename))

    # Save CSV
    save_to_csv(catalog_data)

    print("-" * 50)
    print(f"Processing Complete.")
    print(f"CSV Data: {CSV_FILE}")


if __name__ == "__main__":
    main()