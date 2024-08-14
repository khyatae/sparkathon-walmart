import React from "react";
import ProductList from "./components/ProductList";
import AddProductForm from "./components/AddProductForm";

function App() {
  return (
    <div className="bg-gray-100 min-h-screen">
      <header className="bg-blue-800 text-white p-4">
        <h1 className="text-2xl font-bold">Walmart Clone</h1>
      </header>
      <main className="p-4">
        <div className="mb-6">
          <AddProductForm />
        </div>
        <ProductList />
      </main>
    </div>
  );
}

export default App;
