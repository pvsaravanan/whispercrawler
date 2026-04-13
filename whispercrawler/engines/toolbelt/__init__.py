from whispercrawler.proxy import ProxyWheel as ProxyRotator

from .proxy_rotation import cyclic_rotation, is_proxy_error

__all__ = ["ProxyRotator", "is_proxy_error", "cyclic_rotation"]
