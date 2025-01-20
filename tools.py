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
                    # Automotive
                    "car_dealer", "car_rental", "car_repair", "car_wash", "electric_vehicle_charging_station", "gas_station", "parking", "rest_stop",

                    # Business
                    "corporate_office", "farm", "ranch",

                    # Culture
                    "art_gallery", "art_studio", "auditorium", "cultural_landmark", "historical_place", "monument", "museum", "performing_arts_theater", "sculpture",

                    # Education
                    "library", "preschool", "primary_school", "school", "secondary_school", "university",

                    # Entertainment and Recreation
                    "adventure_sports_center", "amphitheatre", "amusement_center", "amusement_park", "aquarium", "banquet_hall", "barbecue_area", "botanical_garden",
                    "bowling_alley", "casino", "childrens_camp", "comedy_club", "community_center", "concert_hall", "convention_center", "cultural_center",
                    "cycling_park", "dance_hall", "dog_park", "event_venue", "ferris_wheel", "garden", "hiking_area", "historical_landmark", "internet_cafe",
                    "karaoke", "marina", "movie_rental", "movie_theater", "national_park", "night_club", "observation_deck", "off_roading_area", "opera_house",
                    "park", "philharmonic_hall", "picnic_ground", "planetarium", "plaza", "roller_coaster", "skateboard_park", "state_park", "tourist_attraction",
                    "video_arcade", "visitor_center", "water_park", "wedding_venue", "wildlife_park", "wildlife_refuge", "zoo",

                    # Facilities
                    "public_bath", "public_bathroom", "stable",

                    # Finance
                    "accounting", "atm", "bank",

                    # Food and Drink
                    "acai_shop", "afghani_restaurant", "african_restaurant", "american_restaurant", "asian_restaurant", "bagel_shop", "bakery", "bar",
                    "bar_and_grill", "barbecue_restaurant", "brazilian_restaurant", "breakfast_restaurant", "brunch_restaurant", "buffet_restaurant", "cafe",
                    "cafeteria", "candy_store", "cat_cafe", "chinese_restaurant", "chocolate_factory", "chocolate_shop", "coffee_shop", "confectionery",
                    "deli", "dessert_restaurant", "dessert_shop", "diner", "dog_cafe", "donut_shop", "fast_food_restaurant", "fine_dining_restaurant",
                    "food_court", "french_restaurant", "greek_restaurant", "hamburger_restaurant", "ice_cream_shop", "indian_restaurant", "indonesian_restaurant",
                    "italian_restaurant", "japanese_restaurant", "juice_shop", "korean_restaurant", "lebanese_restaurant", "meal_delivery", "meal_takeaway",
                    "mediterranean_restaurant", "mexican_restaurant", "middle_eastern_restaurant", "pizza_restaurant", "pub", "ramen_restaurant", "restaurant",
                    "sandwich_shop", "seafood_restaurant", "spanish_restaurant", "steak_house", "sushi_restaurant", "tea_house", "thai_restaurant",
                    "turkish_restaurant", "vegan_restaurant", "vegetarian_restaurant", "vietnamese_restaurant", "wine_bar",

                    # Geographical Areas
                    "administrative_area_level_1", "administrative_area_level_2", "country", "locality", "postal_code", "school_district",

                    # Government
                    "city_hall", "courthouse", "embassy", "fire_station", "government_office", "local_government_office", "neighborhood_police_station",
                    "police", "post_office",

                    # Health and Wellness
                    "chiropractor", "dental_clinic", "dentist", "doctor", "drugstore", "hospital", "massage", "medical_lab", "pharmacy", "physiotherapist",
                    "sauna", "skin_care_clinic", "spa", "tanning_studio", "wellness_center", "yoga_studio",

                    # Housing
                    "apartment_building", "apartment_complex", "condominium_complex", "housing_complex",

                    # Lodging
                    "bed_and_breakfast", "budget_japanese_inn", "campground", "camping_cabin", "cottage", "extended_stay_hotel", "farmstay", "guest_house",
                    "hostel", "hotel", "inn", "japanese_inn", "lodging", "mobile_home_park", "motel", "private_guest_room", "resort_hotel", "rv_park",

                    # Natural Features
                    "beach",

                    # Places of Worship
                    "church", "hindu_temple", "mosque", "synagogue",

                    # Services
                    "astrologer", "barber_shop", "beautician", "beauty_salon", "body_art_service", "catering_service", "cemetery", "child_care_agency",
                    "consultant", "courier_service", "electrician", "florist", "food_delivery", "foot_care", "funeral_home", "hair_care", "hair_salon",
                    "insurance_agency", "laundry", "lawyer", "locksmith", "makeup_artist", "moving_company", "nail_salon", "painter", "plumber",
                    "psychic", "real_estate_agency", "roofing_contractor", "storage", "summer_camp_organizer", "tailor", "telecommunications_service_provider",
                    "tour_agency", "tourist_information_center", "travel_agency", "veterinary_care",

                    # Shopping
                    "asian_grocery_store", "auto_parts_store", "bicycle_store", "book_store", "butcher_shop", "cell_phone_store", "clothing_store",
                    "convenience_store", "department_store", "discount_store", "electronics_store", "food_store", "furniture_store", "gift_shop",
                    "grocery_store", "hardware_store", "home_goods_store", "home_improvement_store", "jewelry_store", "liquor_store", "market", "pet_store",
                    "shoe_store", "shopping_mall", "sporting_goods_store", "store", "supermarket", "warehouse_store", "wholesaler",

                    # Sports
                    "arena", "athletic_field", "fishing_charter", "fishing_pond", "fitness_center", "golf_course", "gym", "ice_skating_rink", "playground",
                    "ski_resort", "sports_activity_location", "sports_club", "sports_coaching", "sports_complex", "stadium", "swimming_pool",

                    # Transportation
                    "airport", "airstrip", "bus_station", "bus_stop", "ferry_terminal", "heliport", "international_airport", "light_rail_station",
                    "park_and_ride", "subway_station", "taxi_stand", "train_station", "transit_depot", "transit_station", "truck_stop",

                    # Table B Additional Types
                    "administrative_area_level_3", "administrative_area_level_4", "administrative_area_level_5", "administrative_area_level_6",
                    "administrative_area_level_7", "archipelago", "colloquial_area", "continent", "establishment", "finance", "floor", "food",
                    "general_contractor", "geocode", "health", "intersection", "landmark", "natural_feature", "neighborhood", "place_of_worship",
                    "plus_code", "point_of_interest", "political", "post_box", "postal_code_prefix", "postal_code_suffix", "postal_town", "premise",
                    "room", "route", "street_address", "street_number", "sublocality", "sublocality_level_1", "sublocality_level_2", "sublocality_level_3",
                    "sublocality_level_4", "sublocality_level_5", "subpremise", "town_square"
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
