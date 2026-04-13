import webbrowser
from typing import Any
from vnstock import Vnstock
import pandas as pd
from datetime import datetime, timedelta


class CleanChartHandler:

    def __init__(self, assistant: Any):
        self.assistant = assistant
        self.vn_exchanges = {'HOSE': ['HPG', 'VCB', 'PLX', 'FPT', 'MWG',
            'VNM'], 'HNX': ['SHS', 'PVS', 'IDC'], 'UPCOM': ['VGI', 'ACV']}

    def detect_exchange(self, symbol: str) ->str:
        symbol = symbol.upper()
        for exchange, symbols in self.vn_exchanges.items():
            if symbol in symbols:
                return exchange
        return 'HOSE'

    def get_candle_data(self, symbol: str, exchange: str, days: int=15):
        try:
            stock = Vnstock().stock(symbol=symbol, source='VCI')
            end_date = datetime.now()
            start_date = end_date - timedelta(days=days * 2)
            df = stock.quote.history(start=start_date.strftime('%Y-%m-%d'),
                end=end_date.strftime('%Y-%m-%d'), interval='1D')
            if df.empty:
                return pd.DataFrame()
            df = df.tail(days)
            return df[['time', 'open', 'high', 'low', 'close', 'volume']]
        except Exception as e:
            print(f'⚠️ Lỗi khi lấy dữ liệu {symbol}: {e}')
            return pd.DataFrame()

    def get_all_candles(self, days: int=1):
        all_data = []
        for exchange, symbols in self.vn_exchanges.items():
            for sym in symbols:
                print(f'📥 Đang lấy {sym} ({exchange})...')
                df = self.get_candle_data(sym, exchange, days)
                if not df.empty:
                    df['symbol'] = sym
                    df['exchange'] = exchange
                    all_data.append(df)
        if all_data:
            return pd.concat(all_data, ignore_index=True)
        else:
            print('❌ Không lấy được dữ liệu.')
            return pd.DataFrame()

    def can_handle(self, command: str) ->bool:
        return command.startswith('chart') or command.startswith('tv'
            ) or command.startswith('getdata')

    def handle(self, command: str) ->None:
        try:
            parts = command.split()
            if len(parts) < 2:
                print(
                    '❗ Cách dùng: chart HPG          # mở TradingView + FireAnt'
                    )
                print(
                    '            getdata all         # lấy dữ liệu nến tất cả cổ phiếu'
                    )
                print(
                    '            getdata HPG         # lấy dữ liệu riêng một mã'
                    )
                return
            sub_cmd = parts[1].lower()
            if sub_cmd == 'all':
                print('🔄 Đang thu thập dữ liệu nến cho tất cả cổ phiếu...')
                df = self.get_all_candles(days=1)
                if not df.empty:
                    print('\n📊 Kết quả (giá mở cửa, đóng cửa):')
                    print(df[['symbol', 'exchange', 'time', 'open', 'close',
                        'volume']].to_string(index=False))
                    df.to_csv('candle_data.csv', index=False, encoding='utf-8')
                    print('\n✅ Đã lưu vào candle_data.csv')
                else:
                    print('Không có dữ liệu.')
                return
            symbol = parts[1].upper()
            if ':' in symbol:
                print(f'📈 Mở TradingView cho {symbol}')
                webbrowser.open(
                    f'https://www.tradingview.com/chart/?symbol={symbol}')
                return
            exchange = self.detect_exchange(symbol)
            print(f'📊 Lấy dữ liệu nến cho {symbol}...')
            df = self.get_candle_data(symbol, exchange, days=245)
            if not df.empty:
                print(df[['time', 'open', 'high', 'low', 'close', 'volume']
                    ].to_string(index=False))
            else:
                print(f'Không có dữ liệu cho {symbol}')
            if command.startswith('chart') or command.startswith('tv'):
                self.open_tradingview(symbol, exchange)
                self.open_fireant(symbol)
        except Exception as e:
            print(f'⚠️ Lỗi: {e}')

    def open_tradingview(self, symbol: str, exchange: str):
        tv_symbol = f'{exchange}:{symbol}'
        url = f'https://www.tradingview.com/chart/?symbol={tv_symbol}'
        print(f'📈 TradingView: {tv_symbol}')
        webbrowser.open(url)

    def open_fireant(self, symbol: str):
        url = f'https://fireant.vn/ma-chung-khoan/{symbol}'
        print(f'🔥 FireAnt: {symbol}')
        webbrowser.open(url)


def register(assistant: Any):
    assistant.handlers.append(CleanChartHandler(assistant))


plugin_info = {'enabled': True, 'register': register, 'command_handle': [
    'chart', 'tv', 'getdata']}
