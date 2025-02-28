from django.core.management.base import BaseCommand
import asyncio
import websockets
import json
import logging
from django.utils import timezone
from decimal import Decimal
from apps.trading.models import TradingPair

logger = logging.getLogger(__name__)

class Command(BaseCommand):
    help = 'Start MCX market data feed WebSocket connection'

    def add_arguments(self, parser):
        parser.add_argument(
            '--verbose',
            action='store_true',
            help='Show detailed output'
        )

    def handle(self, *args, **options):
        self.verbose = options['verbose']
        self.stdout.write('Starting MCX market data feed...')
        asyncio.run(self.run_websocket())

    async def run_websocket(self):
        """Run the WebSocket connection"""
        ws_url = "ws://78.46.93.146:8084"
        
        while True:
            try:
                async with websockets.connect(ws_url) as websocket:
                    self.stdout.write(self.style.SUCCESS('Connected to MCX WebSocket'))
                    
                    while True:
                        try:
                            message = await websocket.recv()
                            await self.process_message(message)
                        except websockets.ConnectionClosed:
                            self.stdout.write(self.style.WARNING('Connection closed, reconnecting...'))
                            break
                        except Exception as e:
                            logger.error(f"Error processing message: {str(e)}")
                            continue
                            
            except Exception as e:
                logger.error(f"Connection error: {str(e)}")
                self.stdout.write(self.style.ERROR(f'Connection failed: {str(e)}'))
                await asyncio.sleep(5)  # Wait before retrying

    async def process_message(self, message):
        """Process incoming market data message"""
        try:
            data = json.loads(message)
            for item in data:
                if len(item) < 10:
                    continue
                
                # Extract data from message
                symbol = item[0]
                name = item[1]
                
                try:
                    # Handle potential invalid decimal values
                    open_price = Decimal(str(item[2])) if item[2] not in ['', None] else None
                    low_price = Decimal(str(item[3])) if item[3] not in ['', None] else None
                    high_price = Decimal(str(item[4])) if item[4] not in ['', None] else None
                    close_price = Decimal(str(item[5])) if item[5] not in ['', None] else None
                    last_price = Decimal(str(item[6])) if item[6] not in ['', None] else None
                    bid_price = Decimal(str(item[7])) if item[7] not in ['', None] else None
                    ask_price = Decimal(str(item[8])) if item[8] not in ['', None] else None
                    timestamp = item[9]
                    
                    # Update or create trading pair
                    base_asset = symbol.replace('FUT', '').strip()
                    quote_asset = 'INR'
                    
                    pair = await self.get_or_create_pair(base_asset, quote_asset)
                    await self.update_pair_data(
                        pair,
                        last_price=last_price,
                        bid_price=bid_price,
                        ask_price=ask_price,
                        high_price=high_price,
                        low_price=low_price,
                        open_price=open_price,
                        close_price=close_price,
                        timestamp=timestamp
                    )
                    
                    if self.verbose:
                        self.stdout.write(
                            self.style.SUCCESS(
                                f'Updated {symbol}: Last: {last_price}, Bid: {bid_price}, Ask: {ask_price}'
                            )
                        )
                        
                except Exception as e:
                    logger.error(f"Error updating {symbol}: {str(e)}")
                    
        except json.JSONDecodeError:
            logger.error("Invalid JSON message received")
        except Exception as e:
            logger.error(f"Error processing message: {str(e)}")

    async def get_or_create_pair(self, base_asset, quote_asset):
        """Get or create trading pair"""
        try:
            pair = await TradingPair.objects.aget_or_create(
                base_asset=base_asset,
                quote_asset=quote_asset,
                defaults={
                    'min_trade_size': Decimal('0.01'),
                    'price_precision': 2,
                    'is_active': True
                }
            )
            return pair[0]
        except Exception as e:
            logger.error(f"Error getting/creating pair: {str(e)}")
            raise

    async def update_pair_data(self, pair, **kwargs):
        """Update trading pair with new market data"""
        try:
            for key, value in kwargs.items():
                if value is not None:  # Only update if value is not None
                    setattr(pair, key, value)
            pair.last_updated = timezone.now()
            await pair.asave()
        except Exception as e:
            logger.error(f"Error updating pair data: {str(e)}")
            raise
