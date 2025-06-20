import pybase64, base64, binascii, requests, os, concurrent.futures
from bs4 import BeautifulSoup

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
            padded = encoded + b"=" * (-len(encoded) % 4) if isinstance(encoded, bytes) else encoded.encode() + b"=" * (-len(encoded) % 4)
            decoded = pybase64.b64decode(padded).decode(encoding)
            break
        except (UnicodeDecodeError, binascii.Error): pass
    return decoded

def get_max_pages(base_url):
    try:
        r = requests.get(base_url)
        s = BeautifulSoup(r.text, "html.parser")
        p = s.find("ul", class_="pagination justify-content-center")
        if p:
            nums = [int(l.get("href", "").split("=")[-1]) for l in p.find_all("a", class_="page-link") if l.get("href", "").startswith("?page=")]
            return max(nums) if nums else 1
        return 1
    except: return 1

def fetch_url_config(url):
    try:
        r = requests.get(url)
        return decode_base64(r.content) if r.content else ""
    except: return ""

def fetch_server_config(url):
    try:
        r = requests.get(url)
        s = BeautifulSoup(r.text, "html.parser")
        d = s.find("textarea", {"id": "config"})
        return d.get("data-config") if d and d.get("data-config") else None
    except: return None

def scrape_v2nodes_links(base_url):
    maxp = get_max_pages(base_url)
    links = []
    for page in range(1, maxp + 1):
        try:
            r = requests.get(f"{base_url}?page={page}")
            s = BeautifulSoup(r.text, "html.parser")
            servers = s.find_all("div", class_="col-md-12 servers")
            links += [f"{base_url}/servers/{srv.get('data-id')}/" for srv in servers if srv.get("data-id")]
        except: pass
    return links

def fetch_mosifree(url):
    try:
        r = requests.get(url)
        if r.status_code == 200:
            lines = r.text.strip().splitlines()
            out = []
            for l in lines:
                if l.startswith("//"): out.append(l.replace("//", "#"))
                elif any(p in l for p in ["vmess://", "vless://", "trojan://", "ss://", "ssr://", "hy2://", "tuic://", "warp://"]): out.append(l)
            return "\n".join(out)
    except: return ""

def decode_urls(urls):
    data = []
    with concurrent.futures.ThreadPoolExecutor(30) as e:
        f = {e.submit(fetch_url_config, u): u for u in urls}
        for fut in concurrent.futures.as_completed(f):
            r = fut.result()
            if r: data.append(r)
    return data

def decode_links(links):
    data = []
    with concurrent.futures.ThreadPoolExecutor(30) as e:
        f = {e.submit(fetch_server_config, u): u for u in links}
        for fut in concurrent.futures.as_completed(f):
            r = fut.result()
            if r: data.append(r)
    return data

def decode_mosifree(urls):
    data = []
    with concurrent.futures.ThreadPoolExecutor(30) as e:
        f = {e.submit(fetch_mosifree, u): u for u in urls}
        for fut in concurrent.futures.as_completed(f):
            r = fut.result()
            if r: data.append(r)
    return data

def filter_for_protocols(data, protos):
    out = []
    for l in data:
        for c in (l.splitlines() if "\n" in l else [l]):
            if any(p in c for p in protos) or c.startswith("#profile-"): out.append(c)
    return out

def ensure_directories_exist():
    d = os.path.abspath(os.path.join(os.getcwd(), ".."))
    if not os.path.exists(d): os.makedirs(d)
    return d

def main():
    folder = ensure_directories_exist()
    protos = ["vmess", "vless", "trojan", "ss", "ssr", "hy2", "tuic", "warp://"]
    urls = [
        "https://shadowmere.xyz/api/b64sub",
        "https://raw.githubusercontent.com/roosterkid/openproxylist/main/V2RAY_BASE64.txt",
        "https://raw.githubusercontent.com/mahdibland/V2RayAggregator/master/Eternity"
    ]
    mosifree = [
        "https://raw.githubusercontent.com/Mosifree/-FREE2CONFIG/main/Vmess",
        "https://raw.githubusercontent.com/Mosifree/-FREE2CONFIG/main/Vless",
        "https://raw.githubusercontent.com/Mosifree/-FREE2CONFIG/main/SS",
        "https://raw.githubusercontent.com/Mosifree/-FREE2CONFIG/main/T%2CH"
    ]
    base_url = "https://v2nodes.com"
    a = decode_urls(urls)
    b = scrape_v2nodes_links(base_url)
    c = decode_links(b)
    d = decode_mosifree(mosifree)
    all_data = filter_for_protocols(a + c + d, protos)
    f_txt = os.path.join(folder, "All_Configs_Sub.txt")
    b64_txt = os.path.join(folder, "All_Configs_Base64.txt")
    if os.path.exists(b64_txt): os.remove(b64_txt)
    with open(f_txt, "w") as f:
        f.write(fixed_text)
        for config in all_data: f.write(config + "\n")
    with open(f_txt, "r") as i: data = i.read()
    with open(b64_txt, "w") as o:
        o.write(base64.b64encode(data.encode()).decode())

if __name__ == "__main__": main()
