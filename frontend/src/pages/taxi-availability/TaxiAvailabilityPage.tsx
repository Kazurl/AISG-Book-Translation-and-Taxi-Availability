import { useEffect } from "react";
import { useTaxiStore } from "../../stores/useTaxiStore"
import { LoaderCircle } from "lucide-react";

export default function TaxiAvailabilityPage() {
    const {
        areas,
        totalTaxis,
        isLoading,
        error,
        fetchTaxiAreas
    } = useTaxiStore();

    useEffect(() => {
        fetchTaxiAreas();
    }, [fetchTaxiAreas]);

    return (
    <div className="min-h-screen bg-gray-50 flex flex-col items-center py-12">
        <h1 className="text-3xl font-bold mb-4 text-yellow-700 flex items-center gap-2">
            🚕 Taxi Hotspots
        </h1>
        {isLoading && (
            <div className="text-gray-500 flex items-center gap-2">
                <LoaderCircle className="animate-spin" /> Loading taxi data...
            </div>
        )}
        {error && (
            <div className="text-red-700 bg-red-100 p-2 mt-4 rounded">{error}</div>
        )}
        {(!isLoading && !error) && (
            <div className="w-full max-w-3xl">
                <p className="mb-6 text-gray-700 text-center">
                    Top-10 SG locations with most taxis (Total taxis: <span className="font-semibold">{totalTaxis}</span>)
                </p>

                {areas.length === 0 ? (
                    <div className="text-gray-500 text-center my-6">
                        No taxi areas available right now.
                    </div>
                ) : (
                    <table className="w-full bg-white rounded-lg shadow text-left">
                        <thead>
                            <tr className="bg-yellow-100">
                            <th className="p-3">#</th>
                            <th className="p-3">Address / Landmark</th>
                            <th className="p-3">Taxi Count</th>
                            <th className="p-3">Map</th>
                            </tr>
                        </thead>
                        <tbody>
                            {areas.map((area, i) => (
                                <tr key={`${area.lat}:${area.lon}`} className="border-t">
                                    <td className="p-3">{i + 1}</td>
                                    <td className="p-3">{area.address && area.address !== "NIL" ? area.address : "Unknown location"}</td>
                                    <td className="p-3">{area.count}</td>
                                    <td className="p-3">
                                        <a
                                            href={area.googleMapsLink}
                                            target="_blank"
                                            rel="noopener noreferrer"
                                            className="text-blue-600 underline"
                                        >
                                            View
                                        </a>
                                    </td>
                                </tr>
                            ))}
                        </tbody>
                    </table>
                )}
            </div>
        )}
    </div>
    );
}
