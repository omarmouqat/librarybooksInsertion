import requests


def get_book_details_openlib(isbn):
    # 1. Get Metadata
    url = f"https://openlibrary.org/api/books?bibkeys=ISBN:{isbn}&format=json&jscmd=data"
    response = requests.get(url)

    if response.status_code == 200:
        data = response.json()
        key = f"ISBN:{isbn}"

        if key in data:
            book = data[key]
            title = book.get('title')
            authors = [a['name'] for a in book.get('authors', [])]

            # 2. Construct Image URL manually (Very reliable)
            # Size options: -S.jpg, -M.jpg, -L.jpg
            cover_url = f"https://covers.openlibrary.org/b/isbn/{isbn}-L.jpg"

            return {
                "title": title,
                "authors": authors,
                "image_url": cover_url
            }
    return None


# Test
isbn = "9782266222334"
info = get_book_details_openlib(isbn)
print(info)