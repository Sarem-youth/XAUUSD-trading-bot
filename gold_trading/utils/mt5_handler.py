import MetaTrader5 as mt5
from typing import Dict, Any
import logging

class MT5Handler:
    def __init__(self, account: str, password: str, server: str):
        self.account = account
        self.password = password
        self.server = server
        self.logger = logging.getLogger(__name__)

    def initialize(self) -> bool:
        if not mt5.initialize():
            self.logger.error("MT5 initialization failed")
            return False
            
        authorized = mt5.login(self.account, password=self.password, server=self.server)
        if not authorized:
            self.logger.error(f"MT5 login failed: {mt5.last_error()}")
            return False
            
        return True

    def place_order(self, symbol: str, order_type: str, volume: float, price: float = 0.0, 
                   sl: float = 0.0, tp: float = 0.0) -> Dict[str, Any]:
        request = {
            "action": mt5.TRADE_ACTION_DEAL,
            "symbol": symbol,
            "volume": volume,
            "type": mt5.ORDER_TYPE_BUY if order_type == "BUY" else mt5.ORDER_TYPE_SELL,
            "price": price,
            "sl": sl,
            "tp": tp,
            "magic": 234000,
            "comment": "gold bot order",
            "type_time": mt5.ORDER_TIME_GTC,
            "type_filling": mt5.ORDER_FILLING_IOC,
        }
        
        result = mt5.order_send(request)
        if result.retcode != mt5.TRADE_RETCODE_DONE:
            self.logger.error(f"Order failed: {result.comment}")
            return {"success": False, "error": result.comment}
            
        return {"success": True, "order": result}

    def close_position(self, ticket: int) -> bool:
        position = mt5.positions_get(ticket=ticket)
        if position:
            close_request = {
                "action": mt5.TRADE_ACTION_DEAL,
                "symbol": position.symbol,
                "volume": position.volume,
                "type": mt5.ORDER_TYPE_SELL if position.type == 0 else mt5.ORDER_TYPE_BUY,
                "position": ticket,
                "price": mt5.symbol_info_tick(position.symbol).ask,
                "magic": 234000,
                "comment": "gold bot close",
                "type_time": mt5.ORDER_TIME_GTC,
                "type_filling": mt5.ORDER_FILLING_IOC,
            }
            
            result = mt5.order_send(close_request)
            return result.retcode == mt5.TRADE_RETCODE_DONE
            
        return False
