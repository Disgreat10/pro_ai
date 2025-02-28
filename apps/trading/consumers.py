import json
import asyncio
import websockets
import logging
from channels.generic.websocket import AsyncWebsocketConsumer
from asgiref.sync import sync_to_async
from django.utils import timezone
from decimal import Decimal
from .models import TradingPair

logger = logging.getLogger(__name__)

class MCXMarketDataConsumer(AsyncWebsocketConsumer):
    MCX_WS_URL = "ws://78.46.93.146:8084"
    
    async def connect(self):
        """
        Connect to the WebSocket server and start receiving market data
        """
        await self.accept()
        self.mcx_connection = None
        self.is_running = True
        
        # Start the MCX data feed
        asyncio.create_task(self.connect_to_mcx())

    async def disconnect(self, close_code):
        """
        Clean up connections on disconnect
        """
        self.is_running = False
        if self.mcx_connection:
            await self.mcx_connection.close()

    async def connect_to_mcx(self):
        """
        Connect to MCX WebSocket and handle incoming data
        """
        while self.is_running:
            try:
                async with websockets.connect(self.MCX_WS_URL) as websocket:
                    self.mcx_connection = websocket
                    logger.info("Connected to MCX WebSocket")
                    
                    while self.is_running:
                        try:
                            message = await websocket.recv()
                            await self.process_mcx_data(message)
                        except websockets.ConnectionClosed:
                            logger.warning("MCX WebSocket connection closed")
                            break
                        except Exception as e:
                            logger.error(f"Error processing MCX data: {str(e)}")
                            continue
                            
            except Exception as e:
                logger.error(f"Error connecting to MCX: {str(e)}")
                await asyncio.sleep(5)  # Wait before retrying

    async def process_mcx_data(self, message):
        """
        Process incoming MCX market data
        Format: [symbol, name, open, low, high, close, ltp, bid, ask, timestamp, extra]
        """
        try:
            data = json.loads(message)
            for item in data:
                if len(item) < 10:
                    continue
                    
                symbol = item[0]
                trading_pair = await self.get_or_create_trading_pair(symbol)
                
                # Update trading pair data
                updates = {
                    'last_price': Decimal(str(item[6])),  # LTP
                    'bid_price': Decimal(str(item[7])),
                    'ask_price': Decimal(str(item[8])),
                    'high_price': Decimal(str(item[4])),
                    'low_price': Decimal(str(item[3])),
                    'open_price': Decimal(str(item[2])),
                    'close_price': Decimal(str(item[5])),
                    'last_updated': timezone.now()
                }
                
                await self.update_trading_pair(trading_pair.id, updates)
                
                # Broadcast the update to connected clients
                await self.send(text_data=json.dumps({
                    'type': 'market_data',
                    'symbol': symbol,
                    'data': {
                        'last_price': str(updates['last_price']),
                        'bid': str(updates['bid_price']),
                        'ask': str(updates['ask_price']),
                        'high': str(updates['high_price']),
                        'low': str(updates['low_price']),
                        'open': str(updates['open_price']),
                        'close': str(updates['close_price']),
                        'timestamp': item[9]
                    }
                }))
                
        except Exception as e:
            logger.error(f"Error processing MCX data: {str(e)}")

    @sync_to_async
    def get_or_create_trading_pair(self, symbol):
        """
        Get or create a trading pair from MCX symbol
        """
        # Extract base and quote assets from symbol (you may need to adjust this based on your symbol format)
        base_asset = symbol.replace('FUT', '').strip()
        quote_asset = 'INR'  # MCX typically quotes in INR
        
        trading_pair, created = TradingPair.objects.get_or_create(
            base_asset=base_asset,
            quote_asset=quote_asset,
            defaults={
                'min_trade_size': Decimal('0.01'),
                'price_precision': 2,
                'is_active': True
            }
        )
        
        return trading_pair

    @sync_to_async
    def update_trading_pair(self, pair_id, updates):
        """
        Update trading pair with new market data
        """
        TradingPair.objects.filter(id=pair_id).update(**updates)
