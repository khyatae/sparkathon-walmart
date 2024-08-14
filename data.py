import pandas as pd
import numpy as np
import mysql.connector
from mysql.connector import Error
from faker import Faker
import dateparser
from sqlalchemy import create_engine
import pandas as pd
import pymysql
from datetime import timedelta,datetime

fake = Faker()

categories = ["Electronics", "Clothing", "Books", "Automotive", "Sports", "Grocery", "Pharmacy", "Beauty", "Home", "Toys"]

seasonal_items = {
    "Grocery": ["Summer", "Winter"],
    "Clothing": ["Winter", "Spring"],
    "Toys": ["Winter"],  # E.g., around Christmas
    "Home": ["Spring", "Fall"],  # E.g., gardening tools in spring
}

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

def load_data():
    connection = connect_db()
    if connection:
        query = "SELECT * FROM sales_data"
        df = pd.read_sql(query, connection)
        connection.close()
        return df
    else:
        print("Failed to connect to the database")
        return None

def get_expiry_date(category, manufacturing_date):
    #print("hii",manufacturing_date)
    if category in ["Electronics", "Clothing", "Books", "Automotive", "Sports"]:
        return 0  
    elif category == "Grocery":
        #print("hii",manufacturing_date+pd.DateOffset(months=fake.random_int(min=6, max=12)))
        return manufacturing_date + pd.DateOffset(months=fake.random_int(min=6, max=12))  
    elif category == "Pharmacy":
        #print("hii",manufacturing_date+pd.DateOffset(months=fake.random_int(min=6, max=12)))
        return manufacturing_date + pd.DateOffset(years=2)  
    elif category == "Beauty":
        #print("hii",manufacturing_date+pd.DateOffset(months=fake.random_int(min=6, max=12)))
        return manufacturing_date + pd.DateOffset(years=3)  
    elif category == "Home":
        #print("hii",manufacturing_date+pd.DateOffset(months=fake.random_int(min=6, max=12)))
        return manufacturing_date + pd.DateOffset(years=5)  
    elif category == "Toys":
        return manufacturing_date + pd.DateOffset(years=4)  
    else:
        return manufacturing_date + pd.DateOffset(years=3)  
    
def create_data():

    num_samples_large = 10000
    start_date = datetime.today() - timedelta(days=int(0.2* 365))
    end_date = datetime.today()
    data_large = {
        "order_id": np.arange(1001, 1001 + num_samples_large),
        "customer_id": [f"C{fake.random_int(min=1, max=1000):03}" for _ in range(num_samples_large)],
        "product_id": np.random.randint(101, 200, num_samples_large),
        "category": np.random.choice(categories, num_samples_large),
        "product_price": np.round(np.random.uniform(5.0, 500.0, num_samples_large), 2),
        "manufacturing_date" : [fake.date_between(start_date=start_date, end_date=end_date) for _ in range(num_samples_large)]
    }

    df_large = pd.DataFrame(data_large)

    df_large['expiry_date'] = df_large.apply(lambda row: get_expiry_date(row['category'], row['manufacturing_date']), axis=1)

    print(df_large[['manufacturing_date', 'expiry_date']].head(10))

    #print(df_large['expiry_date'])
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
            expiry_date DATE
        );
        """
        cursor.execute(create_table_query)
        connection.commit()

        for index, row in df_large.iterrows():
            #print("hii",row["expiry_date"])
            insert_query = """
            INSERT INTO sales_data (order_id, customer_id, product_id, category, product_price, manufacturing_date, expiry_date)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
            ON DUPLICATE KEY UPDATE
            customer_id=VALUES(customer_id),
            product_id=VALUES(product_id),
            category=VALUES(category),
            product_price=VALUES(product_price),
            manufacturing_date=VALUES(manufacturing_date),
            expiry_date=VALUES(expiry_date)
            """
            cursor.execute(insert_query, tuple(row))
            connection.commit()
        
        #print(df_large["expiry_date"])
        print(df_large[['manufacturing_date', 'expiry_date']].head(10))

        print(f"Inserted or updated {len(df_large)} records in the database")

        cursor.close()
        connection.close()
        df = load_data()
        print(df.head())
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
            INSERT INTO sales_data (order_id, customer_id, product_id, category, product_price, manufacturing_date, expiry_date)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
            ON DUPLICATE KEY UPDATE
            customer_id=VALUES(customer_id),
            product_id=VALUES(product_id),
            category=VALUES(category),
            product_price=VALUES(product_price),
            manufacturing_date=VALUES(manufacturing_date),
            expiry_date=VALUES(expiry_date)
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


# Function to determine the current season
def get_current_season(date):
    month = date.month
    if month in [12, 1, 2]:
        return "Winter"
    elif month in [3, 4, 5]:
        return "Spring"
    elif month in [6, 7, 8]:
        return "Summer"
    else:
        return "Fall"
    

def adjust_prices(row):
    today = pd.Timestamp.today()
    expiry_date = pd.to_datetime(row['expiry_date'], format='%Y-%m-%d %H:%M:%S', errors='coerce')
    # Calculate days to expiry
    days_to_expiry = (expiry_date - today).days if pd.notnull(expiry_date) else 0

    # Print for debugging
    #print("kuuu", days_to_expiry, row['expiry_date'], today, expiry_date)

    season = get_current_season(today)
    adjusted_price = row['product_price']
    discount = 0
    
    # Adjust based on expiry date
    if days_to_expiry is not None:
        if days_to_expiry < 30:
            adjusted_price *= 0.5  # 50% discount if less than 30 days to expiry
            discount = 50
        elif days_to_expiry < 90:
            adjusted_price *= 0.75  # 25% discount if less than 90 days to expiry
            discount = 25
    
    # Adjust based on seasonality
    if row['category'] in seasonal_items:
        if season in seasonal_items[row['category']]:
            adjusted_price *= 1.2  # Increase price by 20% in peak season
        else:
            adjusted_price *= 0.9  # Reduce price by 10% in off-season
    
    return round(adjusted_price, 2), discount

def dynamic_pricing():
    df = load_data()
    print(df.head())
    #expiry_date = pd.to_datetime(row['expiry_date'], format='%Y-%m-%d', errors='coerce')
    df['expiry_date'] = pd.to_datetime(df['expiry_date'],format='%Y-%m-%d', errors='coerce')
    df['manufacturing_date'] = pd.to_datetime(df['manufacturing_date'],format='%Y-%m-%d', errors='coerce')
    
    # Apply the adjustment function
    print("huucle")
    df[['adjusted_price', 'discount']] = df.apply(lambda row: pd.Series(adjust_prices(row)), axis=1)
    print("yess")
    
    # Determine offer
    df['offer'] = df.apply(lambda row: f"{row['discount']}% off" if row['discount'] > 0 else "No offer", axis=1)
    
    connection = connect_db()
    if connection:
        cursor = connection.cursor()
        
        cursor.execute("SHOW COLUMNS FROM sales_data LIKE 'discount'")
        result = cursor.fetchone()
        if result is None:
            cursor.execute("ALTER TABLE sales_data ADD COLUMN discount varchar(50)")
            print("Added 'discount' column to 'sales_data' table.")

        cursor.execute("SHOW COLUMNS FROM sales_data LIKE 'adjusted_price'")
        result = cursor.fetchone()
        if result is None:
            cursor.execute("ALTER TABLE sales_data ADD COLUMN adjusted_price DECIMAL(10, 2)")
            print("Added 'discount' column to 'adjusted_price' table.")


        cursor.execute("SHOW COLUMNS FROM sales_data LIKE 'offer'")
        result = cursor.fetchone()
        if result is None:
            cursor.execute("ALTER TABLE sales_data ADD COLUMN offer varchar(50)")
            print("Added 'offer' column to 'sales_data' table.")

        cursor.execute("SHOW COLUMNS FROM sales_data LIKE 'offer'")
        offer_column = cursor.fetchone()
        if offer_column is not None:
            column_type = offer_column[1].decode('utf-8') if isinstance(offer_column[1], bytes) else offer_column[1]
            if 'varchar' in column_type.lower():
                length = int(column_type.split('(')[1].strip(')'))
                if length < 50:  # Adjust this value if needed
                    cursor.execute("ALTER TABLE sales_data MODIFY COLUMN offer VARCHAR(100)")  # Increase length
                    print("Modified 'offer' column length to VARCHAR(100).")


        # Update prices and discounts in the database
        for _, row in df.iterrows():
            update_query = """
            UPDATE sales_data
            SET adjusted_price = %s, discount = %s, offer = %s
            WHERE order_id = %s
            """
            cursor.execute(update_query, (row['adjusted_price'], row['discount'], row['offer'], row['order_id']))
        
        connection.commit()
        cursor.close()
        connection.close()
        print("Database updated with adjusted prices and discounts.")
    else:
        print("Failed to connect to the database")