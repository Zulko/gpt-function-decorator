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
    """Format the date as yyyy-mm-dd"""

# And just like that, you have a new python function:

format_date("December 9, 1992.") # returns '1992-12-09'
format_date("On May the 4th 1979") # returns '1992-05-04'
format_date("12/31/2008.") # returns '2008-12-31'
```

Here is another example with a more structured output:

```python
from gpt_function_decorator import gpt_function

@gpt_function
def deduplicate_celebrities(names) -> list[str]:
    """Return the deduplicated version of the celebrities list."""

celebrities = [
    "Leo Messi",
    "Mozart",
    "W. A. Mozart",
    "Lionel Messi",
    "Leo diCaprio"
]
answer = deduplicate_celebrities(celebrities, gpt_reasoning=true)

print (answer)
# ['Leo Messi', 'Mozart', 'Leo diCaprio']

print (answer.__reasoning__)
# `Leo Messi` and `Lionel Messi` refer to the same person,
# and `Mozart` and `W. A. Mozart` also refer to the same individual.
# We include `Leo diCaprio` as it is a distinct name.

```

The library relies on OpenAI's new [structured outputs](https://platform.openai.com/docs/guides/structured-outputs/introduction) feature, which enables complex output schemas. GPTs can definitely be unreliable for complex and open-ended tasks, but leveraged on the right use-cases they can replace hours of scripting and hundreds of lines of code.

## Acknowledging Marvin

In a classic case of *"oops I had not realized there was already a library for this"*, I only discovered after releasing `gpt_function_decorator` that another library, [marvin](https://github.com/PrefectHQ/marvin/), had had an equivalent feature for over a year:

```python
@marvin.fn
def sentiment(text: str) -> float:
    """Returns a sentiment score for `text`
    between -1 (negative) and 1 (positive).
    """
```

One advantage of `marvin` has been the possibility to enforce an output schema, however this is now a feature we get for free from the OpenAI API. In comparison, the `gpt_function`, which leverages the new OpenAI feature, is much more lightweight (it only depends on `openai`, and the core logics is ~50 lines of code) and provides extra practical features like automated keyword arguments and reasoned answers.


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

Import the decorator and apply it to a function whose docstring explains what to do with the parameters. The docstring can 


```python
from gpt_function_decorator import gpt_function

@gpt_function
def synonym(word, tone='formal'):
    """Return a synonym of the word with the given tone."""

# Let's try it!

synonym("man", tone="slang") # returns "dude"
synonym("man", tone="formal") # returns "male" or "gentleman"
synonym("man", tone="academic") # returns "individual" or "male"
```

The docstring can be any normal Python docstring. Longer docstrings, as long as they are well-written, will not only make your function more user-friendly but be used by the GPT to better understand your intended inputs outputs and outputs (GPTs love to be given examples on which they can model their output):

```python
@gpt_function
def species(breed):
    """Return the species for the given breed.
    
    Parameters
    ----------
    breed:
       The name of the breed.

    Examples
    --------
    >>> species("Fox Terrier") # Returns "dog"
    >>> species("Eagle") # Returns "bird"
    """

species("German Shepard") # Returns "dog"
species("Siamese") # Returns "cat"
species("Black widow") # Returns "spider"
```

### Formatted docstrings

This is a library for lazy people, and as an option you can write the docstring as below so the `{bracketed}` fields will get replaced by the function's parameters. In some cases this can help ChatGPT as it will be presented with a shorter and more to-the-point prompt. 

```python
@gpt_function
def find_rhyme(reference_word, topic):
    """Return a word related to {topic} that rhymes with {reference_word}"""
    
find_rhyme("boat", topic="space exploration") # returns "remote"
```

Any argument not converted in the docstring formatting will still be passed to the function on its own. In the example below most arguments are passed in the first sentence (it flows well) but the text will be passed separately.

```python
@gpt_function
def find_words_in_text(text, categories, max=3) -> list[str]:
    """Return at most {max} words of the text that relate to {categories}"""

# Call:
text = "The sailor's dog and cat ate a basket of apples and biscuits"
find_words_in_text(text, categories=["animal", "food"])

# Returns:
['dog', 'cat', 'apples']
```

### Basic output formatting

By default, functions decorated with `@gpt_function` return a string, but you can specify the returned type with the usual hint  `->` in your function:

```python
@gpt_function
def positivity(sentence) -> int:
    """Return the positivity of "{sentence}" on a 0-100 scale"""

positivity("I am desperate") # returns 10
positivity("Everyone was stoked!!!") # returns 90
```

Lists should always declare their element type (for instance `list[str]`):

```python
@gpt_function
def list_famous_composers(n) -> list[str]:
    "Return the {n} most famous composers."
    
list_famous_composers(20)
# Returns ['Johann Sebastian Bach',  'Ludwig van Beethoven', ...]
```

(Shameless ad: if classical music is your thing, I built a [GPT-automated website](https://github.com/Zulko/composer-timelines) on top of this function and a few others powered by ChatGPT)

### Advanced output formatting with Pydantic

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

### Using Pydantic fields to specify outputs

Finally, the `@gpt_function` decorator will also transmit any Pydantic field description to the GPT, which is a nice way to provide more specifications on each element of the output:

```python
from pydantic import BaseModel, Field

class USPresident(BaseModel):
    birth_date: str = Field(description="date in yyyy-mm-dd")
    name: str = Field(description="Family name")

@gpt_function
def first_us_presidents(n) -> list[USPresident]:
    """Return the {n} first US presidents with their birth date"""

first_us_presidents(3)
# [USPresident(birth_date='1732-02-22', name='Washington'),
#  USPresident(birth_date='1735-10-30', name='Adams'),
#  USPresident(birth_date='1751-03-30', name='Jefferson')]
```

### Using `gpt_function` on class methods

Class methods can use the `gpt_function` just like any other function. The `self` can then be used for interpolation in the docstring but beware that only access to attributes, not other class methods, is supported (attributes computed via `property` are also supported)

```python
from gpt_function_decorator import gpt_function
from pydantic import BaseModel

class Event:
    year: int
    summary: str

class City:
    def __init__(self, name, country):
        self.name = name
        self.country = country
    
    @property
    def full_name(self):
        return f"{self.name} ({self.country})"
    
    @gpt_function
    def events(self, period) -> list[Event]:
        """List events from {period} that happened in {self.full_name}"""

city = City("Boston", "England")

city.events(period="14th century", gpt_model="gpt-4o")
# [Event(year=1313, summary='Boston fairs are among the busiest...')
#  Event(year=1390, summary='Boston Guildhall is constructed...'),
#  ...]
```

Class `staticmethods` can also be gpt functions which allows to group a Pydantic output format with a function that generates it: 

```python
from gpt_function_decorator import gpt_function
from pydantic import BaseModel

class Car(BaseModel):
    brand: str
    age: int
    damaged: bool

    @staticmethod
    @gpt_function
    def from_description(description) -> "Car":
        """Extract car properties from the description."""

car = Car.from_description("A 5-year-old Subaru in mint condition")
# Car(brand='Subaru', age=5, damaged=False)
```

### Asking the GPT for a reasoned answer

Consider this function:

```python
@gpt_function
def could_have_met(person: str, celebrities: list) -> list[str]:
    """List the names in {celebrities} that {person} could have met."""

could_have_met("Chopin", celebrities=[
    "Napoleon", "Jefferson", "Mozart", "Julius Cesar", "Peggy Lee", "Beethoven"
])
```

It turns out that this function struggles to find the right answer. Its output (generated by `gpt-4o-mini`) varies a lot and typically includes Peggy Lee, who lived in a different century. This is because this short prompt actually requires real reasoning from the GPT: first listing everyone's birth and death years, then checking who overlapped with Chopin. 

To get a smarter answer, we provide a `gpt_reasoning` parameter to gpt-decorated functions. Concretely, it requests the GPT answer to have two fields, `reasoning` and `result` (the final result will have the reasoning under the `.__reasoning__` attribute). The GPT answers is more verbose, and therefore slower and more costly, but also more helpful:
- The `reasoning` field gives the GPT room to "think through" the problem and produce better answers.
- It is now possible for the user to see what the GPT's "reasoning" was, and whether a wrong answer was caused by a lack of knowledge, or logics, etc.
- It reduces the risk that some of GPT's reasoning and formatting ends up polluting the result's schema.

So let's ask for a reasoning and observe the improvement:

```python
from gpt_function_decorator import gpt_function

@gpt_function
def could_have_met(person, celebrities) -> list[str]:
    """List the names in {celebrities} that {person} could have met."""

celebrities = [
    "Napoleon", "Jefferson", "Mozart", "Julius Cesar", "Peggy Lee", "Beethoven"
]
answer = could_have_met("Chopin", celebrities, gpt_reasoning=True)

print (answer)
# ['Napoleon', 'Jefferson', 'Beethoven']

print (answer.__reasoning__)
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


### Parameters for the GPT model

The `gpt_function` decorator adds two parameters to the function it decorates:
- `gpt_model`: this allows the function's user to switch between `gpt-4o-mini` (the default, fast and cheap but less capable) and `gpt-4o` (any compatible version).
- `gpt_system_prompt`: this enables the user to tweak the answer as they would like by asking the GPT to focus on some aspects, or to roleplay.
- `gpt_reasoning` as described in the previous section.
- `gpt_debug`: this will cause the function to print the full prompt that it sends to the GPT (useful for troubleshooting or just getting a sense of what's going on).

As an example, let's start from this function:

```python
@gpt_function
def list_movies(actor, n=2) -> list[str]:
    """Return {n} movies featuring {actor}, e.g. "Batman", "Up"..."""

list_movies("Brad Pitt")
# ['Fight Club', 'Once Upon a Time in Hollywood']
```

Now when calling this function we also ask for a more specific list, and a better (more expensive) GPT model:

```python
list_movies(
    "Brad Pitt",
    gpt_system_prompt="Don't list movies released before 2020.",
    gpt_model="gpt-4o" #gpt-4o knows more than -mini
)
# ['Bullet Train', 'Babylon']
```


### Async GPT functions

Your GPT function can be `async`, which can be very useful as OpenAI may be slow to answer some requests but will also let you send many requests in parallel:

```python
import asyncio

@gpt_function
async def summarize(text):
    """Summarize the text."""

# In another async function, or directly in a notebook, call the function
# to summarize several texts asynchronously (in "parallel"):
summaries = await asyncio.gather(*[summarize(txt) for txt in texts])
```

For practicality, async functions decorated with `@gpt_function` get an extra parameter `semaphore` which enables to limit the number of concurrent calls to OpenAI. In the example above, if there is a lot of texts to summarize, you could ask for only 10 OpenAI requests at a time:

```python
semaphore = asyncio.Semaphore(10)
summaries = await asyncio.gather(*[
    summarize(txt, semaphore=semaphore) for txt in texts
])
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
@gpt_function(reasoning=True)
def help_troubleshoot(error_traceback: str) -> str:
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
        raise Exception(f"{gpt_advice}\n{gpt_advice.__reasoning__}") from error
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