import { Link } from "react-router-dom";
import { BookOpenText, Languages } from "lucide-react";
/**
 * Home page component displaying available services.
 *
 * @export
 * @return {*} 
 */
export default function HomePage() {
  
  return (
    <div className="min-h-screen bg-gray-50 flex flex-col items-center justify-center">
      <h1 className="text-4xl font-bold mb-4 flex items-center gap-2">
        <Languages className="w-10 h-10 text-blue-600" />
        Multiservice Platform
      </h1>
      <p className="mb-8 text-lg text-gray-700 text-center max-w-lg">
        Welcome! Choose a service below to get started.
      </p>
      <div className="flex flex-wrap gap-6 justify-center">
        {/* Translation Service */}
        <Link
          to="/translate"
          className="flex flex-col items-center bg-white p-6 rounded-lg shadow-md transition hover:bg-blue-50 w-60"
        >
          <BookOpenText className="w-12 h-12 text-blue-500 mb-2" />
          <span className="text-xl font-semibold mb-1">Translation Service</span>
          <span className="text-gray-600 text-sm text-center">
            Upload or paste your book and get fast, multi-language translations.
          </span>
        </Link>
        {/* Placeholder for other services */}
        <div className="flex flex-col items-center bg-white opacity-50 p-6 rounded-lg shadow-md w-60">
          <span className="w-12 h-12 flex mb-2 items-center justify-center text-gray-300">
            {/* You can add a Lucide icon for your next service */}
            <Languages className="w-12 h-12" />
          </span>
          <span className="text-xl font-semibold mb-1 text-gray-400">Future Service</span>
          <span className="text-gray-400 text-sm text-center">
            More AI tools coming soon!
          </span>
        </div>
      </div>
    </div>
  );
}
