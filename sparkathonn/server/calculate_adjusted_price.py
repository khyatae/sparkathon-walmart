import sys
from datetime import datetime

def calculate_adjusted_price(product_price, expiry_date):
    # Example logic for calculating adjusted price
    expiry_date = datetime.strptime(expiry_date, '%Y-%m-%d')
    days_until_expiry = (expiry_date - datetime.now()).days

    # Adjust the price based on the days until expiry
    if days_until_expiry > 30:
        return float(product_price) * 0.9  # 10% discount if more than 30 days to expiry
    elif 10 <= days_until_expiry <= 30:
        return float(product_price) * 0.8  # 20% discount if between 10 and 30 days to expiry
    else:
        return float(product_price) * 0.5  # 50% discount if less than 10 days to expiry

if __name__ == "__main__":
    product_price = sys.argv[1]
    expiry_date = sys.argv[2]
    adjusted_price = calculate_adjusted_price(product_price, expiry_date)
    print(adjusted_price)
