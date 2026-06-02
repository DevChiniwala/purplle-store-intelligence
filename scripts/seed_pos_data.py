import pandas as pd
import asyncio
import asyncpg
import os
import logging
from pathlib import Path

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def seed_pos_data():
    csv_path = Path("data/pos/pos_sales.csv")
    if not csv_path.exists():
        logger.error(f"POS data file not found at {csv_path}")
        return

    logger.info("Reading POS CSV file...")
    df = pd.read_csv(csv_path)

    # Rename columns to match schema
    # Rename columns to match schema
    df = df.rename(columns={
        "dep_name": "category",
        "GMV": "gmv",
        "NMV": "nmv"
    })
    
    # Fill any NaNs
    df = df.fillna({
        "customer_name": "Guest",
        "customer_number": "",
        "brand_name": "",
        "category": "",
        "sub_category": "",
        "salesperson_name": ""
    })

    # Clean date/time
    df['order_date'] = pd.to_datetime(df['order_date'], format='%d-%m-%Y').dt.date
    # Override order_date to today so that it matches our pipeline events generated today
    from datetime import datetime
    df['order_date'] = datetime.now().date()
    
    # Override store_id to ST-5001 to match pipeline events
    df['store_id'] = 'ST-5001'
    
    # Some times are 16:55:36 (%H:%M:%S), some might be AM/PM. Let's just use mixed or %H:%M:%S.
    try:
        df['order_time'] = pd.to_datetime(df['order_time'], format='%H:%M:%S').dt.time
    except ValueError:
        df['order_time'] = pd.to_datetime(df['order_time'], format='mixed').dt.time

    db_url = os.getenv("DATABASE_URL", "postgresql://admin:admin@postgres:5432/store_intelligence")
    # For local execution outside docker:
    if "postgres" in db_url and not os.getenv("IN_DOCKER"):
        db_url = "postgresql://admin:admin@localhost:5432/store_intelligence"

    logger.info("Connecting to database...")
    try:
        conn = await asyncpg.connect(db_url)
        
        # Clear existing
        await conn.execute("TRUNCATE TABLE pos_transactions;")

        # Insert records
        records = df.to_dict('records')
        
        query = """
        INSERT INTO pos_transactions (
            transaction_id, store_id, timestamp, basket_value_inr
        ) VALUES (
            $1, $2, $3, $4
        )
        ON CONFLICT (transaction_id) DO NOTHING
        """
        
        for record in records:
            from datetime import datetime
            # Combine date and time
            dt_str = f"{record['order_date']} {record['order_time']}"
            ts = datetime.strptime(dt_str, "%Y-%m-%d %H:%M:%S")
            
            await conn.execute(
                query,
                str(record['order_id']), record['store_id'], ts, float(record['total_amount'])
            )
            
        logger.info(f"Successfully seeded {len(records)} POS transaction rows.")
        await conn.close()
    except Exception as e:
        logger.error(f"Failed to seed data: {e}")

if __name__ == "__main__":
    asyncio.run(seed_pos_data())
