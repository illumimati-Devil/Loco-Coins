BotToken = "Enter your Bot Token here!"
BotPrefix = "Enter Bot Prefix here!"

import random
import requests
import asyncio
from discord import Game
from discord.ext.commands import Bot
import discord
from discord.ext import commands
import random
import aiohttp
import json

client = Bot(command_prefix = BotPrefix)

headers = {
    "authorization": "Blep NxiYEwFvgWh6D01whmjp6YFhiEKdn40"
}
apiUrl = "http://blep.host:10101/"

with open("UsersData.json", "w+") as f:
    json.dump({}, f)

with open("UsersData.json") as f:
    UsersData = json.load(f)

def SaveUsersData():
    with open("UsersData.json", "w+") as f:
        json.dump(UsersData, f)

@client.event
async def on_ready():
    print(
        "Logged in as",
        str(client.user)
    )
    await client.change_presence(
        game = Game(
            name = "Loco Practice | {}play".format(
                BotPrefix
            )
        )
    )

@client.command(pass_context = True, no_pm = True)
async def play(ctx, *, phoneNumber: str = None):
    if phoneNumber is None:
        return await client.say(
            "**Correct Use:**\n`{}play <phoneNumber>`".format(
                BotPrefix
            )
        )
    print(phoneNumber)
    if phoneNumber.startswith("+91"):
        phoneNumber = phoneNumber[3:]
    print(phoneNumber)
    if len(phoneNumber) != 10:
        return await client.say(
            "**Invalid Phone Number!**"
        )
    
    response = requests.post(
        apiUrl+"Loco/SendOTP",
        headers = headers,
        json = {
            "phoneNumber": phoneNumber
        }
    ).json()
    
    if response.get("error"):
        return await client.say(
            "**An error occurred.**"
        )
    
    elif not response.get("status"):
        return await client.say(
            "**An error occurred.**"
        )
    
    await client.say(
        "**OTP has been successfully sent to your phone number:**\n`+91{}*****`\nPlease enter your otp using `{}code <otp>`".format(
            phoneNumber[:5],
            BotPrefix
        )
    )
    
    def CodeCheck(Message):
        return Message.content.lower().startswith(
            "{}code".format(
                BotPrefix
            )
        )
    
    codeMessage = await client.wait_for_message(
        author = ctx.message.author,
        timeout = 60,
        check = CodeCheck
    )
    code = codeMessage.content.lower()[(len(BotPrefix)+4):]
    code = str(code.replace(" ", ""))
    
    if len(code) != 4:
        return await client.say(
            "**Invalid OTP Entered!**"
        )
    
    response = requests.post(
        apiUrl+"Loco/VerifyOTP",
        headers = headers,
        json = {
            "phoneNumber": phoneNumber,
            "code": code
        }
    ).json()
    print(response)
    if response.get("error"):
        if response["errorCode"] == 7:
            return await client.say(
                "**Session expired!\nPlease use `{}play` command again.**".format(
                    BotPrefix
                )
            )
        else:
            return await client.say(
                "**Incorrect OTP entered!**"
            )
    
    
    authToken = response["authToken"]
    
    UsersData[ctx.message.author.id] = authToken
    SaveUsersData()
    print("otp verified")
    response = requests.post(
        apiUrl+"Loco/PlayPractice",
        headers = headers,
        json = {
            "authToken": authToken
        }
    ).json()
    print(response)
    if response.get("error"):
        if response["errorCode"] == 10:
            return await client.say(
                "**{}**".format(
                    response["error"]
                )
            )
        
        else:
            return await client.say(
                "**An unknown error occurred!**"
            )
    
    practiceMessage = await client.say(
        "**Started Loco Practice!**"
    )
    
    TotalEarned = 0
    TotalBalance = "Unknown"
    
    while True:
        await asyncio.sleep(5)
        
        response = requests.get(
            apiUrl+"Loco/GetPracticeStatus",
            headers = headers,
            json = {
                "authToken": authToken
            }
        ).json()
        
        if response.get("error"):
            del UsersData[ctx.message.author.id]
            SaveUsersData()
                
            if response["errorCode"] == 11:
                if TotalEarned == 0:
                    return await client.edit_message(
                        practiceMessage,
                        "**You played all the Practice Games!\nPlease try again later.**"
                    )
                
                return await client.edit_message(
                    practiceMessage,
                    "**Loco Practice Over!**\n\n**• Total Coins Earned: {}\n• Total Coin Balance: {}**".format(
                        TotalEarned,
                        TotalBalance
                    )
                )
            
            return await client.edit_message(
                practiceMessage,
                "**An unknown error occurred!**"
            )
        
        TotalEarned = response["TotalEarned"]
        TotalBalance = response["TotalBalance"]
        
        await client.edit_message(
            practiceMessage,
            "**Playing Loco Practice...**\n\n**• Total Coins Earned: {}\n• Total Coin Balance: {}**".format(
                TotalEarned,
                TotalBalance
            )
        )

@client.command(pass_context = True, no_pm = True)
async def stop(ctx):
    if ctx.message.author.id not in UsersData:
        return await client.say(
            "**No game running on your account!**"
        )
    
    authToken = UsersData[ctx.message.author.id]
    del UsersData[ctx.message.author.id]
    SaveUsersData()
    
    response = requests.post(
        apiUrl+"Loco/StopPractice",
        headers = headers,
        json = {
            "authToken": authToken
        }
    ).json()
    
    if response.get("status"):
        return await client.say(
            "**"+response["message"]+"**"
        )
    
    elif response.get("error"):
        if response["errorCode"] == 11:
            return await client.say(
                "**No game running on your account!**"
            )
        
        return await client.say(
            "**An unknown error occurred!**"
        )
    
    else:
        return await client.say(
            "**An unknown error occurred!**"
        )

if BotToken == "Enter your Bot Token here!":
    raise ValueError("Please enter your Bot Token in line 1")
if BotPrefix == "Enter Bot Prefix here!":
    raise ValueError("In line 2, please enter the prefix that you want for the Bot!")

auth2 = BotToken
response = requests.get(
    apiUrl+"GetOnline",
    headers = headers,
    json = {"auth2": auth2}
).json()
print(response)
if response.get("error"):
    raise ConnectionError("Unable to connect to the API.")
else:
    print(response["message"])

loop = asyncio.get_event_loop()
while True:
    try:
        loop.run_until_complete(client.start(BotToken, reconnect=True))
    except Exception as e:
        time.sleep(1)
        print("Event loop error:", e)
