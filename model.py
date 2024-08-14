import pandas as pd
import numpy as np
import mysql.connector
from mysql.connector import Error
from sklearn.model_selection import train_test_split
from sklearn.neural_network import MLPRegressor
from sklearn.metrics import mean_squared_error
from sklearn.preprocessing import StandardScaler
import joblib 

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

def preprocess_data_nn(df):
    df['expiry_date'] = pd.to_datetime(df['expiry_date'], format='%Y-%m-%d', errors='coerce')
    df['manufacturing_date'] = pd.to_datetime(df['manufacturing_date'], format='%Y-%m-%d', errors='coerce')

    df['days_to_expiry'] = (df['expiry_date'] - pd.Timestamp.today()).dt.days
    df['days_to_expiry'] = df['days_to_expiry'].fillna(0)  # Fill NaN with 0 for products without expiry

    # One-hot encode categories
    df = pd.get_dummies(df, columns=['category'])

    # Ensure that only numeric columns are selected as features
    features = df.drop(columns=['order_id', 'customer_id', 'product_id', 'expiry_date', 'manufacturing_date', 'adjusted_price', 'discount', 'offer'])
    
    target = df['adjusted_price']

    return features, target


def train_neural_network(features, target):
    # Split the data into training and testing sets
    X_train, X_test, y_train, y_test = train_test_split(features, target, test_size=0.2, random_state=42)

    # Scale the features
    scaler = StandardScaler()
    X_train_scaled = scaler.fit_transform(X_train)
    X_test_scaled = scaler.transform(X_test)

    # Define and train the Neural Network
    nn = MLPRegressor(hidden_layer_sizes=(64, 64), max_iter=500, random_state=42)
    nn.fit(X_train_scaled, y_train)

    # Predict and evaluate
    y_pred_train = nn.predict(X_train_scaled)
    y_pred_test = nn.predict(X_test_scaled)

    train_error = mean_squared_error(y_train, y_pred_train)
    test_error = mean_squared_error(y_test, y_pred_test)

    print(f"Train MSE: {train_error}")
    print(f"Test MSE: {test_error}")

    joblib.dump(nn, 'final_model.pkl')
    joblib.dump(scaler, 'scaler.pkl')

    return nn, scaler

def neural_network():
    df = load_data()
    if df is not None:
        features, target = preprocess_data_nn(df)
        nn, scaler = train_neural_network(features, target)

        # Scale the entire feature set
        features_scaled = scaler.transform(features)

        # Predict adjusted prices
        df['predicted_adjusted_price'] = nn.predict(features_scaled)


        # Update the database with the new prices
        connection = connect_db()
        if connection:
            cursor = connection.cursor()

            cursor.execute("SHOW COLUMNS FROM sales_data LIKE 'predicted_adjusted_price'")
            result = cursor.fetchone()
            if result is None:
                cursor.execute("ALTER TABLE sales_data ADD COLUMN predicted_adjusted_price varchar(50)")
                print("Added 'predicted_adjusted_price' column to 'sales_data' table.")


            for _, row in df.iterrows():
                update_query = """
                UPDATE sales_data
                SET predicted_adjusted_price = %s
                WHERE order_id = %s
                """
                cursor.execute(update_query, (row['predicted_adjusted_price'], row['order_id']))

            connection.commit()
            cursor.close()
            connection.close()

            print("Database updated with Neural Network predicted prices.")
        else:
            print("Failed to connect to the database")

# Call the function to run the neural network and update prices
