import axios from "axios";
import dotenv from "dotenv";
import NodeCache from "node-cache";

dotenv.config();

// Initialize cache (TTL 30s)
const cache = new NodeCache({ stdTTL: 30 });
const TAXI_API_URL = "https://api.data.gov.sg/v1/transport/taxi-availability";
const ONEMAP_API_ACCESS_TOKEN = process.env.ONE_API_ACCESS_TOKEN;
const ONEMAP_TOKEN_CACHE_KEY = "onemap_token";
const ONEMAP_EMAIL = process.env.ONE_API_EMAIL;
const ONEMAP_PASSWORD = process.env.ONE_API_PASSWORD;
const GRID_SIZE = 0.005;  // ~500m grid in SG


/**
 * Get OneMap API token, with caching
 * https://docs.onemap.sg/#authentication
 * Returns cached token if not expired (with 1min buffer)
*/
async function getOneMapToken() {
    const cachedToken = cache.get(ONEMAP_TOKEN_CACHE_KEY);
    if (cachedToken && cachedToken.expiry > Date.now() + 60000) {  // buffer for 1min before expiry
        return cachedToken;
    }

    const { data } = await axios.post(
        "https://developers.onemap.sg/privateapi/auth/post/getToken", 
        { email: ONEMAP_EMAIL, password: ONEMAP_PASSWORD }
    );

    cache.set(ONEMAP_TOKEN_CACHE_KEY,{
        token: data.access_token, expiry: Number(data.expiry_timestamp) * 1000
    });

    return data.access_token;
}


/**
 * Convert lat, lng to grid cell (for caching)
 *
 * @param {*} lat
 * @param {*} lng
 * @return {*} 
 */
function latLOngToGridCell(lat, lng) {
    return [
        Math.round(lat / GRID_SIZE) * GRID_SIZE,
        Math.round(lng / GRID_SIZE) * GRID_SIZE
    ];
}


/**
 * Use Public OneMap API to reverse geocode lat, lon to address
 * https://docs.onemap.sg/#reverse-geocode
 *
 * @param {*} lat - latitude
 * @param {*} lon - longitude
 * @return {String} address or "Unknown location" if not found
*/
async function reverseGeocode(lat, lon) {
    try {
        const token = ONEMAP_API_ACCESS_TOKEN;
        // const token = await getOneMapToken();
        // if (!token) token = ONEMAP_API_ACCESS_TOKEN;
    
        const url = `https://www.onemap.gov.sg/api/public/revgeocode?location=${lat},${lon}&buffer=40&addressType=All&otherFeatures=N`;
        const { data } = await axios.get(url, {
            headers: { "Authorization": token }   
        });

        if (data && Array.isArray(data.GeocodeInfo) && data.GeocodeInfo.length > 0) {
            const geocode = data.GeocodeInfo[0];
            return (
                geocode.BUILDINGNAME ||
                [geocode.BLOCK, geocode.ROAD, geocode.POSTALCODE].filter(Boolean).join(" ") ||
                "Unknown location"
            );
        }
    } catch (error) {
        console.log("An error occured in reverseGeocode:", error.message);
    }
    return "Unknown location";
}


/**
 * Get top 10 taxi availability areas in Singapore
 * - Fetch taxi locations from data.gov.sg API
 * - Cluster by grid cell (to group nearby taxis)
 * - Sort by cluster size and take top 10
 * - Reverse geocode to get address and Google Maps link
 *
 * Caches result for 30s to avoid excessive API calls
 *
 * @return {Object} { total_taxis: number, areas: [ { lat, lon, count, address, googleMapsLink } ] }
*/
export async function getTopTaxiAreas() {
    const cached = cache.get("taxiAvalability");
    if (cached) {
        return cached;
    }

    // Fetch locations
    const { data } = await axios.get(TAXI_API_URL);
    const coords = data.features[0].geometry.coordinates.map(([lon, lat]) => ({
        lat, lon,
    }));

    // Cluster by grid cell
    const gridMap = {};
    for (const { lat, lon } of coords) {
        const cell = latLOngToGridCell(lat, lon).join(",");
        if (!gridMap[cell]) gridMap[cell] = [];
        gridMap[cell].push({ lat, lon });
    }

    // compute top 10 clusters via size
    const topClusters = Object.entries(gridMap)
        .map(([cell, taxis]) => {
            const lats = taxis.map(t => t.lat), lons = taxis.map(t => t.lon);

            // Area center is avg of lat/lon of taxis in cluster
            const lat = lats.reduce((a, b) => a + b, 0) / taxis.length;
            const lon = lons.reduce((a, b) => a + b, 0) / taxis.length;
            return { lat, lon, count: taxis.length };
        })
        .sort((a, b) => b.count - a.count)
        .slice(0, 10);

    // Reverse geocode to get address and Google Maps link per area
    const areaRes = await Promise.all(
        topClusters.map(async area => {
            const address = await reverseGeocode(area.lat, area.lon);
            return {
                ...area,
                address,
                googleMapsLink: `https://www.google.com/maps/search/?api=1&query=${area.lat},${area.lon}`,
            };
        })
    );

    const res = {
        total_taxis: coords.length,
        areas: areaRes,
    }

    // Cache result and return
    cache.set("taxiAvalability", res);
    return res;
}