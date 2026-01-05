import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin
import re
import pandas as pd
from conf import *
# ---------------- Configuration ----------------
LOGIN_URL = f"{BASE_URL}/main.php"

CATALOG_CREATE = f"{BASE_URL}/catalog.php?categ=create_form&id=0"

# ------------------------------------------------

def restorAllInputs(page):
    payload = {}
    # inputs
    for inp in page.find_all("input"):
        name = inp.get("name")
        if name:
            payload[name] = inp.get("value", "")

    # textareas
    for ta in page.find_all("textarea"):
        name = ta.get("name")
        if name:
            payload[name] = ta.text or ""

    # selects
    for sel in page.find_all("select"):
        name = sel.get("name")
        if not name:
            continue
        option = sel.find("option", selected=True)
        payload[name] = option["value"] if option else ""
    
    return payload


def login_to_pmb(session):
    headers = {
        "Content-Type": "application/x-www-form-urlencoded",
    }

    # GET login page (cookies + hidden fields)
    r = session.get(LOGIN_URL, headers=headers)
    if r.status_code != 200:
        print("Cannot reach login page")
        return False

    soup = BeautifulSoup(r.text, "html.parser")

    payload = restorAllInputs(soup)

    # Inject credentials (field names are PMB-standard)
    payload["user"] = USERNAME
    payload["password"] = PASSWORD

    # POST login (URL-ENCODED)
    r = session.post(
        LOGIN_URL,
        data=payload,
        headers=headers,
        allow_redirects=True
    )
    # Detect failure (PMB returns 200 even on failure)
    if "Identification incorrecte" in r.text:
        print("Login failed: incorrect credentials")
        return False

    
    # Verify session cookie
    cookies = list(session.cookies)
    if not cookies:
        print("Login failed: no session cookie received")
        return False

    # Final confirmation
    if "logout.php" in r.text or "navbar" in r.text:
        print("Login successful")
        return True

    print("Login status uncertain")
    return False


def test_authenticated_request(session: requests.Session):
    """
    Example of an authenticated request after login
    """
    main_url = f"{BASE_URL}/main.php"
    response = session.get(main_url)

    if response.status_code == 200 and "Tableau de Bord" in response.text:
        print("Session is authenticated (dashboard accessible)")
    else:
        print("Session lost or unauthorized")


def submit_isbn(session, isbn):
    r = session.post(
        CATALOG_CREATE,
        data={"saisie_cb": isbn},
        headers={
            "Content-Type": "application/x-www-form-urlencoded",
            "Referer": CATALOG_CREATE,
        },
    )
    soup = BeautifulSoup(r.text, "html.parser")
    form = soup.find("form")

    if not form:
        raise Exception("Second form not returned")

    action = urljoin(CATALOG_CREATE, form.get("action"))

    return action, soup



def submit_notice(session, action_url, soup,notice):
    print(f"Creating Notice with isbn : {notice["code_barre"]}\n")
    payload = restorAllInputs(soup)

    payload["f_tit1"] = notice["Titre"]
    payload["f_n_resume"] = notice["Note_generale"]
    payload["f_thumbnail_url"] = notice["Cover_URL"]
    payload["f_aut0"] = notice["Auteurs"]

    
    r = session.post(
        action_url,
        data=payload,
        headers={
            "Content-Type": "application/x-www-form-urlencoded",
            "Referer": action_url,
        },
        allow_redirects=True,
    )
   
    if "notice enregistrée" in r.text.lower():
        print("Notice successfully created")
    else:
        print("Notice submission done — verify manually")

    soup = BeautifulSoup(r.text, "html.parser")
    contenu_div = soup.find("div", id="contenu")
    url = ""
    if contenu_div:
    # 2️⃣ Find all <script> tags inside that div
        for script in contenu_div.find_all("script"):
            if script.string:
                # 3️⃣ Extract URL from document.location
                match = re.search(r"document\.location\s*=\s*['\"](.*?)['\"]", script.string)
                if match:
                    print("Notice successfully created")
                    url = match.group(1)
                    submit_exmplaire(session,url,notice)
                    return 
                    
    else:
        print("Div 'contenu' not found")
    
def submit_exmplaire(session,action_url,notice):
    action = action = urljoin(CATALOG_CREATE, action_url)
    payload = {}
    
    print(action)
    r = session.get(
        action,
        data=payload,
        headers={
            
        },
        allow_redirects=True,
    )

    #Page 1 (Insertion of examplaire nb )
    soup = BeautifulSoup(r.text, "html.parser")
    form = soup.find("form",{"name": "addex"})
    action = urljoin(CATALOG_CREATE, form.get("action"))
    payload = restorAllInputs(soup)
    payload["noex"] = notice["code_barre"]

    r = session.post(
        action,
        data=payload,
        headers={
            "Content-Type": "application/x-www-form-urlencoded",
            "Referer": action_url,
        },
        allow_redirects=True,
    )
    
    #Page 2(Insert of Cote )
    soup = BeautifulSoup(r.text, "html.parser")
    form = soup.find("form",{"name": "expl"})
    action = urljoin(CATALOG_CREATE, form.get("action"))
    payload = restorAllInputs(soup)
    payload["f_ex_cb"] = notice["code_barre"]
    payload["f_ex_cote"] = "lk3j324"
    r = session.post(
        action,
        data=payload,
        headers={
            "Content-Type": "application/x-www-form-urlencoded",
            "Referer": action_url,
        },
        allow_redirects=True,
    )

    #Page 3 (Form validation)
    soup = BeautifulSoup(r.text, "html.parser")
    form = soup.find("form",{"name": "dummy"})
    input  = form.find("input",{"name":"id_form"})
    action = urljoin(CATALOG_CREATE, form.get("action"))
    payload = restorAllInputs(soup)
    payload["id_form"] = input.get("value")
    r = session.post(
        action,
        data=payload,
        headers={
            "Content-Type": "application/x-www-form-urlencoded",
            "Referer": action_url,
        },
        allow_redirects=True,
    )

    

def main():
    # Session object automatically stores cookies (PHPSESSID)
    session = requests.Session()

    if not login_to_pmb(session):
        return

    data = pd.read_csv(CSV_FILE)
    row = data.iloc[8]

    
    action_url, soup = submit_isbn(session,row["code_barre"])
    action_url = BASE_URL + "/catalog.php?&categ=update"
    
    submit_notice(session, action_url, soup,row)


if __name__ == "__main__":
    main()

