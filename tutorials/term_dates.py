from datetime import date, timedelta, datetime

TERM_DATES = {
    'sept-christmas': {
        'start_date': (9, 1),   # (Month, Day)
        'end_date': (12, 20),
    },
    'jan-easter': {
        'start_date': (1, 6),
        'end_date': (4, 10),
    },
    'may-july': {
        'start_date': (5, 1),
        'end_date': (7, 31),
    },
}

def get_term(input_date):
    """
    Calculate term start and end dates for the given term and reference year.
    """
    if isinstance(input_date, datetime):
        input_date = input_date.date()
    reference_year = input_date.year

    for term, dates in TERM_DATES.items():
        start_month, start_day = dates['start_date']
        end_month, end_day = dates['end_date']

        # Handle terms that span the year boundary (e.g., Sept-Dec crossing into the next year)
        if start_month > end_month:
            # Term starts in the previous year and ends in the current year
            start_date = date(reference_year - 1, start_month, start_day)
            end_date = date(reference_year, end_month, end_day)
        else:
            # Term is within the same year
            start_date = date(reference_year, start_month, start_day)
            end_date = date(reference_year, end_month, end_day)

        # Check if the input date falls within this term's date range
        if start_date <= input_date <= end_date:
            return {
                'term': term,
                'start_date': start_date,
                'end_date': end_date,
            }
    
    raise ValueError(f"Invalid date {input_date}: not in term time.")
