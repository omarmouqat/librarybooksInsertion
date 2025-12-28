import requests


def get_book_details_google(isbn):
    url = f"https://www.googleapis.com/books/v1/volumes?q=isbn:{isbn}"
    response = requests.get(url)

    if response.status_code == 200:
        data = response.json()
        if "items" in data:
            book = data['items'][0]['volumeInfo']

            # Extract info
            title = book.get('title')
            authors = book.get('authors', [])
            # Get image URL (defaults to a placeholder if missing)
            image_links = book.get('imageLinks', {})
            thumbnail = image_links.get('thumbnail')

            return {
                "title": title,
                "authors": authors,
                "image_url": thumbnail
            }
    return None


# Test
isbn = "9780134685991"  # Effective Java
info = get_book_details_google(isbn)
print(info)