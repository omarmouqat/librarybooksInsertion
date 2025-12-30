import os
import csv
import requests
import shutil

# ---------------- Configuration ----------------
OUTPUT_DIR = "output"
COVERS_FOLDER = os.path.join(OUTPUT_DIR, "fetched_covers")
CSV_FILE = os.path.join(OUTPUT_DIR, "library_catalog.csv")

os.makedirs(COVERS_FOLDER, exist_ok=True)


# ---------------- Helpers ----------------
def is_book_isbn(code):
    clean = code.replace("-", "").replace(" ", "")
    return clean.isdigit() and clean.startswith(("978", "979"))


def fetch_google_books(isbn):
    url = f"https://www.googleapis.com/books/v1/volumes?q=isbn:{isbn}"

    try:
        response = requests.get(url, timeout=10)
        if response.status_code != 200:
            return None

        data = response.json()
        if not data.get("items"):
            return None

        item = data["items"][0]
        info = item.get("volumeInfo", {})
        search_info = item.get("searchInfo", {})

        description = info.get("description") or \
                      search_info.get("textSnippet", "Pas de description disponible.")

        images = info.get("imageLinks", {})
        cover_url = images.get("thumbnail") or images.get("smallThumbnail")

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
            "Local_Cover_File": "",
            "error": ""
        }

    except Exception as e:
        print(f"API error: {e}")
        return None


def download_cover_image(url, isbn):
    if not url:
        return ""

    try:
        response = requests.get(url, stream=True, timeout=10)
        if response.status_code == 200:
            filename = f"{isbn}_cover.jpg"
            path = os.path.join(COVERS_FOLDER, filename)
            with open(path, "wb") as f:
                shutil.copyfileobj(response.raw, f)
            return filename
    except Exception:
        pass

    return ""


def save_to_csv(rows):
    fieldnames = [
        "code_barre", "Titre", "Auteurs", "Editeur",
        "Type de document", "Format", "Langues",
        "Mots_cles", "Note_generale",
        "Cover_URL", "Local_Cover_File", "error"
    ]

    file_exists = os.path.isfile(CSV_FILE)

    with open(CSV_FILE, "a", newline="", encoding="utf-8") as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)

        if not file_exists:
            writer.writeheader()

        for row in rows:
            for field in fieldnames:
                row.setdefault(field, "")
            writer.writerow(row)


# ---------------- Main Loop ----------------
def main():
    print("📚 ISBN Book Catalog System")
    print("Type 'exit' to stop\n")

    while True:
        isbn = input("Enter ISBN: ").strip()

        if isbn.lower() == "exit":
            print("Goodbye 👋")
            break

        if not is_book_isbn(isbn):
            print("❌ Invalid ISBN (must start with 978 or 979)\n")
            continue

        book = fetch_google_books(isbn)

        if book:
            cover_file = download_cover_image(book["Cover_URL"], isbn)
            book["Local_Cover_File"] = cover_file
            save_to_csv([book])
            print(f"✅ Saved: {book['Titre']}\n")
        else:
            print("⚠ ISBN valid, but no metadata found\n")


if __name__ == "__main__":
    main()

