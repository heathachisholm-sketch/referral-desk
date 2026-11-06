"""
Synthetic, fictional clinics for the front-office handoff demo.

Availability-only: there is deliberately NO scar-type or provider-matching
logic here — that lives in Mended Skin's private production system. These are
invented clinics; no real clinics, addresses, or practitioners.
"""

CLINICS = [
    {"id": "clinic_north", "name": "Northgate Skin Clinic",
     "area": "Manchester", "accepting_enquiries": True},
    {"id": "clinic_river", "name": "Riverside Dermatology",
     "area": "Leeds", "accepting_enquiries": True},
    {"id": "clinic_park", "name": "Parkview Scar Clinic",
     "area": "Bristol", "accepting_enquiries": False},
]
