import pandas as pd
import asyncio
import asyncpg
import os
import logging
from pathlib import Path

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def seed_pos_data():
    csv_path = Path("data/pos/Brigade_Bangalore_10_April_26 (1)bc6219c.csv")
    if not csv_path.exists():
        logger.error(f"POS data file not found at {csv_path}")
        return

    logger.info("Reading POS CSV file...")
    df = pd.read_csv(csv_path)

    # Rename columns to match schema
    df = df.rename(columns={
        "Order ID": "order_id",
        "Invoice Number": "invoice_number",
        "Order Date": "order_date",
        "Order Time": "order_time",
        "Store ID": "store_id",
        "Store Name": "store_name",
        "Customer Name": "customer_name",
        "Customer Number": "customer_number",
        "Product Name": "product_name",
        "Brand Name": "brand_name",
        "Category": "category",
        "Sub Category": "sub_category",
        "Salesperson Name": "salesperson_name",
        "Qty": "qty",
        "GMV": "gmv",
        "NMV": "nmv",
        "Total Amount": "total_amount"
    })

    # Clean date/time
    df['order_date'] = pd.to_datetime(df['order_date'], format='%d-%m-%Y').dt.date
    df['order_time'] = pd.to_datetime(df['order_time'], format='%I:%M %p').dt.time

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
            order_id, invoice_number, order_date, order_time, store_id, 
            store_name, customer_name, customer_number, product_name, 
            brand_name, category, sub_category, salesperson_name, 
            qty, gmv, nmv, total_amount
        ) VALUES (
            $1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, $13, $14, $15, $16, $17
        )
        """
        
        for record in records:
            await conn.execute(
                query,
                record['order_id'], record['invoice_number'], record['order_date'], record['order_time'],
                record['store_id'], record['store_name'], record['customer_name'], str(record['customer_number']),
                record['product_name'], record['brand_name'], record['category'], record['sub_category'],
                record['salesperson_name'], int(record['qty']), float(record['gmv']), float(record['nmv']), float(record['total_amount'])
            )
            
        logger.info(f"Successfully seeded {len(records)} POS transaction rows.")
        await conn.close()
    except Exception as e:
        logger.error(f"Failed to seed data: {e}")

if __name__ == "__main__":
    asyncio.run(seed_pos_data())
