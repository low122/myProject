import discord
import os
from dotenv import load_dotenv
import logging
from Binance.Binance_api import BinanceTrade

load_dotenv('/Users/lowjiatzin/Desktop/myProject/KEY.env')

DISCORD_API = os.getenv('DISCORD_TOKEN')

intents = discord.Intents.all()
intents.messages = True

client = discord.Client(intents=intents)
logging.basicConfig(level=logging.INFO)

@client.event
async def on_ready():
    print(f'Logged in as {client.user}')


user_states = {}
user_symbol = {}
user_content = {}

def get_user_state(user_id):
    return user_states.get(user_id)

def set_user_state(user_id, state):
    user_states[user_id] = state

def get_user_symbol(user_id):
    return user_symbol.get(user_id)

def set_user_symbol(user_id, symbol):
    user_symbol[user_id] = symbol

def get_user_content(user_id):
    return user_content.get(user_id)

def set_user_specific_price(user_id, content):
    user_content[user_id] = content

async def mainBoard(message):
    generalInfo = discord.Embed(title='Binance Track')
    generalInfo.add_field(name='1', value='- General Information', inline=False)
    generalInfo.add_field(name='2', value='- Track Highest Peak', inline=False)
    generalInfo.add_field(name='3', value='- Track Specific Price', inline=False)
    await message.channel.send(embed=generalInfo)
    set_user_state(message.author.id, 'awaiting selection')

@client.event
async def on_message(message: discord.Message):

    # At first prompt both of these will be None
    current_state = get_user_state(message.author.id)
    user_symbol = get_user_symbol(message.author.id)

    if message.author == client.user:
        return

    if message.content.upper().endswith('USDT') and current_state is None:
        set_user_symbol(message.author.id, message.content.upper())
        await mainBoard(message=message)
    elif current_state == 'awaiting selection':
        bt = BinanceTrade(user_symbol)
        bt.run()
        if bt.curr_mkt_price is None:
            await message.channel.send("Failed to retrieve data.")
            return
        if message.content == "1":
            # Chekcing if the dictionary is not empty
            if user_symbol:
                embed = discord.Embed(title='Peak Notification (USDT)', description='track peak', color=0x00ff00)
                embed.add_field(name='SYMBOL: ', value=user_symbol, inline=False)
                embed.add_field(name='Price: ', value=f'${bt.curr_mkt_price}', inline=False)
                embed.add_field(name='Time(UTC): ', value=f'{bt.getEventTime()}', inline=False)
                embed.add_field(name='Historical Peak', value=f'${bt.getHistoricalPeak()}', inline=False)
                await message.channel.send(embed=embed)
            else:
                message.channel.send('No cryptocurrency symbol selected.')
        elif message.content == "2":
            if user_symbol:
                trackPeak = discord.Embed(title='Track Highest Peak', description='---BEGIN---', color=0x00ff00)
                trackPeak.add_field(name='Current Highest Peak (Price): ', value=f'${bt.getHistoricalPeak()}', inline=False)
                await message.channel.send(embed=trackPeak)

                if bt.note_highest_peak():
                    await message.channel.send('CAUTION!!! The price has reached the peak')
        elif message.content == "3":
            if user_symbol:
                await message.channel.send('Enter the specific price you would like to track: ')
                set_user_state(message.author.id, 'awaiting specific price')
        else:
            await message.channel.send('Invalid Choice')
    elif current_state == 'awaiting specific price':
        bt = BinanceTrade(user_symbol)
        bt.run()
        try:
            specific_price = float(message.content)  # Convert input to float
            set_user_specific_price(message.author.id, specific_price)
            await message.channel.send(f"Tracking price set to ${specific_price}.\nCurrent market price ${bt.curr_mkt_price}")
            if bt.note_specific_price(specific_price):
                await message.channel.send(f'Alert!!!! The price has reached ${specific_price}')
            set_user_state(message.author.id, None)  # Reset state after handling
        except ValueError:
            await message.channel.send("Please enter a valid price.")
    else:
        await message.channel.send('Please include "USDT" in your query.')



client.run(DISCORD_API)