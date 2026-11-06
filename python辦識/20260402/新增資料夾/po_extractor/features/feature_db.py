"""
Feature database: keyword signatures for vendor classification.

To add a new vendor (one of your 500+ formats):
    1. Add an entry here with unique keywords
    2. Create a new extractor in extractors/<vendor>.py
    3. Use @ExtractorRegistry.register("<vendor_id>") decorator
"""

FEATURE_DB = [
    {
        "vendor_id": "byd",
        "name": "BYD (H.K.) CO., LIMITED",
        "keywords": [
            "BYD (H.K.) CO., LIMITED",
            "BYD",
        ],
        "priority": 10,
    },
    {
        "vendor_id": "kaifa",
        "name": "Kaifa Technology",
        "keywords": [
            "KAIFA",
            "Kaifa Technology",
            "KFSU",
            "KFML",
        ],
        "priority": 10,
    },
    {
        "vendor_id": "siemens",
        "name": "Siemens",
        "keywords": [
            "Siemens",
            "siemens.com",
            "Siemens Industrial Automation",
            "Siemens Numerical Control",
        ],
        "priority": 10,
    },
    {
        "vendor_id": "desay_sv",
        "name": "DESAY SV / 德赛西威",
        "keywords": [
            "德赛西威",
            "DESAY SV",
            "desaysv.com",
        ],
        "priority": 10,
    },
]
