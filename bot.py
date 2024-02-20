import requests
import asyncio
from telegram import Bot
from emoji import emojize
import time

bot_token = "7165336794:AAFn0S4mbtHGBh4nkZb1zxllJWQtBg6QWG0"
chat_id = "-1001625368792"

# Fungsi untuk mengirim pesan ke grup Telegram
async def send_telegram_message(message):
    bot = Bot(token=bot_token)
    await bot.send_message(chat_id=chat_id, text=message, parse_mode="HTML")
    print("Sending Notification")

# Fungsi untuk mendapatkan semua pasangan kripto di Indodax
def get_all_pairs():
    api_url = 'https://indodax.com/api/pairs'
    response = requests.get(api_url)
    data = response.json()
    return [pair['symbol'] for pair in data]

# Fungsi untuk mendapatkan harga kripto
def get_crypto_price(pair):
    api_url = f'https://indodax.com/api/ticker/{pair.lower()}'
    response = requests.get(api_url)

    if response.status_code == 200:
        data = response.json()
        last_price = float(data.get('ticker', {}).get('last', 0))
        return last_price
    else:
        return None

# Fungsi untuk memonitor kenaikan atau penurunan harga
async def monitor_price_change(threshold_percent=5, interval=5, blacklist_price=15):
    all_pairs = get_all_pairs()
    initial_prices = {}

    print("Initiating Bot...")
    print("Bot is running... Monitoring Price change..")

    while True:
        start_time = time.time()  # Waktu awal permintaan
        for pair in all_pairs:
            current_price = get_crypto_price(pair)

            # Skip pair dengan harga di bawah threshold untuk IDR
            if pair.endswith('idr') and current_price is not None and current_price < blacklist_price:
                continue

            if current_price is not None:
                initial_price = initial_prices.get(pair, current_price)

                if initial_price != 0:
                    percentage_change = ((current_price - initial_price) / initial_price) * 100
                    change_type = 'naik' if percentage_change > 0 else 'turun'
                    percentage_change = abs(percentage_change)
                    if percentage_change >= threshold_percent:
                        chart_link = f'<a href="https://indodax.com/chart/{pair.upper()}">{pair.upper()}</a>'
                        if pair.endswith('usdt'):
                            price_text = f"USD ${current_price:.8f}" if current_price >= 0.01 else f"USD ${current_price:.8e}"
                        else:
                            price_text = f"Rp.{current_price:,.0f}"
                        if change_type == 'naik':
                            emoji = emojize(":rocket:")
                            message = f"{chart_link} Harga {change_type} {emoji} <code>+{percentage_change:.2f}%</code> " \
                                      f"(harga sekarang: {price_text})"
                        else:
                            emoji = emojize(":fire:")
                            message = f"{chart_link} Harga {change_type} {emoji} <code>-{percentage_change:.2f}%</code> " \
                                      f"(harga sekarang: {price_text})"
                        await send_telegram_message(message)

                initial_prices[pair] = current_price

        elapsed_time = time.time() - start_time  # Waktu yang dibutuhkan untuk satu iterasi
        if elapsed_time < interval:  # Menunggu sisa waktu interval
            await asyncio.sleep(interval - elapsed_time)

# Fungsi untuk melakukan koneksi ulang ke API Indodax
async def reconnect_indodax():
    print("Checking connection to Indodax API...")
    while True:
        try:
            start_time = time.time()
            response = requests.get("https://indodax.com/api/pairs")
            latency = time.time() - start_time
            if response.status_code == 200:
                print(f"Indodax API > OK ({latency} seconds)")
                return True
            else:
                print(f"Indodax API > Fail ({latency} seconds)")
        except Exception as e:
            print(f"Error checking connection to Indodax API: {str(e)}")
        await asyncio.sleep(10)  # Delay 10 detik sebelum mencoba kembali

# Fungsi untuk mengecek koneksi bot
async def check_bot_connection():
    print("Checking connection to Telegram Bot...")
    while True:
        try:
            start_time = time.time()
            response = requests.get("https://api.telegram.org")
            latency = time.time() - start_time
            if response.status_code == 200:
                print(f"Telegram Bot > OK ({latency} seconds)")
                return True
            else:
                print(f"Telegram Bot > Fail ({latency} seconds)")
        except Exception as e:
            print(f"Error checking bot connection: {str(e)}")
        await asyncio.sleep(10)  # Delay 10 detik sebelum mencoba kembali

# Fungsi untuk mengecek koneksi secara keseluruhan
async def check_connection():
    indodax_ok = await reconnect_indodax()
    bot_ok = await check_bot_connection()
    if indodax_ok and bot_ok:
        return True
    else:
        return False

async def main():
    try:
        while True:
            connection_ok = await check_connection()
            if connection_ok:
                await monitor_price_change()
            else:
                print("Connection failed. Retrying...")
    except Exception as e:
        print(f"An error occurred: {str(e)}")

if __name__ == '__main__':
    asyncio.run(main())
