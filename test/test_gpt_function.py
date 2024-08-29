from gpt_function_decorator import gpt_function
from pydantic import BaseModel, Field
from typing import List


def test_interpolated_docstring():
    @gpt_function
    def format_date(date):
        """Format {date} as yyyy-mm-dd"""

    assert format_date("December 9, 1992.") == "1992-12-09"


def test_uninterpolated_docstrings_work():
    @gpt_function
    def format_date(date):
        """Format the date as yyyy-mm-dd"""

    assert format_date("December 9, 1992.") == "1992-12-09"


def test_integer_output():
    @gpt_function
    def positivity(sentence) -> int:
        """Return the positivity of "{sentence}" on a 0-100 scale"""

    assert positivity("I am desperate") < 50


def test_list_of_str_output():
    @gpt_function
    def list_famous_composers(n) -> List[str]:
        "Return the {n} most famous composers."

    assert len(list_famous_composers(2)) == 2


def test_list_of_pydantic_output():
    class USPresident(BaseModel):
        birth_year: int
        name: str

    @gpt_function
    def first_us_presidents(n) -> List[USPresident]:
        """Return the {n} first US presidents with their birth year"""

    assert first_us_presidents(1)[0].birth_year == 1732


def test_list_of_pydantic_outputs_with_fields():
    class USPresident(BaseModel):
        birth_date: str = Field(description="date in yyyy-mm-dd")
        name: str = Field(description="Family name")

    @gpt_function
    def first_us_presidents(n) -> List[USPresident]:
        """Return the {n} first US presidents with their birth year"""

    assert first_us_presidents(1)[0].name == "Washington"


def test_class_constructor():

    class Car(BaseModel):
        brand: str
        age: int
        damaged: bool

        @staticmethod
        @gpt_function
        def from_description(description) -> "Car":
            """Extract car properties from the description."""


def test_reasoned_answer():
    @gpt_function
    def could_have_met(person: str, celebrities: list) -> List[str]:
        """List the names in {celebrities} that {person} could have met."""

    answer = could_have_met(
        "Chopin",
        celebrities=[
            "Napoleon",
            "Jefferson",
            "Mozart",
            "Julius Cesar",
            "Peggy Lee",
            "Beethoven",
        ],
        gpt_reasoning=True,
    )
    assert len(answer.__reasoning__) > 30
