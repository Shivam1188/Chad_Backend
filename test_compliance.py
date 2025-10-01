#!/usr/bin/env python3

# Test script for GDPR/CCPA compliance filtering

from app.main import is_public_record

def test_is_public_record():
    # Test cases
    test_records = [
        # Public record (no personal fields)
        {
            "name": "Product A",
            "description": "A great product",
            "price": "10.99"
        },
        # Non-public record (has email)
        {
            "name": "Product B",
            "email": "user@example.com",
            "description": "Another product"
        },
        # Non-public record (has phone)
        {
            "name": "Product C",
            "phone": "123-456-7890",
            "description": "Third product"
        },
        # Non-public record (has personal_id)
        {
            "name": "Product D",
            "personal_id": "123456789",
            "description": "Fourth product"
        },
        # Public record (empty personal fields don't count)
        {
            "name": "Product E",
            "email": "",
            "phone": None,
            "description": "Fifth product"
        }
    ]

    print("Testing is_public_record function:")
    for i, record in enumerate(test_records, 1):
        result = is_public_record(record)
        status = "PUBLIC" if result else "NON-PUBLIC"
        print(f"Record {i}: {status} - {record}")

if __name__ == "__main__":
    test_is_public_record()
