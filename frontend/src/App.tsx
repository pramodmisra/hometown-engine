import { BrowserRouter, Route, Routes } from "react-router-dom";
import Home from "./pages/Home";
import Region from "./pages/Region";
import Layout from "./components/Layout";

export default function App() {
  return (
    <BrowserRouter>
      <Layout>
        <Routes>
          <Route path="/" element={<Home />} />
          <Route path="/region/:state_code" element={<Region />} />
        </Routes>
      </Layout>
    </BrowserRouter>
  );
}
