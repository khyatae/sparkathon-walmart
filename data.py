import pandas as pd
import numpy as np
import mysql.connector
from mysql.connector import Error
from faker import Faker
import dateparser
from sqlalchemy import create_engine

fake = Faker()

categories = ["Electronics", "Clothing", "Books", "Automotive", "Sports", "Grocery", "Pharmacy", "Beauty", "Home", "Toys"]

def connect_db():
    try:
        connection = mysql.connector.connect(
            host='localhost',
            database='walmart_data',
            user='root',
            password='khya'
        )
        if connection.is_connected():
            print("Successfully connected to the database")
            return connection
    except Error as e:
        print(f"Error: {e}")
        return None

def get_expiry_date(category, manufacturing_date):
    if category in ["Electronics", "Clothing", "Books", "Automotive", "Sports"]:
        return None  
    elif category == "Grocery":
        return manufacturing_date + pd.DateOffset(months=fake.random_int(min=6, max=12))  
    elif category == "Pharmacy":
        return manufacturing_date + pd.DateOffset(years=2)  
    elif category == "Beauty":
        return manufacturing_date + pd.DateOffset(years=3)  
    elif category == "Home":
        return manufacturing_date + pd.DateOffset(years=5)  
    elif category == "Toys":
        return manufacturing_date + pd.DateOffset(years=4)  
    else:
        return manufacturing_date + pd.DateOffset(years=3)  
    
def create_data():

    num_samples_large = 10000

    data_large = {
        "order_id": np.arange(1001, 1001 + num_samples_large),
        "customer_id": [f"C{fake.random_int(min=1, max=1000):03}" for _ in range(num_samples_large)],
        "product_id": np.random.randint(101, 200, num_samples_large),
        "category": np.random.choice(categories, num_samples_large),
        "product_price": np.round(np.random.uniform(5.0, 500.0, num_samples_large), 2),
        "manufacturing_date": [fake.date_between(start_date="-3y", end_date="today") for _ in range(num_samples_large)],
        "order_timestamp": [fake.date_time_between(start_date="-1y", end_date="now") for _ in range(num_samples_large)],
    }

    df_large = pd.DataFrame(data_large)

    df_large['expiry_date'] = df_large.apply(lambda row: get_expiry_date(row['category'], row['manufacturing_date']), axis=1)

    connection = connect_db()
    if connection:
        cursor = connection.cursor()

        cursor.execute("SET SQL_MODE='ALLOW_INVALID_DATES';")
        
        create_table_query = """
        CREATE TABLE IF NOT EXISTS sales_data (
            order_id INT PRIMARY KEY,
            customer_id VARCHAR(255),
            product_id INT,
            category VARCHAR(255),
            product_price DECIMAL(10, 2),
            manufacturing_date DATE,
            expiry_date DATE,
            order_timestamp TIMESTAMP
        );
        """
        cursor.execute(create_table_query)
        connection.commit()

        for index, row in df_large.iterrows():
            insert_query = """
            INSERT INTO sales_data (order_id, customer_id, product_id, category, product_price, manufacturing_date, expiry_date, order_timestamp)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
            ON DUPLICATE KEY UPDATE
            customer_id=VALUES(customer_id),
            product_id=VALUES(product_id),
            category=VALUES(category),
            product_price=VALUES(product_price),
            manufacturing_date=VALUES(manufacturing_date),
            expiry_date=VALUES(expiry_date),
            order_timestamp=VALUES(order_timestamp)
            """
            cursor.execute(insert_query, tuple(row))
            connection.commit()

        print(f"Inserted or updated {len(df_large)} records in the database")

        cursor.close()
        connection.close()
    else:
        print("Failed to connect to the database")

def preprocess_data():
    connection = connect_db()
    if connection:
        # Use raw SQL to fetch data instead of pandas.read_sql to avoid the warning
        cursor = connection.cursor(dictionary=True)
        cursor.execute("SELECT * FROM sales_data")
        rows = cursor.fetchall()

        # Convert fetched rows to DataFrame
        data = pd.DataFrame(rows)

        # Preprocess the data
        data['product_price'] = data['product_price'].astype(float).round(2)
        
        # Find and remove the data with zero product_price
        zero_price_data = data[data.product_price == 0.0]
        data.drop(zero_price_data.index, axis=0, inplace=True)
        
        # Reset the index
        data.index = range(len(data))
        
        # Handle any remaining NaN or infinite values
        with pd.option_context('mode.use_inf_as_na', True):
            data = data.dropna(axis=0)
        
        data.index = range(len(data))

        # Insert the processed data back into the database using SQL
        insert_query = """
            INSERT INTO sales_data (order_id, customer_id, product_id, category, product_price, manufacturing_date, expiry_date, order_timestamp)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
            ON DUPLICATE KEY UPDATE
            customer_id=VALUES(customer_id),
            product_id=VALUES(product_id),
            category=VALUES(category),
            product_price=VALUES(product_price),
            manufacturing_date=VALUES(manufacturing_date),
            expiry_date=VALUES(expiry_date),
            order_timestamp=VALUES(order_timestamp)
            """

        # Prepare data for insertion
        data_tuples = list(data.itertuples(index=False, name=None))
        
        # Execute the insert query with the data
        cursor.executemany(insert_query, data_tuples)
        connection.commit()

        print(f"Inserted or updated {len(data)} records in the database.")

        # Close the cursor and connection
        cursor.close()
        connection.close()
    else:
        print("Failed to connect to the database")

def products_with_sales(num_of_sales=1000):
    connection = mysql.connector.connect(
        host='localhost',
        database='walmart_data',
        user='root',
        password='khya'
    )
    
    cursor = connection.cursor()

    # Find products with sales more than num_of_sales
    high_sales_query = f"""
    CREATE TEMPORARY TABLE high_sales_products AS
    SELECT product_id, COUNT(*) AS total_sales
    FROM sales_data
    GROUP BY product_id
    HAVING total_sales >= {num_of_sales};
    """
    cursor.execute(high_sales_query)

    # Join high sales products with original sales_data
    processed_data_query = f"""
    CREATE TABLE IF NOT EXISTS products_{num_of_sales}_sales AS
    SELECT sd.*,
           CEIL(DATEDIFF(sd.order_timestamp, (
               SELECT MIN(order_timestamp) FROM sales_data
           )) / 7) AS week
    FROM sales_data sd
    JOIN high_sales_products hp
    ON sd.product_id = hp.product_id
    ORDER BY sd.order_timestamp;
    """
    cursor.execute(processed_data_query)

    # Drop the temporary table
    cursor.execute("DROP TEMPORARY TABLE IF EXISTS high_sales_products;")
    
    print("donee")
    connection.commit()
    cursor.close()
    connection.close()

