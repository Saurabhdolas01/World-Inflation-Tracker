"""
The full country list for the tracker comes from the World Bank's own
`/v2/country` endpoint at fetch time (so it stays current and covers every
reporting country, not a hand-maintained subset).

This file only holds the smaller list of major economies we also pull a
*monthly* CPI index for from the IMF (IFS), for the Compare view's monthly
trend chart. IMF IFS does not cover every country, so this is deliberately a
curated subset -- roughly G20 + a few regional anchors with good IMF
coverage. Codes are ISO 3166-1 alpha-3, matching both the World Bank and IMF
country codes.
"""

MAJOR_ECONOMIES = [
    "ARG", "AUS", "BRA", "CAN", "CHN", "FRA", "DEU", "IND", "IDN", "ITA",
    "JPN", "MEX", "SAU", "ZAF", "KOR", "TUR", "GBR", "USA", "PAK", "SGP",
    "CHE", "NGA", "EGY", "VNM", "THA", "POL",
]
