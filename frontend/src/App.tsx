import { Route, Routes } from "react-router-dom";

import HomePage from "./pages/home/HomePage";
import TaxiAvailabilityPage from "./pages/taxi-availability/TaxiAvailabilityPage";
import TranslationPage from "./pages/translation/TranslationPage";
import TranslationProgressPage from "./pages/translation/TranslationProgressPage";

function App() {

  return (
    <>
      <Routes>
        <Route path="/" element={<HomePage />} />
        <Route path="/taxis-availability" element={<TaxiAvailabilityPage />} />
        <Route path="/translate" element={<TranslationPage />} />
        <Route path="/translation_progress" element={<TranslationProgressPage />} />
      </Routes>
    </>
  );
}

export default App;
