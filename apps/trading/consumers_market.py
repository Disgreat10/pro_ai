import json
import asyncio
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from .models import TradingPair

class MarketDataConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        """Handle WebSocket connection"""
        try:
            print(f"New WebSocket connection attempt from {self.scope['client']}")
            await self.accept()
            self.should_send = True
            print(f"WebSocket connection accepted for {self.scope['client']}")
            asyncio.create_task(self.send_market_data())
        except Exception as e:
            print(f"Error during WebSocket connection: {str(e)}")
            raise

    async def disconnect(self, close_code):
        """Handle WebSocket disconnection"""
        print(f"WebSocket disconnected with code {close_code} for {self.scope['client']}")
        self.should_send = False

    async def send_market_data(self):
        """Send market data updates periodically"""
        print(f"Starting market data stream for {self.scope['client']}")
        while self.should_send:
            try:
                pairs = await self.get_trading_pairs()
                print(f"Retrieved {len(pairs)} trading pairs")
                
                for pair in pairs:
                    if not self.should_send:
                        print("Stopping market data stream - disconnected")
                        break
                        
                    data = {
                        'type': 'market_data',
                        'symbol': pair['symbol'],
                        'data': {
                            'last_price': str(pair['last_price']),
                            'bid': str(pair['bid_price']),
                            'ask': str(pair['ask_price']),
                            'high': str(pair['high_price']),
                            'low': str(pair['low_price']),
                            'open': str(pair['open_price']),
                            'close': str(pair['close_price']),
                            'volume': str(pair['volume_24h']),
                            'timestamp': pair['last_updated'].isoformat() if pair['last_updated'] else None
                        }
                    }
                    
                    try:
                        await self.send(text_data=json.dumps(data))
                        print(f"Sent market data for {pair['symbol']}")
                    except Exception as send_error:
                        print(f"Error sending market data: {str(send_error)}")
                        self.should_send = False
                        break
                        
                    await asyncio.sleep(0.1)  # Small delay between each symbol
                    
                if self.should_send:
                    await asyncio.sleep(1)  # Wait before next update cycle
                
            except Exception as e:
                print(f"Error in market data consumer: {str(e)}")
                print(f"Connection state: {self.should_send}")
                print(f"Client: {self.scope['client']}")
                await asyncio.sleep(5)  # Wait longer on error

    @database_sync_to_async
    def get_trading_pairs(self):
        """Get all active trading pairs with their latest data"""
        pairs = TradingPair.objects.filter(is_active=True).values(
            'base_asset', 'quote_asset', 'last_price', 'bid_price',
            'ask_price', 'high_price', 'low_price', 'open_price',
            'close_price', 'volume_24h', 'last_updated'
        )
        
        return [{
            'symbol': f"{pair['base_asset']}/{pair['quote_asset']}",
            **pair
        } for pair in pairs]
