"""GraphQL queries for the Skypicker/Kiwi API."""

# Location search query
PLACES_QUERY = """
query UmbrellaPlacesQuery(
    $search: PlacesSearchInput
    $filter: PlacesFilterInput
    $options: PlacesOptionsInput
    $first: Int!
) {
    places(search: $search, filter: $filter, options: $options, first: $first) {
        __typename
        ... on AppError {
            error: message
        }
        ... on PlaceConnection {
            edges {
                node {
                    __typename
                    id
                    legacyId
                    name
                    slug
                    gps { lat lng }
                    ... on Station {
                        type
                        code
                        city {
                            name
                            country { name code }
                        }
                    }
                    ... on City {
                        code
                        country { name code }
                    }
                }
            }
        }
    }
}
"""

# One-way flight search query
ONEWAY_SEARCH_QUERY = """
query SearchOneWayItinerariesQuery(
    $search: SearchOnewayInput
    $filter: ItinerariesFilterInput
    $options: ItinerariesOptionsInput
) {
    onewayItineraries(search: $search, filter: $filter, options: $options) {
        __typename
        ... on AppError {
            error: message
        }
        ... on Itineraries {
            itineraries {
                __typename
                ... on ItineraryOneWay {
                    id
                    price { amount }
                    priceEur { amount }
                    sector {
                        duration
                        sectorSegments {
                            segment {
                                source {
                                    station { code name }
                                    localTime
                                }
                                destination {
                                    station { code name }
                                    localTime
                                }
                                duration
                                carrier { code name }
                            }
                        }
                    }
                    bookingOptions {
                        edges {
                            node { bookingUrl }
                        }
                    }
                }
            }
        }
    }
}
"""

# Round-trip flight search query
ROUNDTRIP_SEARCH_QUERY = """
query SearchReturnItinerariesQuery(
    $search: SearchReturnInput
    $filter: ItinerariesFilterInput
    $options: ItinerariesOptionsInput
) {
    returnItineraries(search: $search, filter: $filter, options: $options) {
        __typename
        ... on AppError {
            error: message
        }
        ... on Itineraries {
            itineraries {
                __typename
                ... on ItineraryReturn {
                    id
                    price { amount }
                    bagsInfo {
                        includedCheckedBags
                        checkedBagTiers {
                            tierPrice { amount }
                        }
                    }
                    outbound {
                        duration
                        sectorSegments {
                            segment {
                                source {
                                    station { code name }
                                    localTime
                                }
                                destination {
                                    station {
                                        code
                                        name
                                        city {
                                            name
                                            country { code name }
                                        }
                                    }
                                    localTime
                                }
                                duration
                                carrier { code name }
                            }
                        }
                    }
                    inbound {
                        duration
                        sectorSegments {
                            segment {
                                source {
                                    station { code name }
                                    localTime
                                }
                                destination {
                                    station { code name }
                                    localTime
                                }
                                duration
                                carrier { code name }
                            }
                        }
                    }
                    bookingOptions {
                        edges {
                            node { bookingUrl }
                        }
                    }
                }
            }
        }
    }
}
"""
