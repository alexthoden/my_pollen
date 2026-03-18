/**
 * Location Database - Maps city names to coordinates for Pollen API queries
 */

const LOCATION_DATABASE = {
    // Northeast
    "Boston, MA": { lat: 42.3601, lng: -71.0589 },
    "New York, NY": { lat: 40.7128, lng: -74.0060 },
    "Philadelphia, PA": { lat: 39.9526, lng: -75.1652 },
    "Washington, DC": { lat: 38.9072, lng: -77.0369 },
    "Baltimore, MD": { lat: 39.2904, lng: -76.6122 },
    "Rockville, MD": { lat: 39.0840, lng: -77.1436 },
    
    // Southeast
    "Charlotte, NC": { lat: 35.2271, lng: -80.8431 },
    "Atlanta, GA": { lat: 33.7490, lng: -84.3880 },
    "Miami, FL": { lat: 25.7617, lng: -80.1918 },
    "Nashville, TN": { lat: 36.1627, lng: -86.7816 },
    
    // Midwest
    "Chicago, IL": { lat: 41.8781, lng: -87.6298 },
    "Detroit, MI": { lat: 42.3314, lng: -83.0458 },
    "Indianapolis, IN": { lat: 39.7684, lng: -86.1581 },
    "Columbus, OH": { lat: 39.9612, lng: -82.9988 },
    "Minneapolis, MN": { lat: 44.9778, lng: -93.2650 },
    
    // Southwest
    "Dallas, TX": { lat: 32.7767, lng: -96.7970 },
    "Houston, TX": { lat: 29.7604, lng: -95.3698 },
    "Austin, TX": { lat: 30.2672, lng: -97.7431 },
    "Phoenix, AZ": { lat: 33.4484, lng: -112.0742 },
    "Denver, CO": { lat: 39.7392, lng: -104.9903 },
    
    // West Coast
    "Los Angeles, CA": { lat: 34.0522, lng: -118.2437 },
    "San Francisco, CA": { lat: 37.7749, lng: -122.4194 },
    "Seattle, WA": { lat: 47.6062, lng: -122.3321 },
    "Portland, OR": { lat: 45.5152, lng: -122.6784 },
    
    // Mountain
    "Salt Lake City, UT": { lat: 40.7608, lng: -111.8910 },
    "Albuquerque, NM": { lat: 35.0844, lng: -106.6504 },
    
    // Great Plains
    "Kansas City, MO": { lat: 39.0997, lng: -94.5786 },
    "St. Louis, MO": { lat: 38.6270, lng: -90.1994 },
    "Memphis, TN": { lat: 35.1495, lng: -90.0490 },
};

/**
 * Get coordinates for a location name
 * @param {string} locationName - The city name to look up
 * @returns {object|null} { lat, lng } or null if not found
 */
function getLocationCoordinates(locationName) {
    if (!locationName) return null;
    
    // Try exact match first
    if (LOCATION_DATABASE[locationName]) {
        return LOCATION_DATABASE[locationName];
    }
    
    // Try case-insensitive partial match
    const normalized = locationName.trim().toLowerCase();
    for (const [key, coords] of Object.entries(LOCATION_DATABASE)) {
        if (key.toLowerCase() === normalized) {
            return coords;
        }
    }
    
    return null;
}

/**
 * Get all available locations for autocomplete
 * @returns {array} Sorted array of location names
 */
function getAvailableLocations() {
    return Object.keys(LOCATION_DATABASE).sort();
}

/**
 * Format location string (standardizes format)
 * @param {string} location - Location string
 * @returns {string} Standardized location string
 */
function formatLocation(location) {
    if (!location) return "";
    
    // Try to find matching location in database
    const coords = getLocationCoordinates(location);
    
    for (const [key, coord] of Object.entries(LOCATION_DATABASE)) {
        if (coord === coords) {
            return key; // Return standardized format
        }
    }
    
    return location; // Return as-is if not found
}
