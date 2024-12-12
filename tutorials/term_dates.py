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

        if start_month > end_month:
            start_date = date(reference_year - 1, start_month, start_day)
            end_date = date(reference_year, end_month, end_day)
        else:
            start_date = date(reference_year, start_month, start_day)
            end_date = date(reference_year, end_month, end_day)
            
        if start_date <= input_date <= end_date:
            return {
                'term': term,
                'start_date': start_date,
                'end_date': end_date,
            }
    
    raise ValueError(f"Invalid date {input_date}: not in term time.")
