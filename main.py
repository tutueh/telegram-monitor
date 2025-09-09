#!/usr/bin/env python3

import os
import sys
import asyncio
import logging
from monitor import TelegramMonitor

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def load_config():
    config = {
        'api_id': os.getenv('API_ID'),
        'api_hash': os.getenv('API_HASH'),
        'phone': os.getenv('PHONE'),
        'db_path': os.getenv('DB_FILE', '/app/data/telegram_monitor.db')
    }

    missing = [k for k, v in config.items() if not v]
    if missing:
        logger.error(f"Missing required environment variables: {', '.join(missing)}")
        return None

    return config

def show_alerts(monitor):
    alerts = monitor.db.get_recent_alerts()
    if not alerts:
        print("No alerts found")
        return

    print("\nRecent alerts:")
    print("-" * 60)
    for timestamp, group, alert_type, brand, content in alerts:
        print(f"{timestamp} | {group}")
        print(f"Type: {alert_type} | Brand: {brand}")
        print(f"Content: {content[:100]}")
        print("-" * 60)

def show_stats(monitor):
    stats = monitor.db.get_stats()
    print(f"\nStatistics:")
    print(f"Messages: {stats['messages']}")
    print(f"Alerts: {stats['alerts']}")

    if stats['types']:
        print("\nAlert types:")
        for alert_type, count in stats['types'].items():
            print(f"  {alert_type}: {count}")

    if stats['brands']:
        print("\nTop brands:")
        for brand, count in stats['brands'].items():
            print(f"  {brand}: {count}")

def main():
    config = load_config()
    if not config:
        sys.exit(1)

    os.makedirs(os.path.dirname(config['db_path']), exist_ok=True)

    monitor = TelegramMonitor(**config)

    while True:
        print("\nTelegram Fraud Monitor")
        print("1. Start monitoring")
        print("2. View alerts")
        print("3. Show statistics")
        print("4. Exit")

        try:
            choice = input("\nOption: ").strip()
        except (KeyboardInterrupt, EOFError):
            break

        if choice == '1':
            try:
                asyncio.run(monitor.start_monitoring())
            except KeyboardInterrupt:
                logger.info("Monitoring stopped")
        elif choice == '2':
            show_alerts(monitor)
        elif choice == '3':
            show_stats(monitor)
        elif choice == '4':
            break
        else:
            print("Invalid option")

    print("Goodbye")

if __name__ == '__main__':
    main()
