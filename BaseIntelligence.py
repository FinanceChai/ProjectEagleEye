import os
import requests
import concurrent.futures
from dotenv import load_dotenv
from telegram import Update, Bot, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, CallbackContext
import logging

# Load environment variables from .env file
load_dotenv()

DEXTOOLS_API_KEY = os.getenv('DEXTOOLS_API_KEY')
TELEGRAM_BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')

logging.basicConfig(level=logging.INFO)

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
        'telegram': 'N/A',
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
                token_info['telegram'] = endpoint_data.get('socialInfo', {}).get('telegram', 'N/A')
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
                    '📄 isOpenSource': endpoint_data.get('isOpenSource', 'N/A'),
                    '🍯 isHoneypot': endpoint_data.get('isHoneypot', 'N/A'),
                    '🍃 isMintable': endpoint_data.get('isMintable', 'N/A'),
                    '👯 isProxy': endpoint_data.get('isProxy', 'N/A'),
                    '🥿 slippageModifiable': endpoint_data.get('slippageModifiable', 'N/A'),
                    '👎🏼 isBlacklisted': endpoint_data.get('isBlacklisted', 'N/A'),
                    '🫰🏼 sellTax': endpoint_data.get('sellTax', {}),
                    '🫰🏼 buyTax': endpoint_data.get('buyTax', {}),
                    '🔨 isContractRenounced': endpoint_data.get('isContractRenounced', 'N/A'),
                    '🚫 isPotentiallyScam': endpoint_data.get('isPotentiallyScam', 'N/A'),
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

    # Generate the result message
    result = (
        f"📑 Name: {token_info['name']}\n"
        f"🔍 Symbol: {token_info['symbol']}\n"
        f"\n🕸️ [Website]({token_info['website']}) | 🐥 [Twitter]({token_info['twitter']}) | 📢 [Telegram]({token_info['telegram']})\n"
        f"\n💰 Px: ${format_value(token_info['price'])}\n"
        f"💲 Market cap: ${format_value(token_info['market cap'])}\n"
        f"✊🏼 Holders: {format_value(token_info['holders'])}\n"
        f"🔥 Locked tokens: {format_value(token_info['locked tokens'])}\n"
        f"\n📈 Px change: 1hr - {token_info['price_change_1h']} | 6hr - {token_info['price_change_6h']} | 24hr - {token_info['price_change_24h']}\n"
        f"\nAudit Information:\n" +
        "\n".join([f"{key}: {value}" for key, value in token_info['audit'].items()]) +
        f"\n\n[TweetScout](https://app.tweetscout.io/search?q=apetardio) | [DEXTools](https://www.dextools.io/app/en/base/pair-explorer/{token_address}) | [Basescan](https://basescan.org/address/{token_address}) | [BubbleMaps](https://app.bubblemaps.io/base/token/{token_address})\n"
        f"\nContract Address: **[{token_address}](https://basescan.org/address/{token_address})**"
    )

    keyboard = [
        [InlineKeyboardButton("🍌 Banana Gun", url="https://t.me/BananaGunSniper_bot?start=ref_rubberd"),
         InlineKeyboardButton("😎 Prodigy bot", url="https://t.me/ProdigySniperBot?start=G7K13A")]
    ]
    
    return result, InlineKeyboardMarkup(keyboard)

def calculate_percentage_change(current_price, previous_price):
    if previous_price is None or previous_price == 'N/A':
        return 'N/A'
    try:
        previous_price = float(previous_price)
        if previous_price == 0:
            return 'N/A'
        change = ((current_price - previous_price) / previous_price) * 100
        return f"{change:.1f}%"
    except ValueError:
        return 'N/A'

def format_value(value):
    try:
        if value is None or value == 'N/A':
            return 'N/A'
        value = float(value)
        return f"{value:,.6f}" if value < 1 else f"{value:,.0f}"
    except ValueError:
        return value

async def handle_search(update: Update, context: CallbackContext) -> None:
    token_address = context.args[0] if context.args else None
    if not token_address:
        await update.message.reply_text('Please provide a contract address.')
        return

    endpoints = ['', '/price', '/info', '/audit', '/locks']
    
    # Run the requests concurrently
    with concurrent.futures.ThreadPoolExecutor() as executor:
        future_to_endpoint = {executor.submit(get_token_data, token_address, endpoint): endpoint for endpoint in endpoints}
        token_data = {}
        for future in concurrent.futures.as_completed(future_to_endpoint):
            endpoint = future_to_endpoint[future]
            try:
                data = future.result()
                if data:
                    print(f"Debug: Data received for {endpoint}")
                    token_data.update(data)
            except Exception as exc:
                print(f'{endpoint} generated an exception: {exc}')

    pool_address = get_pool_address(token_address)
    pool_price_data = None
    if pool_address:
        pool_price_data = get_pool_price_data(pool_address)
    
    result, keyboard = print_and_store_token_data(token_data, token_address, pool_price_data)
    await update.message.reply_text(result, parse_mode='Markdown', disable_web_page_preview=True, reply_markup=keyboard)

def main() -> None:
    application = ApplicationBuilder().token(TELEGRAM_BOT_TOKEN).build()

    search_handler = CommandHandler('search', handle_search)
    application.add_handler(search_handler)

    application.run_polling()

if __name__ == '__main__':
    main()
