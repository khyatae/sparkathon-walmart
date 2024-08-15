import React, { useEffect, useState } from "react";
import product1 from "./assets/product1.jpeg";

const App = () => {
  const [products, setProducts] = useState([]);
  const [showModal, setShowModal] = useState(false);
  const [newProduct, setNewProduct] = useState({
    order_id: "",
    customer_id: "",
    product_id: "",
    category: "",
    product_price: "",
    manufacturing_date: "",
    expiry_date: "",
  });

  useEffect(() => {
    fetch("http://localhost:3000/api/products")
      .then((response) => response.json())
      .then((data) => setProducts(data))
      .catch((error) => console.error("Error fetching products:", error));
  }, []);

  const handleInputChange = (e) => {
    const { name, value } = e.target;
    setNewProduct({ ...newProduct, [name]: value });
  };

  const handleAddProduct = () => {
    console.log("hiii");
    fetch("http://localhost:3000/api/add-product", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(newProduct),
    })
      .then((response) => response.json())
      .then((data) => {
        console.log("dataa", data);
        setProducts([data, ...products]); // Add the new product to the start of the list
        setShowModal(false); // Close the modal
      })
      .catch((error) => console.error("Error adding product:", error));
  };

  return (
    <div>
      <nav className="bg-blue-600 p-4 text-white">
        <div className="container mx-auto flex justify-between items-center">
          <a href="#" className="text-xl font-bold">
            Walmart Clone
          </a>
          <input
            type="text"
            placeholder="Search"
            className="px-4 py-2 rounded w-1/3"
          />
          <div>
            <button
              onClick={() => setShowModal(true)}
              className="bg-green-600 text-white px-4 py-2 rounded mb-4"
            >
              Add New Product
            </button>

            <a href="#" className="mx-2">
              Sign In
            </a>
            <a href="#" className="mx-2">
              Cart
            </a>
          </div>
        </div>
      </nav>

      <section className="container mx-auto mt-8">
        <h2 className="text-2xl font-bold mb-4">Flash Deals</h2>

        <div className="grid grid-cols-1 md:grid-cols-3 lg:grid-cols-5 gap-6">
          {products.map((product) => (
            <div
              key={product.order_id}
              className="border p-4 rounded-lg relative bg-white shadow-sm"
            >
              <img
                src={product1}
                alt={product.category}
                className="w-full h-48 object-cover mb-4 rounded"
              />
              <div className="absolute top-2 right-2 bg-gray-900 text-white text-sm px-2 py-1 rounded">
                ${product.adjusted_price}
              </div>
              <h3 className="text-lg font-bold">{product.category}</h3>
              <p className="text-gray-700">Now ${product.product_price}</p>
              <button className="mt-4 bg-blue-600 text-white px-4 py-2 rounded">
                Add to Cart
              </button>
            </div>
          ))}
        </div>
      </section>

      {showModal && (
        <div className="fixed inset-0 bg-gray-600 bg-opacity-50 flex justify-center items-center">
          <div className="bg-white p-6 rounded-lg shadow-lg w-1/2">
            <h2 className="text-2xl mb-4">Add New Product</h2>
            <div className="grid grid-cols-2 gap-4">
              <input
                type="text"
                name="order_id"
                placeholder="Order ID"
                value={newProduct.order_id}
                onChange={handleInputChange}
                className="border p-2 rounded"
              />
              <input
                type="text"
                name="customer_id"
                placeholder="Customer ID"
                value={newProduct.customer_id}
                onChange={handleInputChange}
                className="border p-2 rounded"
              />
              <input
                type="text"
                name="product_id"
                placeholder="Product ID"
                value={newProduct.product_id}
                onChange={handleInputChange}
                className="border p-2 rounded"
              />
              <input
                type="text"
                name="category"
                placeholder="Category"
                value={newProduct.category}
                onChange={handleInputChange}
                className="border p-2 rounded"
              />
              <input
                type="number"
                name="product_price"
                placeholder="Product Price"
                value={newProduct.product_price}
                onChange={handleInputChange}
                className="border p-2 rounded"
              />
              <input
                type="date"
                name="manufacturing_date"
                placeholder="Manufacturing Date"
                value={newProduct.manufacturing_date}
                onChange={handleInputChange}
                className="border p-2 rounded"
              />
              <input
                type="date"
                name="expiry_date"
                placeholder="Expiry Date"
                value={newProduct.expiry_date}
                onChange={handleInputChange}
                className="border p-2 rounded"
              />
            </div>
            <div className="mt-4 flex justify-end">
              <button
                onClick={() => setShowModal(false)}
                className="bg-red-600 text-white px-4 py-2 rounded mr-2"
              >
                Cancel
              </button>
              <button
                onClick={handleAddProduct}
                className="bg-green-600 text-white px-4 py-2 rounded"
              >
                Add Product
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default App;
