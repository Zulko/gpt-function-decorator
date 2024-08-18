# gpt-function-decorator

[![PyPI](https://img.shields.io/pypi/v/gpt-function-decorator.svg)](https://pypi.org/project/gpt-function-decorator/)
[![Tests](https://github.com/zulko/gpt-function-decorator/actions/workflows/test.yml/badge.svg)](https://github.com/zulko/gpt-function-decorator/actions/workflows/test.yml)
[![Changelog](https://img.shields.io/github/v/release/zulko/gpt-function-decorator?include_prereleases&label=changelog)](https://github.com/zulko/gpt-function-decorator/releases)
[![License](https://img.shields.io/badge/license-Apache%202.0-blue.svg)](https://github.com/zulko/gpt-function-decorator/blob/main/LICENSE)

This library provides a decorator to define no-code functions that will be "run" by ChatGPT:

```python
from gpt_function_decorator import gpt_function

@gpt_function
def synonym(word, tone='formal'):
    """Return a {tone} synonym of {word}."""

# And just like that, you have a new python function:

synonym("man", tone="slang") # returns "dude"
synonym("man", tone="formal") # returns "male"
synonym("man", tone="academic") # returns "individual"
```

Here is another one I love (I built a [whole website](https://github.com/Zulko/composer-timelines) on top of it):

```python
@gpt_function
def list_famous_composers(n) -> list[str]:
    "Return the {n} most famous composers."
    
list_famous_composers(20)
# Returns ['Johann Sebastian Bach',  'Ludwig van Beethoven', ...]
```

The library relies on the new OpenAI [structured outputs](https://platform.openai.com/docs/guides/structured-outputs/introduction) which can generate output with complex, composite output schemas, and adds automation so the types don't have to be defined with Pydantic.

Yes, using ChatGPT results in unpredictable and unreliable answers. But leveraged on the right use-cases, such functions can replace hundreds of lines of code and save hours of scripting headaches.


## Acknowledging Marvin

In a classic case of *"woops I couldn't find a library that did this until I developed my own"*, I realized after pushing this online that [marvin](https://github.com/PrefectHQ/marvin/) had had an equivalent feature for over a year:

```python
#pip import marvin
import marvin

@marvin.fn
def sentiment(text: str) -> float:
    """Returns a sentiment score for `text`
    between -1 (negative) and 1 (positive).
    """

sentiment("I love working with Marvin!") # 0.8
```

Marvin's huge advantage was the possibility to enforce the output schema, however this is now a native feature of the OpenAI API, which makes the `gpt_function` much more lightweight compared to Marvin's `fn` (the core logics are really ~40 lines of code, with `openai` as the only dependency).


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

In its most basic form, just import the decorator, and apply it to a function with a docstring.
By default, the function will return a string.

```python
from gpt_function_decorator import gpt_function

@gpt_function
def format_date(date):
    """Format {date} as yyyy-mm-dd"""

# Let's try it!
format_date("December 9th, 1992.")

# Returns:
'1992-12-09'
```

Functions defined with the decorator can have multiple arguments and keyword arguments, and you can specify the returned type with the usual type hint  `->`

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

You can provide any simple output format directly (`-> int`, `-> float`, etc.). Lists should always declare the element type (for instance `list[str]`).

The OpenAI API doesn't seem to like types like `tuple` too much, and will complain if you have a type like `Dict` but don't specify the keys. If you really want to specify a `Dict` output with minimal boilerplate you can use the `TypedDict`: 

```python
from typing_extensions import TypedDict # or just typing, for Python>=3.12

@gpt_function
def first_us_presidents(n) -> list[TypedDict("i", dict(birth_year=int, name=str))]:
    """Return the {n} first US presidents with their birth year"""

first_us_presidents(3)
# [{'year': 1732, 'name': 'George Washington'},
#  {'year': 1735, 'name': 'John Adams'},
#  {'year': 1751, 'name': 'Thomas Jefferson'}]
```

But really the cleanest (and OpenAI-officially-supported) way is to provide a Pydantic model:

```python
from pydantic import BaseModel

class USPresident(BaseModel):
    name: str
    birth_year: int

@gpt_function
def first_us_presidents(n) -> list[USPresident]:
    """Return the {n} first US presidents with their birth year"""

first_us_presidents(3)
# [President(name='George Washington', birth_year=1732),
#  President(name='John Adams', birth_year=1735),
#  President(name='Thomas Jefferson', birth_year=1743)]
```

With Pydantic models you can have output schemas as nested and complex as you like (see [the docs](https://cookbook.openai.com/examples/structured_outputs_intro)), although it seems that the more difficult you'll make it for the GPT to understand how to fill the schema, the longer it's take.

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