"""
WebSocket Production Configuration
Handles environment-based configuration, SSL/WSS support, and production settings
"""

import os
import ssl
import logging
from typing import List, Dict, Any, Optional
from dataclasses import dataclass

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@dataclass
class WebSocketConfig:
    """WebSocket configuration settings"""
    host: str = "0.0.0.0"
    port: int = 8000
    path: str = "/socket.io/"
    cors_allowed_origins: List[str] = None
    ssl_enabled: bool = False
    ssl_cert_path: Optional[str] = None
    ssl_key_path: Optional[str] = None
    environment: str = "development"
    max_connections: int = 1000
    ping_timeout: int = 60
    ping_interval: int = 25
    log_level: str = "INFO"
    
    def __post_init__(self):
        """Initialize default CORS origins if none provided"""
        if self.cors_allowed_origins is None:
            self.cors_allowed_origins = self._get_default_cors_origins()
    
    def _get_default_cors_origins(self) -> List[str]:
        """Get default CORS origins based on environment"""
        if self.environment == "production":
            # Production origins - customize these for your deployment
            cors_origins = []
            
            # Get from environment variable (comma-separated)
            env_origins = os.getenv('CORS_ORIGINS', '')
            if env_origins:
                cors_origins.extend([origin.strip() for origin in env_origins.split(',')])
            
            # Default production origins if none specified
            if not cors_origins:
                cors_origins = [
                    "https://*.vercel.app",
                    "https://*.herokuapp.com",
                    "https://*.railway.app",
                    "https://*.render.com"
                ]
            
            return cors_origins
        else:
            # Development origins
            return [
                "http://localhost:3000",
                "http://localhost:3001",
                "http://127.0.0.1:3000",
                "http://127.0.0.1:3001",
                "https://localhost:3000",
                "https://localhost:3001",
                "https://127.0.0.1:3000",
                "https://127.0.0.1:3001"
            ]
    
    def get_ssl_context(self) -> Optional[ssl.SSLContext]:
        """Create SSL context for WSS support"""
        if not self.ssl_enabled or not self.ssl_cert_path or not self.ssl_key_path:
            return None
        
        try:
            context = ssl.create_default_context(ssl.Purpose.CLIENT_AUTH)
            context.load_cert_chain(self.ssl_cert_path, self.ssl_key_path)
            logger.info(f"SSL context created with cert: {self.ssl_cert_path}")
            return context
        except Exception as e:
            logger.error(f"Failed to create SSL context: {e}")
            return None
    
    def get_socket_io_config(self) -> Dict[str, Any]:
        """Get Socket.IO server configuration"""
        config = {
            'async_mode': 'asgi',
            'cors_allowed_origins': self.cors_allowed_origins,
            'ping_timeout': self.ping_timeout,
            'ping_interval': self.ping_interval,
            'max_http_buffer_size': 1000000,  # 1MB for audio data
            'logger': self.environment != "production",
            'engineio_logger': self.environment != "production"
        }
        
        # Add SSL context if enabled
        ssl_context = self.get_ssl_context()
        if ssl_context:
            config['ssl_context'] = ssl_context
        
        return config
    
    def get_uvicorn_config(self) -> Dict[str, Any]:
        """Get Uvicorn server configuration"""
        config = {
            'host': self.host,
            'port': self.port,
            'log_level': self.log_level.lower(),
            'access_log': self.environment != "production",
            'server_header': False,  # Hide server header for security
            'date_header': False     # Hide date header for security
        }
        
        # Add SSL configuration for WSS
        ssl_context = self.get_ssl_context()
        if ssl_context:
            config['ssl_keyfile'] = self.ssl_key_path
            config['ssl_certfile'] = self.ssl_cert_path
        
        return config


class ProductionErrorHandler:
    """Enhanced error handling for production environment"""
    
    def __init__(self, config: WebSocketConfig):
        self.config = config
        self.logger = logging.getLogger(__name__)
    
    def handle_websocket_error(self, error: Exception, session_id: str = None) -> Dict[str, Any]:
        """Handle WebSocket errors with appropriate logging and response"""
        error_id = f"ws_error_{hash(str(error))}"
        
        # Log error with details
        self.logger.error(
            f"WebSocket error {error_id}: {str(error)}", 
            extra={
                'session_id': session_id,
                'error_type': type(error).__name__,
                'environment': self.config.environment
            }
        )
        
        # Return sanitized error response
        if self.config.environment == "production":
            return {
                'error': 'Internal server error',
                'error_id': error_id,
                'timestamp': self._get_timestamp()
            }
        else:
            return {
                'error': str(error),
                'error_id': error_id,
                'error_type': type(error).__name__,
                'timestamp': self._get_timestamp()
            }
    
    def handle_api_error(self, service: str, error: Exception) -> Dict[str, Any]:
        """Handle external API errors"""
        error_id = f"api_error_{hash(f'{service}_{str(error)}')}"
        
        self.logger.error(
            f"API error from {service} {error_id}: {str(error)}",
            extra={
                'service': service,
                'error_type': type(error).__name__,
                'environment': self.config.environment
            }
        )
        
        return {
            'error': f'Service temporarily unavailable: {service}',
            'error_id': error_id,
            'service': service,
            'timestamp': self._get_timestamp()
        }
    
    def _get_timestamp(self) -> str:
        """Get current timestamp"""
        from datetime import datetime
        return datetime.now().isoformat()


class ConnectionManager:
    """Manage WebSocket connections with rate limiting and monitoring"""
    
    def __init__(self, config: WebSocketConfig):
        self.config = config
        self.connections: Dict[str, Dict[str, Any]] = {}
        self.connection_counts: Dict[str, int] = {}
        self.logger = logging.getLogger(__name__)
    
    def can_connect(self, client_ip: str) -> bool:
        """Check if client can connect based on rate limits"""
        if len(self.connections) >= self.config.max_connections:
            self.logger.warning(f"Connection limit reached: {len(self.connections)}")
            return False
        
        # Rate limiting: max 10 connections per IP
        ip_connections = self.connection_counts.get(client_ip, 0)
        if ip_connections >= 10:
            self.logger.warning(f"IP connection limit reached for {client_ip}")
            return False
        
        return True
    
    def add_connection(self, session_id: str, client_ip: str):
        """Add new connection"""
        self.connections[session_id] = {
            'ip': client_ip,
            'connected_at': self._get_timestamp(),
            'last_activity': self._get_timestamp()
        }
        self.connection_counts[client_ip] = self.connection_counts.get(client_ip, 0) + 1
        self.logger.info(f"New connection: {session_id} from {client_ip}")
    
    def remove_connection(self, session_id: str):
        """Remove connection"""
        if session_id in self.connections:
            client_ip = self.connections[session_id]['ip']
            del self.connections[session_id]
            self.connection_counts[client_ip] = max(0, self.connection_counts.get(client_ip, 1) - 1)
            self.logger.info(f"Connection removed: {session_id}")
    
    def update_activity(self, session_id: str):
        """Update last activity for connection"""
        if session_id in self.connections:
            self.connections[session_id]['last_activity'] = self._get_timestamp()
    
    def get_stats(self) -> Dict[str, Any]:
        """Get connection statistics"""
        return {
            'total_connections': len(self.connections),
            'unique_ips': len(self.connection_counts),
            'max_connections': self.config.max_connections,
            'connections_by_ip': dict(self.connection_counts)
        }
    
    def _get_timestamp(self) -> str:
        """Get current timestamp"""
        from datetime import datetime
        return datetime.now().isoformat()


def get_websocket_config() -> WebSocketConfig:
    """Get WebSocket configuration from environment"""
    environment = os.getenv('ENVIRONMENT', 'development')
    
    config = WebSocketConfig(
        host=os.getenv('WEBSOCKET_HOST', '0.0.0.0'),
        port=int(os.getenv('PORT', os.getenv('WEBSOCKET_PORT', '8000'))),
        path=os.getenv('WEBSOCKET_PATH', '/socket.io/'),
        ssl_enabled=os.getenv('SSL_ENABLED', 'false').lower() == 'true',
        ssl_cert_path=os.getenv('SSL_CERT_PATH'),
        ssl_key_path=os.getenv('SSL_KEY_PATH'),
        environment=environment,
        max_connections=int(os.getenv('MAX_CONNECTIONS', '1000')),
        ping_timeout=int(os.getenv('PING_TIMEOUT', '60')),
        ping_interval=int(os.getenv('PING_INTERVAL', '25')),
        log_level=os.getenv('LOG_LEVEL', 'INFO')
    )
    
    logger.info(f"WebSocket config loaded for {environment} environment")
    logger.info(f"CORS origins: {config.cors_allowed_origins}")
    logger.info(f"SSL enabled: {config.ssl_enabled}")
    
    return config


def validate_production_config(config: WebSocketConfig) -> bool:
    """Validate production configuration"""
    issues = []
    
    if config.environment == "production":
        # Check SSL configuration
        if not config.ssl_enabled:
            issues.append("SSL should be enabled in production")
        
        # Check CORS origins
        if any("localhost" in origin for origin in config.cors_allowed_origins):
            issues.append("Localhost origins should not be allowed in production")
        
        # Check if any wildcard origins are too broad
        if "*" in config.cors_allowed_origins:
            issues.append("Wildcard CORS origins should be avoided in production")
        
        # Check logging configuration
        if config.log_level.upper() == "DEBUG":
            issues.append("Debug logging should be disabled in production")
    
    if issues:
        logger.warning(f"Production configuration issues: {', '.join(issues)}")
        return False
    
    logger.info("Production configuration validation passed")
    return True


# Export configured instances
config = get_websocket_config()
error_handler = ProductionErrorHandler(config)
connection_manager = ConnectionManager(config)

# Validate configuration
if config.environment == "production":
    validate_production_config(config)