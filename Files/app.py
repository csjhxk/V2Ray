import pybase64
import base64
import binascii
import requests
from bs4 import BeautifulSoup
import os
import concurrent.futures

fixed_text = """#profile-title: base64:VjJSYXkgQ29uZmlncw==
#profile-update-interval: 1
#subscription-userinfo: upload=29; download=12; total=10737418240000000; expire=2546249531
#support-url: https://github.com/T3stAcc/V2Ray
#profile-web-page-url: https://github.com/T3stAcc/V2Ray
"""

def decode_base64(encoded):
    for encoding in ["utf-8", "iso-8859-1"]:
        try:
            padded = (encoded if isinstance(encoded, bytes) else encoded.encode()) + b"=" * (-len(encoded) % 4)
            return pybase64.b64decode(padded).decode(encoding)
        except (UnicodeDecodeError, binascii.Error):
            pass
    return ""

def get_max_pages(base_url):
    try:
        soup = BeautifulSoup(requests.get(base_url).text, "html.parser")
        pagination = soup.find("ul", class_="pagination justify-content-center")
        if pagination:
            page_nums = [int(link["href"].split("=")[-1]) for link in pagination.find_all("a", class_="page-link") if link["href"].startswith("?page=")]
            return max(page_nums) if page_nums else 1
        return 1
    except requests.RequestException:
        return 1

def fetch_url_config(url):
    try:
        response = requests.get(url).content
        try:
            return decode_base64(response).splitlines()
        except (UnicodeDecodeError, binascii.Error):
            return response.decode("utf-8", errors="ignore").splitlines()
    except requests.RequestException:
        return []

def fetch_server_config(url):
    try:
        soup = BeautifulSoup(requests.get(url).text, "html.parser")
        config_div = soup.find("textarea", {"id": "config"})
        return config_div.get("data-config") if config_div and config_div.get("data-config") else None
    except requests.RequestException:
        return None

def scrape_v2nodes_links(base_url):
    links = []
    for page in range(1, get_max_pages(base_url) + 1):
        try:
            soup = BeautifulSoup(requests.get(f"{base_url}?page={page}").text, "html.parser")
            links.extend(f"{base_url}/servers/{server['data-id']}/" for server in soup.find_all("div", class_="col-md-12 servers") if server.get("data-id"))
        except requests.RequestException:
            pass
    return links

def decode_urls(urls):
    with concurrent.futures.ThreadPoolExecutor(max_workers=30) as executor:
        return [config for future in concurrent.futures.as_completed(executor.submit(fetch_url_config, url) for url in urls) for config in future.result()]

def decode_links(links):
    with concurrent.futures.ThreadPoolExecutor(max_workers=30) as executor:
        return [config for future in concurrent.futures.as_completed(executor.submit(fetch_server_config, url) for url in links) if (config := future.result())]

def filter_for_protocols(data, protocols):
    return [line.strip() for line in data if not line.strip().startswith(("#", "//")) and any(protocol in line for protocol in protocols)]

def main():
    output_folder = os.path.abspath(os.path.join(os.getcwd(), ".."))
    os.makedirs(output_folder, exist_ok=True)
    protocols = ["vmess", "vless", "trojan", "ss", "ssr", "hy2", "tuic", "warp://"]
    links = [
        "https://shadowmere.xyz/api/b64sub",
        "https://raw.githubusercontent.com/roosterkid/openproxylist/main/V2RAY_BASE64.txt",
        "https://raw.githubusercontent.com/mahdibland/V2RayAggregator/master/Eternity",
        "https://raw.githubusercontent.com/Mosifree/-FREE2CONFIG/main/Vless",
        "https://raw.githubusercontent.com/Mosifree/-FREE2CONFIG/main/Vmess",
        "https://raw.githubusercontent.com/Mosifree/-FREE2CONFIG/main/SS",
        "https://raw.githubusercontent.com/Mosifree/-FREE2CONFIG/main/T%2CH"
    ]
    base_url = "https://v2nodes.com"

    decoded_links = decode_urls(links)
    v2nodes_configs = decode_links(scrape_v2nodes_links(base_url))
    merged_configs = filter_for_protocols(decoded_links + v2nodes_configs, protocols)

    output_filename = os.path.join(output_folder, "All_Configs_Sub.txt")
    base64_filename = os.path.join(output_folder, "All_Configs_Base64.txt")
    if os.path.exists(base64_filename):
        os.remove(base64_filename)

    with open(output_filename, "w") as f:
        f.write(fixed_text)
        f.write("\n".join(merged_configs) + "\n")

    with open(output_filename, "r") as f:
        with open(base64_filename, "w") as out:
            out.write(base64.b64encode(f.read().encode()).decode())

if __name__ == "__main__":
    main()
