import os
import requests
import concurrent.futures
from dotenv import load_dotenv
from telegram import Update
from telegram.ext import Updater, CommandHandler, CallbackContext

# Load environment variables from .env file
load_dotenv()

DEXTOOLS_API_KEY = os.getenv('DEXTOOLS_API_KEY')
TELEGRAM_BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')

def get_token_data(token_address, endpoint=''):
    api_key = DEXTOOLS_API_KEY
    chain = 'base'
    url = f'https://public-api.dextools.io/trial/v2/token/{chain}/{token_address}{endpoint}'

    headers = {
        'X-API-KEY': api_key,
        'accept': 'application/json'
    }

    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        data = response.json()
        return {endpoint: data['data']}
    except requests.exceptions.HTTPError as http_err:
        print(f'HTTP error occurred: {http_err}')
        if response.content:
            print(f'Response content: {response.content}')
    except Exception as err:
        print(f'Other error occurred: {err}')
        if response.content:
            print(f'Response content: {response.content}')
    return None

def get_pool_address(token_address):
    data = get_token_data(token_address, '/pools')
    print(f"Debug: Pools data received: {data}")
    if data and '/pools' in data:
        pools = data['/pools']['results']
        if pools:
            pool_address = pools[0]['address']
            print(f"Debug: Pool address: {pool_address}")
            return pool_address
    return None

def get_pool_price_data(pool_address):
    api_key = DEXTOOLS_API_KEY
    chain = 'base'
    url = f'https://public-api.dextools.io/trial/v2/pool/{chain}/{pool_address}/price'

    headers = {
        'X-API-KEY': api_key,
        'accept': 'application/json'
    }

    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        data = response.json()
        print(f"Debug: Pool price data received: {data}")
        return {'/price': data['data']}
    except requests.exceptions.HTTPError as http_err:
        print(f'HTTP error occurred: {http_err}')
        if response.content:
            print(f'Response content: {response.content}')
    except Exception as err:
        print(f'Other error occurred: {err}')
        if response.content:
            print(f'Response content: {response.content}')
    return None

def print_and_store_token_data(data, token_address, pool_price_data):
    token_info = {
        'name': 'N/A',
        'symbol': 'N/A',
        'website': 'N/A',
        'twitter': 'N/A',
        'price': 'N/A',
        'market cap': 'N/A',
        'holders': 'N/A',
        'locked tokens': 'N/A',
        'price24h': 'N/A',
        'price6h': 'N/A',
        'price1h': 'N/A',
        'price_change_24h': 'N/A',
        'price_change_6h': 'N/A',
        'price_change_1h': 'N/A',
        'audit': {},
        'pool_price': 'N/A'
    }

    if data:
        print("Debug: Data received from API")
        for endpoint, endpoint_data in data.items():
            print(f"Debug: Processing endpoint {endpoint}")
            print(f"Debug: Endpoint data: {endpoint_data}")
            if endpoint == '':
                token_info['name'] = endpoint_data.get('name', 'N/A')
                token_info['symbol'] = endpoint_data.get('symbol', 'N/A')
                token_info['website'] = endpoint_data.get('socialInfo', {}).get('website', 'N/A')
                token_info['twitter'] = endpoint_data.get('socialInfo', {}).get('twitter', 'N/A')
            if endpoint == '/price':
                current_price = endpoint_data.get('price', 'N/A')
                token_info['price'] = current_price
                token_info['price24h'] = endpoint_data.get('price24h', 'N/A')
                token_info['price6h'] = endpoint_data.get('price6h', 'N/A')
                token_info['price1h'] = endpoint_data.get('price1h', 'N/A')
                if current_price != 'N/A' and current_price is not None:
                    current_price = float(current_price)
                    token_info['price_change_24h'] = calculate_percentage_change(current_price, endpoint_data.get('price24h'))
                    token_info['price_change_6h'] = calculate_percentage_change(current_price, endpoint_data.get('price6h'))
                    token_info['price_change_1h'] = calculate_percentage_change(current_price, endpoint_data.get('price1h'))
            if endpoint == '/info':
                token_info['market cap'] = endpoint_data.get('mcap', 'N/A')
                token_info['holders'] = endpoint_data.get('holders', 'N/A')
            if endpoint == '/audit':
                token_info['audit'] = {
                    'isOpenSource': endpoint_data.get('isOpenSource', 'N/A'),
                    'isHoneypot': endpoint_data.get('isHoneypot', 'N/A'),
                    'isMintable': endpoint_data.get('isMintable', 'N/A'),
                    'isProxy': endpoint_data.get('isProxy', 'N/A'),
                    'slippageModifiable': endpoint_data.get('slippageModifiable', 'N/A'),
                    'isBlacklisted': endpoint_data.get('isBlacklisted', 'N/A'),
                    'sellTax': endpoint_data.get('sellTax', {}),
                    'buyTax': endpoint_data.get('buyTax', {}),
                    'isContractRenounced': endpoint_data.get('isContractRenounced', 'N/A'),
                    'isPotentiallyScam': endpoint_data.get('isPotentiallyScam', 'N/A'),
                    'updatedAt': endpoint_data.get('updatedAt', 'N/A')
                }
            if endpoint == '/locks':
                locked_tokens = sum(lock.get('amount', 0) for lock in endpoint_data.get('locks', []))
                token_info['locked tokens'] = locked_tokens

    if pool_price_data:
        print("Debug: Pool price data received from API")
        for endpoint, endpoint_data in pool_price_data.items():
            print(f"Debug: Processing pool price endpoint {endpoint}")
            print(f"Debug: Pool price endpoint data: {endpoint_data}")
            if endpoint == '/price':
                token_info['pool_price'] = endpoint_data.get('price', 'N/A')

    result = (
        f"Name: {token_info['name']}\n"
        f"🔍 Symbol: {token_info['symbol']}\n"
        f"Website: {token_info['website']}\n"
        f"Twitter: {token_info['twitter']}\n"
        f"Px: ${format_value(token_info['price'])}\n"
        f"Market cap: ${format_value(token_info['market cap'])}\n"
        f"Holders: {format_value(token_info['holders'])}\n"
        f"Locked tokens: {format_value(token_info['locked tokens'])}\n"
        f"Pool Price: {format_value(token_info['pool_price'])}\n"
        f"Price change 1h: {token_info['price_change_1h']}\n"
        f"Price change 6h: {token_info['price_change_6h']}\n"
        f"Price change 24h: {token_info['price_change_24h']}\n"
        f"\nAudit Information:\n"
    )

    for key, value in token_info['audit'].items():
        result += f"{key}: {value}\n"

    result += (
        f"\n[TweetScout](https://app.tweetscout.io/search?q=apetardio) | "
        f"[DEXTools](https://www.dextools.io/app/en/base/pair-explorer/{token_address}) | "
        f"[Basescan](https://basescan.org/address/{token_address})\n"
        f"\n**Contract Address:** {token_address}\n"
    )

    return result

def calculate_percentage_change(current_price, previous_price):
    if previous_price is None or previous_price == 'N/A':
        return 'N/A'
    try:
        previous_price = float(previous_price)
        if previous_price == 0:
            return
