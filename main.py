import os
import sys
import json
import asyncio
import platform
import requests
import websockets
from colorama import init, Fore
from keep_alive import keep_alive

init(autoreset=True)

status = "online"  # online/dnd/idle
custom_status = ""  # Custom Status

# Collect tokens from environment variables TOKEN1..TOKEN10
tokens = []
for i in range(1, 11):
    token = os.getenv(f"TOKEN{i}")
    print(f"DEBUG: TOKEN{i} = {token}")  # Debug print to confirm tokens are read
    if token:
        tokens.append(token)

if not tokens:
    print(f"{Fore.WHITE}[{Fore.RED}-{Fore.WHITE}] Please add at least one token inside Secrets.")
    sys.exit()

# Validate tokens and gather user info
users_info = []
for token in tokens:
    headers = {"Authorization": token, "Content-Type": "application/json"}
    validate = requests.get("https://canary.discordapp.com/api/v9/users/@me", headers=headers)
    if validate.status_code != 200:
        print(f"{Fore.WHITE}[{Fore.RED}-{Fore.WHITE}] Token '{token[:6]}...' might be invalid. Skipping.")
        continue
    userinfo = validate.json()
    users_info.append({
        "token": token,
        "username": userinfo["username"],
        "discriminator": userinfo["discriminator"],
        "userid": userinfo["id"]
    })

if not users_info:
    print(f"{Fore.WHITE}[{Fore.RED}-{Fore.WHITE}] No valid tokens found. Exiting.")
    sys.exit()

async def onliner(token, status, username, userid):
    try:
        async with websockets.connect("wss://gateway.discord.gg/?v=9&encoding=json") as ws:
            start = json.loads(await ws.recv())
            heartbeat = start["d"]["heartbeat_interval"]

            auth = {
                "op": 2,
                "d": {
                    "token": token,
                    "properties": {
                        "$os": "Windows 10",
                        "$browser": "Google Chrome",
                        "$device": "Windows",
                    },
                    "presence": {"status": status, "afk": False},
                },
            }
            await ws.send(json.dumps(auth))

            cstatus = {
                "op": 3,
                "d": {
                    "since": 0,
                    "activities": [
                        {
                            "type": 4,
                            "state": custom_status,
                            "name": "Custom Status",
                            "id": "custom",
                            # Uncomment and edit emoji if needed
                            # "emoji": {
                            #     "name": "emoji name",
                            #     "id": "emoji id",
                            #     "animated": False,
                            # },
                        }
                    ],
                    "status": status,
                    "afk": False,
                },
            }
            await ws.send(json.dumps(cstatus))

            online = {"op": 1, "d": "None"}
            await asyncio.sleep(heartbeat / 1000)
            await ws.send(json.dumps(online))

            # Keep connection alive by sending heartbeat every interval
            while True:
                await asyncio.sleep(heartbeat / 1000)
                await ws.send(json.dumps(online))
    except Exception as e:
        print(f"{Fore.RED}[{username}] Connection error: {e}")

async def run_all_onliners():
    if platform.system() == "Windows":
        os.system("cls")
    else:
        os.system("clear")

    for info in users_info:
        print(f"{Fore.WHITE}[{Fore.LIGHTGREEN_EX}+{Fore.WHITE}] Logged in as {Fore.LIGHTBLUE_EX}{info['username']}#{info['discriminator']} {Fore.WHITE}({info['userid']})!")

    tasks = []
    for info in users_info:
        tasks.append(asyncio.create_task(onliner(info["token"], status, info["username"], info["userid"])))

    await asyncio.gather(*tasks)

keep_alive()
asyncio.run(run_all_onliners())
