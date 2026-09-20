import os
import sys
import logging
import uvicorn

# Configure logging for production
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)],
)

logger = logging.getLogger("start_production")

if __name__ == "__main__":
    os.environ["ENVIRONMENT"] = "production"
    
    from app.config import get_settings
    settings = get_settings()
    
    host = os.getenv("HOST", settings.host)
    port = int(os.getenv("PORT", settings.port))
    
    logger.info(f"============================================================")
    logger.info(f" Starting TradePilot Production Server")
    logger.info(f" Host: {host}:{port} | Environment: {settings.environment}")
    logger.info(f" App Name: {settings.app_name}")
    logger.info(f"============================================================")
    
    uvicorn.run(
        "app.main:app",
        host=host,
        port=port,
        loop="auto",
        http="auto",
        ws="auto",
        timeout_keep_alive=65,
        log_level="info",
        proxy_headers=True,
        forwarded_allow_ips="*",
    )
