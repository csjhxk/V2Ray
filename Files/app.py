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
    decoded = ""
    for encoding in ["utf-8", "iso-8859-1"]:
        try:
            padded = (encoded if isinstance(encoded, bytes) else encoded.encode()) + b"=" * (-len(encoded) % 4)
            decoded = pybase64.b64decode(padded).decode(encoding)
            break
        except:
            pass
    return decoded

def get_max_pages(base_url):
    try:
        response = requests.get(base_url)
        soup = BeautifulSoup(response.text, "html.parser")
        pagination = soup.find("ul", class_="pagination justify-content-center")
        if pagination:
            page_numbers = [int(link.get("href").split("=")[-1]) for link in pagination.find_all("a", class_="page-link") if link.get("href").startswith("?page=")]
            return max(page_numbers) if page_numbers else 1
        return 1
    except:
        return 1

def fetch_url_config(url):
    try:
        response = requests.get(url)
        return decode_base64(response.content) if response.content else ""
    except:
        return ""

def fetch_server_config(server_url):
    try:
        response = requests.get(server_url)
        soup = BeautifulSoup(response.text, "html.parser")
        config_div = soup.find("textarea", {"id": "config"})
        return config_div.get("data-config") if config_div and config_div.get("data-config") else None
    except:
        return None

def scrape_v2nodes_links(base_url):
    links = []
    for page in range(1, get_max_pages(base_url) + 1):
        try:
            response = requests.get(f"{base_url}?page={page}")
            soup = BeautifulSoup(response.text, "html.parser")
            links.extend(f"{base_url}/servers/{server.get('data-id')}/" for server in soup.find_all("div", class_="col-md-12 servers") if server.get("data-id"))
        except:
            pass
    return links

def decode_urls(urls):
    decoded_data = []
    with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
        future_to_url = {executor.submit(fetch_url_config, url): url for url in urls}
        for future in concurrent.futures.as_completed(future_to_url):
            if config := future.result():
                decoded_data.append(config)
    return decoded_data

def decode_links(links):
    decoded_data = []
    with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
        future_to_url = {executor.submit(fetch_server_config, url): url for url in links}
        for future in concurrent.futures.as_completed(future_to_url):
            if config := future.result():
                decoded_data.append(config)
    return decoded_data

def filter_for_protocols(data, protocols):
    filtered_data = []
    current_metadata = []
    for config in data:
        lines = config.splitlines() if "\n" in config else [config]
        for line in lines:
            line = line.strip()
            if not line:
                continue
            if line.startswith(("#", "//")):
                current_metadata.append(line)
                continue
            if any(protocol in line for protocol in protocols):
                filtered_data.extend(current_metadata)
                filtered_data.append(line)
                current_metadata = []
        if current_metadata and not any(any(protocol in l for protocol in protocols) for l in lines):
            current_metadata = []
    return filtered_data

def ensure_directories_exist():
    output_folder = os.path.abspath(os.path.join(os.getcwd(), ".."))
    os.makedirs(output_folder, exist_ok=True)
    return output_folder

def main():
    output_folder = ensure_directories_exist()
    protocols = ["vmess://", "vless://", "trojan://", "ss://", "ssr://", "hy2://", "tuic://", "warp://"]
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
    v2nodes_links = scrape_v2nodes_links(base_url)
    v2nodes_configs = decode_links(v2nodes_links)
    merged_configs = filter_for_protocols(decoded_links + v2nodes_configs, protocols)

    output_filename = os.path.join(output_folder, "All_Configs_Sub.txt")
    base64_filename = os.path.join(output_folder, "All_Configs_Base64.txt")
    if os.path.exists(base64_filename):
        os.remove(base64_filename)

    with open(output_filename, "w") as f:
        f.write(fixed_text)
        for config in merged_configs:
            f.write(config + "\n")

    with open(output_filename, "r") as input_file:
        config_data = input_file.read()

    with open(base64_filename, "w") as output_file:
        output_file.write(base64.b64encode(config_data.encode()).decode())

if __name__ == "__main__":
    main()
