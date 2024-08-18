# gpt-function-decorator

[![PyPI](https://img.shields.io/pypi/v/gpt-function-decorator.svg)](https://pypi.org/project/gpt-function-decorator/)
[![Tests](https://github.com/zulko/gpt-function-decorator/actions/workflows/test.yml/badge.svg)](https://github.com/zulko/gpt-function-decorator/actions/workflows/test.yml)
[![Changelog](https://img.shields.io/github/v/release/zulko/gpt-function-decorator?include_prereleases&label=changelog)](https://github.com/zulko/gpt-function-decorator/releases)
[![License](https://img.shields.io/badge/license-Apache%202.0-blue.svg)](https://github.com/zulko/gpt-function-decorator/blob/main/LICENSE)

This library provides a decorator to define no-code functions that will be "run" by ChatGPT:

```python
from gpt_function_decorator import gpt_function

@gpt_function
def format_date(date):
    """Format {date} as yyyy-mm-dd"""

# And just like that, you have a new python function:

format_date("December 9, 1992.") # returns '1992-12-09'
format_date("On May the 4th 1979") # returns '1992-05-04'
format_date("12/31/2008.") # returns '2008-12-31'
```

Here is another example with a more structured output:

```python
from gpt_function_decorator import gpt_function, ReasonedAnswer

@gpt_function
def deduplicate_celebrities(names) -> ReasonedAnswer(list[str]):
    """Deduplicate the list of celebrities {names}."""

celebrities = [
    "Leo Messi",
    "Mozart",
    "W. A. Mozart",
    "Lionel Messi",
    "Leo diCaprio"
]
answer = deduplicate_celebrities(celebrities)

print (answer.result)
# ['Leo Messi', 'Mozart', 'Leo diCaprio']

print (answer.reasoning)
# `Leo Messi` and `Lionel Messi` refer to the same person,
# and `Mozart` and `W. A. Mozart` also refer to the same individual.
# We include `Leo diCaprio` as it is a distinct name.

```

The library relies on the new OpenAI's new [structured outputs](https://platform.openai.com/docs/guides/structured-outputs/introduction) feature which can generate results with complex nested schemas. This service can definitely be to unpredictable or unreliable for complex or open-ended queries. But leveraged on the right use-cases and with the right specifications, it can also replace hours of scripting and hundreds of lines of code.

## Acknowledging Marvin

In a classic case of *"woops I found a library that did this after I developed my own"*, I realized after releasing `gpt_function_decorator` that another library, [marvin](https://github.com/PrefectHQ/marvin/), had had an equivalent feature for over a year:

```python
@marvin.fn
def sentiment(text: str) -> float:
    """Returns a sentiment score for `text`
    between -1 (negative) and 1 (positive).
    """
```

One advantage of `marvin` has been the possibility to enforce an output schema, however this is now a feature we get for free from the OpenAI API. In comparison, the `gpt_function`, which leverages this OpenAI feature, is more lightweight (it only depends on `openai`, and the core logics is ~50 lines of code).


## Installation and setup

Install this library using `pip`:
```bash
pip install gpt-function-decorator
```

This package requires an OpenAI API key. To get one you need to open an account, add credits to your account (2$ should last you a long time), generate an API key, and store it into an environment variable `OPENAI_API_KEY` (see [the OpenAI docs](https://platform.openai.com/docs/quickstart)).

The key will then be automatically detected by `gpt_function`. If you or your users ever need to juggle OpenAI clients with different API keys, projects, etc. you can override gpt_function's OpenAI client at any point of the execution with the following:

```python
import gpt_function_decorator
from openai import OpenAI
...
gpt_function_decorator.SETTINGS["openai_client"] = OpenAI(api_key="...", ...)
```

## Usage:


### Basics

Import the decorator and apply it to a function whose docstring references the parameters as follows

```python
@gpt_function
def species(breed):
    """Return the species name (cat, dog, ...) of {breed}"""

species("German Shepard") # Returns "dog"
species("Siamese") # Returns "cat"
species("Black widow") # Returns "spider"
```

By default, functions decorated with `@gpt_function` return a string, but you can specify the returned type with the usual hint  `->` in your function:

```python
@gpt_function
def list_famous_composers(n) -> list[str]:
    "Return the {n} most famous composers."
    
list_famous_composers(20)
# Returns ['Johann Sebastian Bach',  'Ludwig van Beethoven', ...]
```

(Shameless ad: if classical music is your thing, I built a [GPT-automated website](https://github.com/Zulko/composer-timelines) on top of this function and a few others powered by ChatGPT)

A `gpt_function`-decorated method can also have multiple arguments and keyword arguments:

```python
from gpt_function_decorator import gpt_function

@gpt_function
def synonym(word, tone='formal'):
    """Return a {tone} synonym of {word}."""

# Let's try it!

synonym("man", tone="slang") # returns "dude"
synonym("man", tone="formal") # returns "male"
synonym("man", tone="academic") # returns "individual"
```

Putting everything together in this example:

```python
@gpt_function
def find_words_in_text(text, categories, limit=3) -> list[str]:
    """Return at most {limit} words from "{text}" related to {categories}"""

# Call:
text = "The sailor's dog and cat ate a basket of apples and biscuits"
find_words_in_text(text, categories=["animal", "food"])

# Returns:
['dog', 'cat', 'apples']
```

### Advanced output formatting

You can provide any simple output format directly in the function signature with `-> int`, `-> float`, etc. Lists should always declare the element type (for instance `list[str]`).

The OpenAI API doesn't seem to like types like `tuple` too much, and will refuse a `Dict` type as it doesn't know what key names to use. If To specify a `Dict` output with minimal boilerplate you can use the `TypedDict`: 

```python
from typing_extensions import TypedDict # or just "typing", for Python>=3.12

@gpt_function
def first_us_presidents(n) -> list[TypedDict("i", dict(birth=int, name=str))]:
    """Return the {n} first US presidents with their birth year"""

first_us_presidents(3)
# [{'birth': 1732, 'name': 'George Washington'},
#  {'birth': 1735, 'name': 'John Adams'},
#  {'birth': 1751, 'name': 'Thomas Jefferson'}]
```

But really the cleanest way (also officially supported by OpenAI) is to provide a Pydantic model as type:

```python
from pydantic import BaseModel

class USPresident(BaseModel):
    birth: int
    name: str
    

@gpt_function
def first_us_presidents(n) -> list[USPresident]:
    """Return the {n} first US presidents with their birth year"""

first_us_presidents(3)
# [USPresident(birth=1732, name='George Washington'),
#  USPresident(birth=1735, name='John Adams'),
#  USPresident(birth=1743, name='Thomas Jefferson')]
```

With Pydantic models you can have output schemas as nested and complex as you like (see [the docs](https://cookbook.openai.com/examples/structured_outputs_intro)), although it seems that the more difficult you'll make it for the GPT to understand how to fill the schema, the longer it will take (not sure about costs).

### Using `gpt_function` on class methods

Class methods can use the `gpt_function`. The `self` can then be used in the docstring but beware that only access to attributes, not other methods, is supported at the moment (attributes computed via `property` are also supported)

```python
from gpt_function_decorator import gpt_function
from typing_extensions import TypedDict


class City:
    
    def __init__(self, name, country):
        self.name = name
        self.country = country
    
    @property
    def full_name(self):
        return f"{self.name} ({self.country})"
    
    @gpt_function
    def tell_event(self, period) -> list[TypedDict("o", {"year": int, "event": str})]:
        """List events from {period} that happened in {self.full_name}"""

city = City("Boston", "England")
city.tell_event(period="14th century", gpt_model="gpt-4o-2024-08-06")

# [{'year': 1313, 'event': 'Boston fairs are among the busiest...'},
#  {'year': 1390, 'event': 'Boston Guildhall is constructed...'},
#  ...]
```

### Parameters for the GPT model

The `gpt_function` decorator adds two parameters to the function it decorates:
- `gpt_model`: this allows the function's user to switch between `gpt-4o-mini` (the default, fast and cheap but less capable) and `gpt-4o` (any compatible version).
- `gpt_system_prompt`: this enables the user to tweak the answer as they would like by asking the GPT to focus on some aspects, or to roleplay.

For instance we can start from this decent function:

```python
@gpt_function
def list_movies(actor, n=2) -> list[str]:
    """Return the titles of at most {n} great movies featuring {actor}."""
    
list_movies("Leonardo DiCaprio")
# ['The Revenant', 'Inception']
```

And now let's ask for a more specific list and a better (more expensive) GPT model:

```python
list_movies(
    "Leonardo DiCaprio",
    gpt_system_prompt="Don't list movies released before 2020.",
    gpt_model="gpt-4o-2024-08-06" #gpt-4o knows more than -mini
)
# ['Django Unchained', 'Once Upon a Time in Hollywood']
```

### Asking the GPT for a reasoned answer

Consider this function:

```python
@gpt_function
def could_have_met(person: str, celebrities: list) -> list[str]:
    """List the celebrities in {celebrities} that {person} could have met."""

celebrities = [
    "Napoleon", "Jefferson", "Mozart", "Julius Cesar", "Peggy Lee", "Beethoven"
]
answer = could_have_met("Chopin", celebrities)
```

Despite the short prompt, this would require some reasoning from the GPT : first listing everyone's birth and death years, then checking who overlapped with Chopin. It turns out `gpt4-o-mini` absolutely fails at this: its answers would typically include Peggy Lee, who lived in a different century.


To get a smarter answer, we provide a `ReasonedAnswer` constructor for the output schema. Concretely, it requests the GPT answer to be a have two fields, `reasoning` and `result`.

This causes the answers to be more verbose, which is slower and more costly but also resolves many issues:
- The `reasoning` field gives the GPT room to "think through" the problem and produce better answers.
- It is now possible for the user to see what the GPT's "reasoning" was, and whether a wrong answer was caused by a lack of knowledge, or logics, etc.
- It reduces the risk that some of GPT's reasoning and formatting ends up polluting the result's schema.

So let's just change our function's output to `ReasonedAnswer(list[str])` and observe the improvement:

```python
from gpt_function_decorator import gpt_function, ReasonedAnswer

@gpt_function
def could_have_met(person, celebrities) -> ReasonedAnswer(list[str]):
    """List the celebrities in {celebrities} that that {person} could have met."""

celebrities = [
    "Napoleon", "Jefferson", "Mozart", "Julius Cesar", "Peggy Lee", "Beethoven"
]

answer = could_have_met("Chopin", celebrities)
print (answer.result)
# ['Napoleon', 'Jefferson', 'Beethoven']

print (answer.reasoning)
# Frédéric Chopin was born in 1810 and died in 1849. To determine which
# celebrities he could have met, we need to consider the lifespans of
# each individual listed:  
# - Napoleon Bonaparte (1769-1821) could have met Chopin.  
# - Thomas Jefferson (1743-1826) could have met Chopin.  
# - Wolfgang Amadeus Mozart (1756-1791) could not have met Chopin,
#   as he died before Chopin was born.  
# - Julius Caesar (100 BC-44 BC) definitely could not have met Chopin,
#   as he lived in ancient times.  
# - Peggy Lee (1920-2002) could not have met Chopin, as she was born
#   after Chopin died.  
# - Ludwig van Beethoven (1770-1827) could have met Chopin.  
```



## Limitations

Ye be warned:

- Only people who have an OpenAI API key will be able to use these functions.
- GPTs have a token size limit so these functions will fail if your inputs or outputs are too large (long lists, etc.)
- GPT answers can be changing and unreliable.
- Calls to OpenAI-powered functions generally have a ~0.5-1 second of overhead then get slower as the input and output increase in size. So pure-python solutions will often beat GPT-based solutions. Sometimes it's better to just ask the ChatGPT app for python code and run the python code.


## A future with GPT-powered functions?

GPTs are not yet fast and cheap enough to be used anywhere, but when they are it will transform a lot of how we write code (assuming we still code).

For instance instead of having developers write zillions of messages to help users troubleshoot errors, we'll use a function like this:

```python
@gpt_function
def help_troubleshoot(error_traceback: str) -> ReasonedAnswer(str):
    """Return a short analysis of the Python error: {error_traceback}"""
```

With this we can write a function that queries webpages and looks into the issue if need be:

```python
import requests
import traceback


def query_webpages_and_help_troubleshoot(url):
    try:
        requests.get(url)
    except Exception as error:
        gpt_advice = help_troubleshoot(traceback.format_exc())
        raise Exception(str(gpt_advice)) from error
```

And now we can run it into a wall and watch it understand the issue:

```python
query_webpages_and_help_troubleshoot("https://wykipedia.com")

# Raises:
"""
< traceback with ConnectionError, MaxRetryError, etc... />

Exception: The immediate cause of the error is an inability to resolve the
hostname 'wykipedia.com'. To resolve this, ensure the URL is correctly
spelled as 'wikipedia.com'.

GPT reasoning: The error traceback indicates that the Python script attempted
to make a network request to 'wykipedia.com' using the requests library. The
main issue arises from the `socket.gaierror` ... etc.
"""
```

## Contribute!

This open-source project is hosted on Github under the Apache 2.0 license. Everyone is welcome to contribute!

To release a new version:
- Increment the version number in `pyproject.toml`
- Create a new-release with that version on Github.
- The Github Actions will pick it from there and publish

## Thanks

Thanks to Simon Willison for his [python library project template](https://github.com/simonw/python-lib).