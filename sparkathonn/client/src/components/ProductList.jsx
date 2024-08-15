import React, { useState, useEffect } from "react";

const ProductList = () => {
  const [products, setProducts] = useState([]);

  useEffect(() => {
    // Fetch the products from your backend here
    // For demo purposes, we're using static data
    setProducts([
      {
        id: 1,
        name: "Product 1",
        originalPrice: 100,
        adjustedPrice: 90,
        optimizedPrice: 85,
      },
      {
        id: 2,
        name: "Product 2",
        originalPrice: 200,
        adjustedPrice: 180,
        optimizedPrice: 170,
      },
    ]);
  }, []);

  return (
    <div className="bg-white shadow-md rounded-lg p-4">
      <h2 className="text-xl font-semibold mb-4">Products</h2>
      <table className="w-full">
        <thead>
          <tr className="border-b">
            <th className="py-2">Name</th>
            <th className="py-2">Original Price</th>
            <th className="py-2">Adjusted Price</th>
            <th className="py-2">Optimized Price</th>
          </tr>
        </thead>
        <tbody>
          {products.map((product) => (
            <tr key={product.id} className="border-b">
              <td className="py-2">{product.name}</td>
              <td className="py-2">${product.originalPrice.toFixed(2)}</td>
              <td className="py-2">${product.adjustedPrice.toFixed(2)}</td>
              <td className="py-2">${product.optimizedPrice.toFixed(2)}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
};

export default ProductList;
