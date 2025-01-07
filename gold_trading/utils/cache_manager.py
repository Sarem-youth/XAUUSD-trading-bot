from datetime import datetime, timedelta
from typing import Dict, Any
import logging

class CacheManager:
    def __init__(self, cache_duration: int = 900):
        self.cache: Dict[str, Dict[str, Any]] = {}
        self.cache_duration = cache_duration
        self.logger = logging.getLogger(__name__)

    def get(self, key: str) -> Any:
        if key in self.cache:
            entry = self.cache[key]
            if datetime.now() < entry['expiry']:
                return entry['data']
        return None

    def set(self, key: str, data: Any) -> None:
        self.cache[key] = {
            'data': data,
            'expiry': datetime.now() + timedelta(seconds=self.cache_duration)
        }

    def clear_expired(self) -> None:
        now = datetime.now()
        expired_keys = [k for k, v in self.cache.items() if v['expiry'] < now]
        for k in expired_keys:
            del self.cache[k]
