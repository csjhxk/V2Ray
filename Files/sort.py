import requests
import os
import base64

ptt = os.path.abspath(os.path.join(os.getcwd(), '..', 'Splitted-By-Protocol'))
os.makedirs(ptt, exist_ok=True)

files = {
    'vmess': os.path.join(ptt, 'vmess.txt'),
    'vless': os.path.join(ptt, 'vless.txt'),
    'trojan': os.path.join(ptt, 'trojan.txt'),
    'ss': os.path.join(ptt, 'ss.txt'),
    'ssr': os.path.join(ptt, 'ssr.txt')
}

for file in files.values():
    open(file, 'w').close()

configs = {'vmess': '', 'vless': '', 'trojan': '', 'ss': '', 'ssr': ''}

response = requests.get("https://raw.githubusercontent.com/T3stAcc/v2ray/main/All_Configs_Sub.txt").text
for config in response.splitlines():
    for protocol in configs:
        if config.startswith(protocol):
            configs[protocol] += config + '\n'

for protocol, data in configs.items():
    with open(files[protocol], 'wb') as f:
        if protocol == 'vmess':
            content = data.encode('utf-8')
        else:
            content = base64.b64encode(data.encode('utf-8'))
        f.write(content)
