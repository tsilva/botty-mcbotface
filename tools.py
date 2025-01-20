import os

TOOL_SAVE_MEMORY = {
    "name" : "tool_save_memory",
    "description": "Used to store information the user requested to remember. Can optionally specify index to overwrite existing memories. Memorized information will be used in system prompt.",
    "input_schema": {
        "type": "object",
        "properties": {
            "memory_data": {
                "type": "string",
                "description": "Summarized version of the information to remember, compressed to use the least tokens possible while preserving all relevant facts"
            },
            "index": {
                "type": "integer",
                "description": "Optional index where to store the memory. If provided, overwrites existing memory at that index. If not provided, appends to end of memory list.",
                "minimum": 0
            }
        },
        "required": ["memory_data"]
    }
}
def tool_save_memory(app_context, memory_data: str, index: int = None):
    system_memory = app_context["system_memory"]
    system_memory_max_size = app_context["system_memory_max_size"]

    if index is not None and index < len(system_memory):
        system_memory[index] = memory_data
        status = f"✅ Updated memory `{index}`: `{memory_data}`."
    else:
        system_memory.append(memory_data)
        system_memory[:] = system_memory[:system_memory_max_size]
        status = f"✅ Added new memory: `{memory_data}`."
        
    yield {
        "status" : status,
        "result" : None
    }


TOOL_DELETE_MEMORY = {
    "name": "tool_delete_memory",
    "description": "Used to discard information that was previously stored in memory.",
    "input_schema": {
        "type": "object",
        "properties": {
            "memory_index": {
                "type": "integer",
                "description": "The index of the memory slot to discard. The system prompt enumerates all memories at all times, prefixed by their memory slot, this is what should be referenced."
            }
        },
        "required": ["memory_index"]
    }

}
def tool_delete_memory(app_context, memory_index: int):
    system_memory = app_context["system_memory"]
    memory_data = system_memory[memory_index]
    system_memory.pop(memory_index)

    yield {
        "status" : f"✅ Deleted memory: `{memory_data}`.",
        "result" : None
    }


TOOL_PLACES_NEARBY = {
    "name": "tool_places_nearby",
    "description": "Search for places using Google Places API with various filtering options",
    "input_schema": {
        "type": "object",
        "properties": {
            "type": {
                "type": "string",
                "description": "Type of place to search for",
                "enum": [
                    "accounting", "airport", "amusement_park", "aquarium", "art_gallery", 
                    "atm", "bakery", "bank", "bar", "beauty_salon", "bicycle_store", 
                    "book_store", "bowling_alley", "bus_station", "cafe", "campground",
                    "car_dealer", "car_rental", "car_repair", "car_wash", "casino",
                    "cemetery", "church", "city_hall", "clothing_store", "convenience_store",
                    "courthouse", "dentist", "department_store", "doctor", "drugstore",
                    "electrician", "electronics_store", "embassy", "fire_station", 
                    "florist", "funeral_home", "furniture_store", "gas_station", 
                    "gym", "hair_care", "hardware_store", "hindu_temple", "home_goods_store",
                    "hospital", "insurance_agency", "jewelry_store", "laundry", 
                    "lawyer", "library", "light_rail_station", "liquor_store", 
                    "local_government_office", "locksmith", "lodging", "meal_delivery",
                    "meal_takeaway", "mosque", "movie_rental", "movie_theater", 
                    "moving_company", "museum", "night_club", "painter", "park",
                    "parking", "pet_store", "pharmacy", "physiotherapist", "plumber",
                    "police", "post_office", "primary_school", "real_estate_agency",
                    "restaurant", "roofing_contractor", "rv_park", "school", 
                    "secondary_school", "shoe_store", "shopping_mall", "spa", 
                    "stadium", "storage", "store", "subway_station", "supermarket",
                    "synagogue", "taxi_stand", "tourist_attraction", "train_station",
                    "transit_station", "travel_agency", "university", "veterinary_care",
                    "zoo"
                ]
            },
            "location": {
                "type": "object",
                "properties": {
                    "latitude": {"type": "number", "minimum": -90, "maximum": 90},
                    "longitude": {"type": "number", "minimum": -180, "maximum": 180}
                },
                "required": ["latitude", "longitude"],
                "description": "Geographic coordinates of the search center point"
            },
            "radius": {
                "type": "integer",
                "description": "Search radius in meters",
                "minimum": 1,
                "maximum": 50000
            },
            "keyword": {
                "type": "string",
                "description": "Term to match against all content indexed for this place"
            },
            "language": {
                "type": "string",
                "description": "The language code for the results (e.g., 'en', 'pt')"
            },
            "min_price": {
                "type": "integer",
                "minimum": 0,
                "maximum": 4,
                "description": "Minimum price level (0=most affordable, 4=most expensive)"
            },
            "max_price": {
                "type": "integer",
                "minimum": 0,
                "maximum": 4,
                "description": "Maximum price level (0=most affordable, 4=most expensive)"
            },
            "name": {
                "type": "string",
                "description": "Terms to match against place names"
            },
            "open_now": {
                "type": "boolean",
                "description": "Return only places that are currently open"
            },
            "rank_by": {
                "type": "string",
                "enum": ["prominence", "distance"],
                "description": "Order in which to rank results"
            },
            "page_token": {
                "type": "string",
                "description": "Token for retrieving the next page of results"
            }
        },
        "required": ["location"]
    }
}
def tool_places_nearby(
    app_context,
    location: dict,
    type: str = None,
    radius: int = None,
    keyword: str = None,
    language: str = None,
    min_price: int = None,
    max_price: int = None,
    name: str = None,
    open_now: bool = False,
    rank_by: str = None,
    page_token: str = None
) -> dict:
    import googlemaps
    
    yield {"status" : f"⏳ Searching for locations..."}

    gmaps = googlemaps.Client(key=os.getenv('GOOGLE_MAPS_API_KEY'))

    # Convert location dict to tuple
    location_tuple = (location['latitude'], location['longitude'])
    
    # Build params dict with only non-None values
    params = {
        'type': type,
        'location': location_tuple,
        'keyword': keyword,
        'language': language,
        'min_price': min_price,
        'max_price': max_price,
        'name': name,
        'open_now': open_now,
        'rank_by': rank_by,
        'page_token': page_token
    }
    
    # Add radius if specified (required unless rank_by=distance)
    if radius is not None: params['radius'] = radius
    elif rank_by != 'distance': params['radius'] = 1000  # Default radius
        
    # Remove None values
    params = {k: v for k, v in params.items() if v is not None}
    
    # Make the API call
    result = gmaps.places_nearby(**params)
    locations = result.get('results', [])

    yield {
        "status" : f"✅ Found `{len(locations)}` locations.", 
        "result" : locations
    }


TOOL_CALCULATOR = {
    "name": "tool_calculator",
    "description": "Perform mathematical operations with error handling and precision tracking",
    "input_schema": {
        "type": "object",
        "properties": {
            "first_number": {
                "type": "number",
                "description": "First operand for the calculation"
            },
            "second_number": {
                "type": "number",
                "description": "Second operand for the calculation"
            },
            "operation": {
                "type": "string",
                "description": "Mathematical operation to perform",
                "enum": ["add", "subtract", "multiply", "divide"]
            }
        },
        "required": ["first_number", "second_number", "operation"]
    }
}
def tool_calculator(app_context, first_number, second_number, operation: str):
    x, y = first_number, second_number
    
    result = None
    if operation == "add": result = x + y
    elif operation == "subtract": result = x - y
    elif operation == "multiply": result = x * y
    elif operation == "divide": result = x / y if y != 0 else None

    yield {"result" : f"⏳ Searching for locations..."}
    return result


TOOL_GEOCODE = {
    "name": "tool_geocode",
    "description": "Convert addresses into latitude and longitude coordinates using Google Geocoding API",
    "input_schema": {
        "type": "object",
        "properties": {
            "address": {
                "type": "string",
                "description": "Address to convert to coordinates (e.g. 'Porto, Portugal' or 'Avenida dos Aliados, Porto')"
            }
        },
        "required": ["address"]
    }
}
def tool_geocode(app_context, address: str) -> dict:
    # Haversine formula to calculate the great-circle distance
    def _haversine(lat1, lon1, lat2, lon2):
        import math

        # Convert latitude and longitude from degrees to radians
        lat1, lon1, lat2, lon2 = map(math.radians, [lat1, lon1, lat2, lon2])

        # Radius of Earth in kilometers
        R = 6371.0

        # Differences in coordinates
        dlat = lat2 - lat1
        dlon = lon2 - lon1

        # Haversine formula
        a = math.sin(dlat / 2)**2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlon / 2)**2
        c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
        distance = R * c

        return distance

    import googlemaps
    
    yield {"status" : f"⏳ Geocoding '{address}'..."}

    # TODO: reuse gmaps client
    gmaps = googlemaps.Client(key=os.getenv('GOOGLE_MAPS_API_KEY'))
    
    result = gmaps.geocode(address)

    # Retrieve coordinates
    #location = result[0]['geometry']['location']
    #latitude = location["lat"]
    #longitude = location["lng"]

    # Retrieve bounding box
    bounds = result[0]['geometry']['bounds']
    northeast = bounds['northeast']
    southwest = bounds['southwest']

    # Calculate the center of the bounding box
    center_lat = (northeast['lat'] + southwest['lat']) / 2
    center_lng = (northeast['lng'] + southwest['lng']) / 2
    center = {"lat": center_lat, "lng": center_lng}

    # Calculate the radius of the bounding box
    radius = _haversine(center_lat, center_lng, northeast['lat'], northeast['lng'])

    yield {
        "status" : f"✅ Geocoded `{address}` to center=`({center_lat},{center_lng}), radius={radius}m`.",
        "result" : {
            "center": center,
            "radius" : radius
        }
    }


TOOL_PLACE_DETAILS = {
    "name": "tool_place_details",
    "description": "Get detailed information about a specific place using its place_id from Google Places API",
    "input_schema": {
        "type": "object",
        "properties": {
            "place_id": {
                "type": "string",
                "description": "The place_id of the location to get details for. This can be obtained from the results of places_nearby searches."
            },
            "language": {
                "type": "string",
                "description": "The language code for the results (e.g., 'en', 'pt')"
            },
            "fields": {
                "type": "array",
                "description": "List of specific fields to return. If empty, returns all available fields.",
                "items": {
                    "type": "string",
                    "enum": [
                        "address_component", "adr_address", "business_status", 
                        "formatted_address", "geometry", "icon", "name", 
                        "photo", "place_id", "plus_code", "type",
                        "url", "utc_offset", "vicinity", "formatted_phone_number",
                        "international_phone_number", "opening_hours", 
                        "website", "price_level", "rating", "review",
                        "user_ratings_total"
                    ]
                }
            }
        },
        "required": ["place_id"]
    }
}
def tool_place_details(app_context, place_id: str, language: str = None, fields: list = None) -> dict:
    import googlemaps
    
    yield {"status" : f"⏳ Looking up details on location..."}

    gmaps = googlemaps.Client(key=os.getenv('GOOGLE_MAPS_API_KEY'))
    
    params = {'place_id': place_id}
    if language: params['language'] = language
    if fields: params['fields'] = fields
        
    result = gmaps.place(**params)
    details = result.get('result', {})

    yield {
        "status" : f"✅ Location details fetched.",
        "result" : details
    }
        

TOOLS = (
    (TOOL_SAVE_MEMORY, tool_save_memory),
    (TOOL_DELETE_MEMORY, tool_delete_memory),
    (TOOL_CALCULATOR, tool_calculator),
    (TOOL_PLACES_NEARBY, tool_places_nearby),
    (TOOL_GEOCODE, tool_geocode),
    (TOOL_PLACE_DETAILS, tool_place_details)
)

TOOLS_SPECS = {tool[0]["name"]: tool[0] for tool in TOOLS}

TOOLS_FUNCTIONS = {tool[0]["name"]: tool[1] for tool in TOOLS}
