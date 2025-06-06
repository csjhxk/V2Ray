import pybase64
import base64
import requests
import binascii
import os

TIMEOUT = 20

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
            decoded = pybase64.b64decode(encoded + b"=" * (-len(encoded) % 4)).decode(encoding)
            break
        except (UnicodeDecodeError, binascii.Error):
            pass
    return decoded

def decode_links(links):
    decoded_data = []
    for link in links:
        try:
            response = requests.get(link, timeout=TIMEOUT)
            encoded_bytes = response.content
            decoded_text = decode_base64(encoded_bytes)
            decoded_data.append(decoded_text)
        except requests.RequestException:
            pass
    return decoded_data

def filter_for_protocols(data, protocols):
    filtered_data = []
    for line in data:
        if any(protocol in line for protocol in protocols):
            filtered_data.append(line)
    return filtered_data

def ensure_directories_exist():
    output_folder = os.path.abspath(os.path.join(os.getcwd(), ".."))
    if not os.path.exists(output_folder):
        os.makedirs(output_folder)
    return output_folder

def main():
    output_folder = ensure_directories_exist()
    protocols = ["vmess", "vless", "trojan", "ss", "ssr", "hy2", "tuic", "warp://"]
    links = [
        "https://shadowmere.xyz/api/b64sub",
        "https://raw.githubusercontent.com/roosterkid/openproxylist/main/V2RAY_BASE64.txt"
    ]

    decoded_links = decode_links(links)
    merged_configs = filter_for_protocols(decoded_links, protocols)

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
        encoded_config = base64.b64encode(config_data.encode()).decode()
        output_file.write(encoded_config)

if __name__ == "__main__":
    main()
