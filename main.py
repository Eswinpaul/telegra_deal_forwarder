import streamlit as st
import urllib.parse
import time
import requests
import re
from urllib.parse import urlparse, parse_qs, urlencode, urlunparse, quote_plus
from collections import OrderedDict
from unshortenit import UnshortenIt

# --------------------------
# 🔐 Simple Login Mechanism
# --------------------------
USERNAME = "icbadmin"
PASSWORD = "indiancashback"

if "logged_in" not in st.session_state:
    st.session_state.logged_in = False

if not st.session_state.logged_in:
    st.set_page_config(page_title="Login", layout="centered")
    st.title("Login")
    username = st.text_input("Username")
    password = st.text_input("Password", type="password")
    if st.button("Login"):
        if username == USERNAME and password == PASSWORD:
            st.session_state.logged_in = True
            st.success("Login successful")
            st.experimental_rerun()
        else:
            st.error("Invalid credentials")

# --------------------------
# ✅ Cashback Link Generator
# --------------------------
if st.session_state.logged_in:
    st.set_page_config(page_title="Cashback Link Generator", layout="centered")
    st.title("IndianCashback Link Generator")
    st.write("Paste your message containing URLs to convert them into cashback links.")

    SUPPORTED_STORES = {
        "amazon": "amazon.in",
        "flipkart": "flipkart.com",
        "ajio": "ajio.com",
        "myntra": "myntra.com",
        "shopsy": "shopsy.in",
        "pepperfry": "pepperfry.com",
        "croma": "croma.com",
        "tatacliq": "tatacliq.com"
    }

    cashback_links = {
    "Flipkart": "https://qvmdz.com/g/rb1qie435bd42f7f33e6a80d05f527/?ulp=",
    "Ajio": "https://tjzuh.com/g/gobb106sd9d42f7f33e6a663530cb9/?ulp=",
    "Myntra": "https://ymuac.com/g/s56leml8ckd42f7f33e623d5247706/?ulp=",
    "Shopsy": "https://tjzuh.com/g/riiso24dfxd42f7f33e6bf3169313e/?ulp=",
    "Croma": "https://tjzuh.com/g/rjmwpd17fqd42f7f33e621602b7160/?ulp=",
    "Pepperfry": "https://tjzuh.com/g/avo9zwf5jhd42f7f33e6e187ed2532/?ulp=",
    "Tatacliq": "https://tjzuh.com/g/f9pyfv0or6d42f7f33e622654840ad/?ulp="
}

    AFFILIATE_TAG = "tag=revo21-21"
    YOURLS_API = "https://icashbk.in/yourls-api.php"
    YOURLS_SIGNATURE = "d8837aa1b9"

    PARAMS_TO_KEEP = set([
        'query', 'text', 'curated', 'curatedid', 'gridColumns', 'classifier', 'segmentIds',
        'includeUnratedProducts', 'userClusterId', 'q', 'sid', 'sort', 'pid', 'pageUID', 'marketplace',
        'otracker', 'p[]', 'k', 'i', 'bbn', 'srs', 'rh', 's', 'rdpf', 'node', 'hidden-keywords', 'fs',
        'almBrandId', 'p', 'rf', 'rawQuery', 'bu', 'collection-tab-name', 'is_retargeting', 'f'
    ])

    def extract_urls(text):
        return re.findall(r'https?://\S+', text)

    def unshorten_url(url):
        try:
            return UnshortenIt().unshorten(url)
        except:
            return url

    def identify_store(domain):
        for store, pattern in SUPPORTED_STORES.items():
            if pattern in domain:
                return store.capitalize()
        return None

    def clean_url(parsed_url, query_params, store):
        filtered = OrderedDict((k, v) for k, v in query_params.items() if k in PARAMS_TO_KEEP)
        if 'ref' in query_params and 'clp_pc_cart_collapse' in query_params['ref']:
            filtered['ref'] = query_params['ref']
        query_string = urlencode(filtered, doseq=True)
        cleaned = urlunparse((parsed_url.scheme, parsed_url.netloc, parsed_url.path, '', query_string, ''))
        if store.lower() == "amazon":
            cleaned += '&' + AFFILIATE_TAG if query_string else '?' + AFFILIATE_TAG
        return cleaned

    def shorten_url(url):
        params = {
            "signature": YOURLS_SIGNATURE,
            "action": "shorturl",
            "url": url,
            "format": "json"
        }
        try:
            res = requests.get(YOURLS_API, params=params)
            if res.status_code == 200:
                return res.json().get("shorturl")
        except:
            return url
        return url

    def process_links(text):
        modified_links, stores_found = [], []
        urls = extract_urls(text)

        for url in urls:
            final_url = unshorten_url(url)
            parsed = urlparse(final_url)
            query = parse_qs(parsed.query)

            store = identify_store(parsed.netloc)
            if not store:
                continue
            stores_found.append(store)

            cleaned_url = clean_url(parsed, query, store)

            if store.lower() == "amazon":
                final = cleaned_url
            else:
                base = cashback_links.get(store, "")
                final = base + quote_plus(cleaned_url)

            short = shorten_url(final)
            modified_links.append(short)

        return modified_links, list(set(stores_found))

    def send_to_telegram(text):
        token = "7051241078:AAFUjDwcBlvOyRVFOHn49IMrPY0Ly2yJe0c"
        chat_id = "-4689810762"
        url = f"https://api.telegram.org/bot{token}/sendMessage"
        payload = {
            "chat_id": chat_id,
            "text": text,
            "parse_mode": "Markdown"
        }
        response = requests.post(url, data=payload)
        return response.ok

    # UI
    user_input = st.text_area("Paste your message here", height=150)
    if st.button("Generate Links") and user_input:
        with st.spinner("Processing links..."):
            links, stores = process_links(user_input)
            if links:
                st.success("Modified Cashback Links:")
                for link in links:
                    st.code(link)
                telegram_sent = send_to_telegram("\n".join(links))
                if telegram_sent:
                    st.success("✅ Sent to Telegram group!")
                else:
                    st.error("❌ Failed to send to Telegram.")
            else:
                st.warning("No valid URLs found.")

    st.sidebar.button("Logout", on_click=lambda: st.session_state.update({"logged_in": False}))
