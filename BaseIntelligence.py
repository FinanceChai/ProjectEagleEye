import os
import requests
import concurrent.futures
from dotenv import load_dotenv
from telegram import Update, Bot
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
                token_info['mark
