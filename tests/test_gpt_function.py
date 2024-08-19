from gpt_function_decorator import gpt_function


def test_that_interpolated_docstrings_work():
    @gpt_function
    def format_date(date):
        """Format {date} as yyyy-mm-dd"""

    assert format_date("December 9, 1992.") == "1992-12-09"


def test_that_uninterpolated_docstrings_work():
    @gpt_function
    def format_date(date):
        """Format the date as yyyy-mm-dd"""

    assert format_date("December 9, 1992.") == "1992-12-09"
