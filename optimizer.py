import mysql.connector
import numpy as np
import pandas as pd
from random import randint, uniform, random
from tensorflow.keras.models import load_model
import joblib 

# Database credentials
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
    except mysql.connector.Error as e:
        print(f"Error: {e}")
        return None


class GeneticAlgorithm:
    def __init__(self, population_size, mutation_rate, crossover_rate, generations, bounds):
        self.population_size = population_size
        self.mutation_rate = mutation_rate
        self.crossover_rate = crossover_rate
        self.generations = generations
        self.bounds = bounds

    def initialize_population(self):
        return [round(uniform(self.bounds[0], self.bounds[1]), 2) for _ in range(self.population_size)]

    def fitness_function(self, ind, discount, model):
        try:
            # Ensure discount is a float or int
            discount = float(discount)
        except ValueError:
            raise TypeError("Discount must be a numeric value.")

        # Assuming ind is the product price
        product_price = ind

        # Calculate adjusted price
        adjusted_price = product_price * (1 - discount / 100)

        # Create a feature vector with 12 features
        # Here we're just filling the array with the adjusted_price for demonstration.
        # You should replace this with the actual 12 features needed by your model.
        feature_vector = np.array([adjusted_price] * 12).reshape(1, -1)

        # Predict using the model
        fitness = model.predict(feature_vector)
        
        return fitness

    def select_parents(self, population, fitness_scores):
        idx1, idx2 = randint(0, len(population) - 1), randint(0, len(population) - 1)
        return population[idx1] if fitness_scores[idx1] > fitness_scores[idx2] else population[idx2]

    def crossover(self, parent1, parent2):
        return (parent1 + parent2) / 2 if random() < self.crossover_rate else parent1

    def mutate(self, individual):
        return round(uniform(self.bounds[0], self.bounds[1]), 2) if random() < self.mutation_rate else individual

    def optimize(self, discount, model):
        population = self.initialize_population()

        for _ in range(self.generations):
            fitness_scores = [self.fitness_function(ind, discount, model) for ind in population]
            new_population = []
            for _ in range(self.population_size):
                parent1 = self.select_parents(population, fitness_scores)
                parent2 = self.select_parents(population, fitness_scores)
                child = self.crossover(parent1, parent2)
                child = self.mutate(child)
                new_population.append(child)
            population = new_population

        best_individual = max(population, key=lambda ind: self.fitness_function(ind, discount, model))
        best_fitness = self.fitness_function(best_individual, discount, model)
        return best_individual, best_fitness

def fetch_data(query, connection, limit=20):
    cursor = connection.cursor(dictionary=True)
    query_with_limit = f"{query} LIMIT {limit}"
    cursor.execute(query_with_limit)
    result = cursor.fetchall()
    cursor.close()
    return pd.DataFrame(result)

def update_optimized_price(df, connection):
    cursor = connection.cursor()

    cursor.execute("SHOW COLUMNS FROM sales_data LIKE 'optimized_price'")
    result = cursor.fetchone()
    if result is None:
        cursor.execute("ALTER TABLE sales_data ADD COLUMN optimized_price varchar(50)")
        print("Added 'optimized_price' column to 'sales_data' table.")

    for _, row in df.iterrows():
        sql = "UPDATE sales_data SET optimized_price = %s WHERE order_id = %s"
        cursor.execute(sql, (row['optimized_price'], row['order_id']))
    connection.commit()
    cursor.close()

def optimize_prices():
    # Connect to the database
    connection = connect_db()

    # Fetch a limited number of products from the database
    data = fetch_data("SELECT * FROM sales_data", connection, limit=20)

    # Load the pre-trained model
    model = joblib.load("final_model.pkl")

    # Prepare a DataFrame to hold the results
    columns = ["order_id", "product_id", "original_price",
               "optimized_price", "predicted_adjusted_price"]
    optimization_results = pd.DataFrame(columns=columns)

    # Perform the optimization for each row in the data
    for index, row in data.iterrows():
        print(f"Optimizing for order_id {row['order_id']}")

        product_price = row['product_price']
        discount = row['discount']

        # Define the bounds for the price optimization (e.g., 80% to 120% of the original price)
        bounds = (float(product_price) * 0.8, float(product_price) * 1.2)

        # Initialize and run the Genetic Algorithm
        ga = GeneticAlgorithm(population_size=50, mutation_rate=0.1,
                              crossover_rate=0.7, generations=1000, bounds=bounds)
        best_position, best_fitness = ga.optimize(discount, model)

        # Convert best_fitness from a NumPy array to a scalar
        best_fitness_value = best_fitness.item() if isinstance(best_fitness, np.ndarray) else best_fitness

        # Store the results
        optimization_results.loc[index, "order_id"] = row["order_id"]
        optimization_results.loc[index, "product_id"] = row["product_id"]
        optimization_results.loc[index, "original_price"] = product_price
        optimization_results.loc[index, "optimized_price"] = float(round(best_position, 2))
        optimization_results.loc[index, "predicted_adjusted_price"] = round(best_fitness_value, 2)

    # Update the optimized prices in the database
    update_optimized_price(optimization_results, connection)

    # Close the database connection
    connection.close()
