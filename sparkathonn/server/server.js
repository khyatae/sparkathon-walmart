const express = require("express");
const mysql = require("mysql2");
const cors = require("cors");
const { spawn } = require("child_process"); // Import spawn for running Python scripts

const app = express();
app.use(cors());
app.use(express.json());

const connection = mysql.createConnection({
  host: "localhost",
  user: "root",
  password: "khya",
  database: "walmart_data",
});

// Endpoint to get all products
app.get("/api/products", (req, res) => {
  console.log("okayy");
  const query = "SELECT * FROM sales_data LIMIT 20";
  connection.query(query, (error, results) => {
    if (error) throw error;
    res.json(results);
  });
});

// Endpoint to add a new product
app.post("/api/add-product", (req, res) => {
  const {
    order_id,
    customer_id,
    product_id,
    category,
    product_price,
    manufacturing_date,
    expiry_date,
  } = req.body;

  // Run Python script to calculate adjusted price
  const python = spawn("python", [
    "calculate_adjusted_price.py",
    product_price,
    expiry_date,
  ]);

  let adjusted_price = "";

  python.stdout.on("data", (data) => {
    adjusted_price += data.toString().trim();
    console.log(adjusted_price);
  });

  python.stderr.on("data", (data) => {
    console.error("Error calculating adjusted price:", data.toString());
    if (!res.headersSent) {
      res.status(500).send("Error calculating adjusted price");
    }
  });

  python.on("close", (code) => {
    if (code !== 0) {
      console.error(`Python script exited with code ${code}`);
      if (!res.headersSent) {
        return res.status(500).send("Error calculating adjusted price");
      }
    }

    // Insert product into the database if the adjusted price was calculated successfully
    const query = `
      INSERT INTO sales_data (order_id, customer_id, product_id, category, product_price, manufacturing_date, expiry_date, adjusted_price)
      VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    `;
    connection.query(
      query,
      [
        order_id,
        customer_id,
        product_id,
        category,
        product_price,
        manufacturing_date,
        expiry_date,
        parseFloat(adjusted_price),
      ],
      (error, results) => {
        if (error) {
          console.error("Database insertion error:", error);
          if (!res.headersSent) {
            return res.status(500).send("Database error");
          }
        } else {
          console.log("huu", adjusted_price);
          res.json({
            order_id,
            customer_id,
            product_id,
            category,
            product_price,
            manufacturing_date,
            expiry_date,
            adjusted_price: parseFloat(adjusted_price),
          });
        }
      }
    );
  });
});

app.listen(3000, () => {
  console.log("Server is running on port 3000");
});
