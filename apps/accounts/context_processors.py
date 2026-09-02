import socket
from .utils import get_active_profile

_CACHED_LOCAL_IP = None

def get_local_ip():
    global _CACHED_LOCAL_IP
    if _CACHED_LOCAL_IP:
        return _CACHED_LOCAL_IP
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.settimeout(0.2)
        s.connect(('8.8.8.8', 80))
        ip = s.getsockname()[0]
        s.close()
        _CACHED_LOCAL_IP = ip
        return ip
    except Exception:
        _CACHED_LOCAL_IP = '127.0.0.1'
        return '127.0.0.1'

def active_profile_context(request):
    profile = None
    if request.user.is_authenticated:
        profile = get_active_profile(request)
        
    local_ip = get_local_ip()
    host_header = request.get_host()
    port = "8000"
    if ":" in host_header:
        port = host_header.split(":")[-1]

    lan_url = f"http://{local_ip}:{port}"
    
    return {
        'active_profile': profile,
        'lan_access_url': lan_url,
        'local_ip': local_ip,
        'server_port': port,
    }
