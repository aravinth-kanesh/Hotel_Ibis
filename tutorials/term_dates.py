from datetime import date

# Defines a dictionary, with the start and end dates for the three academic terms.
TERM_DATES = {
    'sept-christmas': {
        'start_date': date(2024, 9, 1),
        'end_date': date(2024, 12, 20),
    },
    'jan-easter': {
        'start_date': date(2025, 1, 6),
        'end_date': date(2025, 4, 10),
    },
    'may-july': {
        'start_date': date(2025, 5, 1),
        'end_date': date(2025, 7, 31),
    },
}