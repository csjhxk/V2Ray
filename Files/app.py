import pybase64
import base64
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
    try:
        padded = (encoded.encode() if isinstance(encoded, str) else encoded) + b"=" * (-len(encoded) % 4)
        return pybase64.b64decode(padded).decode("utf-8") or ""
    except:
        return ""

def get_max_pages(base_url):
    try:
        soup = BeautifulSoup(requests.get(base_url).text, "html.parser")
        pagination = soup.find("ul", class_="pagination justify-content-center")
        if pagination:
            page_nums = [int(link.get("href").split("=")[-1]) for link in pagination.find_all("a", class_="page-link") if link.get("href").startswith("?page=")]
            return max(page_nums) if page_nums else 1
        return 1
    except:
        return 1

def fetch_url_config(url):
    try:
        return decode_base64(requests.get(url).content)
    except:
        return ""

def fetch_server_config(url):
    try:
        soup = BeautifulSoup(requests.get(url).text, "html.parser")
        config_div = soup.find("textarea", {"id": "config"})
        return config_div.get("data-config") if config_div else None
    except:
        return None

def scrape_v2nodes_links(base_url):
    links = []
    for page in range(1, get_max_pages(base_url) + 1):
        try:
            soup = BeautifulSoup(requests.get(f"{base_url}?page={page}").text, "html.parser")
            links.extend(f"{base_url}/servers/{server.get('data-id')}/" for server in soup.find_all("div", class_="col-md-12 servers") if server.get("data-id"))
        except:
            pass
    return links

def decode_urls(urls):
    with concurrent.futures.ThreadPoolExecutor(max_workers=30) as executor:
        return [future.result() for future in concurrent.futures.as_completed([executor.submit(fetch_url_config, url) for url in urls]) if future.result()]

def decode_links(links):
    with concurrent.futures.ThreadPoolExecutor(max_workers=30) as executor:
        return [future.result() for future in concurrent.futures.as_completed([executor.submit(fetch_server_config, url) for url in links]) if future.result()]

def filter_for_protocols(data, protocols):
    return [line for line in data for config_line in (line.splitlines() if "\n" in line else [line]) if any(protocol in config_line for protocol in protocols)]

def main():
    output_folder = os.path.abspath(os.path.join(os.getcwd(), ".."))
    os.makedirs(output_folder, exist_ok=True)
    protocols = ["vmess", "vless", "trojan", "ss", "ssr", "hy2", "tuic", "warp://"]
    links = [
        "https://shadowmere.xyz/api/b64sub",
        "https://raw.githubusercontent.com/roosterkid/openproxylist/main/V2RAY_BASE64.txt",
        "https://raw.githubusercontent.com/mahdibland/V2RayAggregator/master/Eternity"
    ]
    base_url = "https://v2nodes.com"

    decoded_links = decode_urls(links)
    v2nodes_configs = decode_links(scrape_v2nodes_links(base_url))
    merged_configs = filter_for_protocols(decoded_links + v2nodes_configs, protocols)

    output_file = os.path.join(output_folder, "All_Configs_Sub.txt")
    base64_file = os.path.join(output_folder, "All_Configs_Base64.txt")
    if os.path.exists(base64_file):
        os.remove(base64_file)

    with open(output_file, "w") as f:
        f.write(fixed_text + "\n".join(merged_configs) + "\n")

    with open(output_file, "r") as f:
        with open(base64_file, "w") as bf:
            bf.write(base64.b64encode(f.read().encode()).decode())

if __name__ == "__main__":
    main()
