#!/usr/bin/env python3
"""
Gateway Service - Kong-based API Gateway
========================================

This service provides enterprise-grade API gateway functionality using Kong.

Features:
- JWT Authentication
- Rate Limiting
- CORS Support
- Request Transformation
- Service Discovery
- Load Balancing
- SSL/TLS Termination

Kong Proxy: http://localhost:8000
Kong Admin API: http://localhost:8001
Kong Admin GUI: http://localhost:8002
"""

import os
import sys
import time
import logging
import requests
from datetime import datetime

# Configure logging (console only)
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

class GatewayService:
    """Kong-based Gateway Service"""

    def __init__(self):
        self.kong_admin_url = os.getenv('KONG_ADMIN_URL', 'http://localhost:8001')
        self.kong_proxy_url = os.getenv('KONG_PROXY_URL', 'http://localhost:8000')
        self.kong_gui_url = os.getenv('KONG_GUI_URL', 'http://localhost:8002')

    def check_kong_status(self):
        """Check Kong gateway status"""
        try:
            response = requests.get(f"{self.kong_admin_url}/status", timeout=10)
            if response.status_code == 200:
                status = response.json()
                logger.info(f"Kong status: {status}")
                return True
            else:
                logger.error(f"Kong status check failed: {response.status_code}")
                return False
        except Exception as e:
            logger.error(f"Error checking Kong status: {e}")
            return False

    def get_services(self):
        """Get registered services from Kong"""
        try:
            response = requests.get(f"{self.kong_admin_url}/services", timeout=10)
            if response.status_code == 200:
                services = response.json()
                logger.info(f"Registered services: {len(services.get('data', []))}")
                return services
            else:
                logger.error(f"Failed to get services: {response.status_code}")
                return None
        except Exception as e:
            logger.error(f"Error getting services: {e}")
            return None

    def get_routes(self):
        """Get registered routes from Kong"""
        try:
            response = requests.get(f"{self.kong_admin_url}/routes", timeout=10)
            if response.status_code == 200:
                routes = response.json()
                logger.info(f"Registered routes: {len(routes.get('data', []))}")
                return routes
            else:
                logger.error(f"Failed to get routes: {response.status_code}")
                return None
        except Exception as e:
            logger.error(f"Error getting routes: {e}")
            return None

    def monitor_services(self):
        """Monitor gateway services and routes"""
        logger.info("Starting Gateway Service monitoring...")

        while True:
            try:
                # Check Kong status
                if self.check_kong_status():
                    logger.info("Kong gateway is healthy")

                    # Get services and routes
                    services = self.get_services()
                    routes = self.get_routes()

                    if services and routes:
                        logger.info("Gateway configuration is valid")
                    else:
                        logger.warning("Issues detected with gateway configuration")

                else:
                    logger.error("Kong gateway is not responding")

                # Wait before next check
                time.sleep(30)

            except KeyboardInterrupt:
                logger.info("Monitoring stopped by user")
                break
            except Exception as e:
                logger.error(f"Error in monitoring loop: {e}")
                time.sleep(30)

def main():
    """Main entry point"""
    logger.info("Starting Gateway Service (Kong-based)")

    # Initialize service
    gateway = GatewayService()

    # Log service information
    logger.info("Kong URLs:")
    logger.info(f"  Proxy: {gateway.kong_proxy_url}")
    logger.info(f"  Admin API: {gateway.kong_admin_url}")
    logger.info(f"  Admin GUI: {gateway.kong_gui_url}")

    # Start monitoring
    try:
        gateway.monitor_services()
    except Exception as e:
        logger.error(f"Gateway service error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
