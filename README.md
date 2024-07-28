# gpt-function-decorator

[![PyPI](https://img.shields.io/pypi/v/gpt-function-decorator.svg)](https://pypi.org/project/gpt-function-decorator/)
[![Tests](https://github.com/zulko/gpt-function-decorator/actions/workflows/test.yml/badge.svg)](https://github.com/zulko/gpt-function-decorator/actions/workflows/test.yml)
[![Changelog](https://img.shields.io/github/v/release/zulko/gpt-function-decorator?include_prereleases&label=changelog)](https://github.com/zulko/gpt-function-decorator/releases)
[![License](https://img.shields.io/badge/license-Apache%202.0-blue.svg)](https://github.com/zulko/gpt-function-decorator/blob/main/LICENSE)

This library provides a decorator to define no-code functions that will be "run" by a GPT:

```python
from gpt_function_decorator import gpt_function

@gpt_function
def synonym(word, tone='formal'):
    """Return a synonym of the word in the given tone."""

# And just like that, you have a new python function:

synonym("man", tone="slang") # returns "dude"
synonym("man", tone="formal") # returns "male"
synonym("man", tone="academic") # returns "individual"
```

At each call the GPT (right now, any model from OpenAI, such as GPT-4o or GPT-4o-mini) looks at the function's parameters and  docstring, and infers what it should return for the given inputs. Yes, this is unreliable, the answer can even change between calls. But leveraged for the right use-cases, such functions can replace hundreds of lines of code and save hours of scripting headaches.

## Installation

Install this library using `pip`:
```bash
pip install gpt-function-decorator
```

## Usage

### Setting up an OpenAI API key

This package requires an OpenAI API key. To get one you need to open an account, add credits to your account (2$ should last you a long time), generate an API key, and store it into an environment variable `OPENAI_API_KEY` (see [the OpenAI docs](https://platform.openai.com/docs/quickstart)).

The key will then be automatically detected by `gpt_function`. If you or your users ever need to juggle OpenAI clients with different API keys, projects, etc. you can override gpt_function's OpenAI client at any point of the execution with the following:

```python
import gpt_function_decorator
from openai import OpenAI
...
gpt_function_decorator.SETTINGS["openai_client"] = OpenAI(api_key="...", ...)
```

### Basic usage:

In its most basic form, just import the decorator, and apply it to a function with a docstring:

```python
from gpt_function_decorator import gpt_function

@gpt_function
def format_date(data):
    """Format the date as "yyyy-mm-dd" """

# Let's try it!
format_date("December 9th, 1992.")

# Returns:
'1992-12-09'
```

Functions defined with the decorator can have multiple arguments and keyword arguments.

```python
@gpt_function
def find_words_in_text(text, categories, max_words=10):
    """Return at most max_words of the text from the provided categories"""

# Call:
text = "The dog in the house ate an apple and a pear from the fridge"
find_words_in_text(text, categories=["animal", "food"])

# Returns:
['dog', 'apple', 'pear']
```

### Controlling the output format

The inputs and outputs can be any usual format, str, list, dict, number. Think "anything that can be represented through JSON".

The basic way to control the output is to describe it. You can go with a very minimal description and let the GPT decide on the details:

```python
@gpt_function
def country_metadata(country):
    """Return the capital city, language, and calling code of each country"""

# Call:
country_metadata(["France", "Japan", "Peru"])

# Returns:
[{'country': 'France',
  'capital': 'Paris',
  'language': 'French',
  'calling_code': '+33'},
 {'country': 'Japan',
  'capital': 'Tokyo',
  'language': 'Japanese',
  'calling_code': '+81'},
 {'country': 'Peru',
  'capital': 'Lima',
  'language': 'Spanish',
  'calling_code': '+51'}]
```

If you want to really control the output schema you must provide it in some way. One nice way is with an example in the docstring:

```python
@gpt_function
def country_metadata(cities):
    """Return the capital city, language, and the calling code of each country

    Example
    -------

    >>> country_metadata(["France"])
    >>> [{'name': 'France', 'capital': 'Paris', 'lang': 'French', 'code': '+33'}]
    """

# Call:
country_metadata(["France", "Japan", "Peru"])

# Returns:
[{'name': 'France', 'capital': 'Paris', 'lang': 'French', 'code': '+33'},
 {'name': 'Japan', 'capital': 'Tokyo', 'lang': 'Japanese', 'code': '+81'},
 {'name': 'Peru', 'capital': 'Lima', 'lang': 'Spanish', 'code': '+51'}]
```

Or you can be fully explicit

```python
@gpt_function
def country_metadata(cities):
    """Return the capital city, language, and the calling code of each country
    using this output format:

    [
        {
            name: str,
            capital: str
            lang: str,
            calling_code: int

        }
        ...
    ]
    """
```

Even this way, though, it might happen that the GPT won't exactly stick to the schema. If this is critical, then you need to validate the output with a schema validation (like [pydantic](https://docs.pydantic.dev/latest/)) and try running the function again if the schema is wrong.

### Selecting the GPT model

By default, `gpt_function` uses `gpt-4o-mini` under the hood, which is 10 times cheaper than `gpt-4o`, much faster and just almost as good (although `gpt-4o` knows more, makes less mistakes, and sometimes cracks better jokes).

You can change the GPT model used via the `gpt_model` argument:

```python
@gpt_function(gpt_model="gpt-4o")
def list_life_events(person):
    """Return a list of the person's life events (year, city, long_summary).
    Give as many details as possible in the long summary."""

# Call:
list_life_events("Mozart")

# Returns:
[{'year': 1756,
  'city': 'Salzburg',
  'long_summary': 'Wolfgang Amadeus Mozart was born on January 27, 1756, ...'},
  ...]
```

Note that, just like for any other parameter of `gpt_function`, users can override it when calling the function:

```python
list_life_events("Mozart", model="gpt-4o-mini")
```

In general, I find `gpt-4o` superior when it comes to reasoning over general culture. This kind of task:

```python
@gpt_function(gpt_model='gpt-4o', think_through=True)
def deduplicate_list_of_celebrities(celebrities):
    """Detect and remove duplicates in the list of celebrities provided
    (consider aliases and diminutives)."""

# Call:
deduplicate_list_of_celebrities([
    "Claude Debussy",
    "Leo Messi",
    "Leonardo diCaprio",
    "Leonardo da Vinci",
    "Clark Kent",
    "Superman",
    "Leo diCaprio",
    "Lionel Messi",
    "Eminem",
    "Marshall Mathers",
    "Claude Achille Debussy"
])

# Result 
['Lionel Messi',
 'Claude Debussy',
 'Leonardo da Vinci',
 'Leonardo diCaprio',
 'Clark Kent',
 'Eminem']
```


### Asking python to "think through" an answer

By default, `gpt_function` tells the GPT *"answer directly without any explanations"*.
When setting `@gpt_function(think_through=True)`, however, it will tell the GPT *"Think carefully through the answer and if the function docstring suggests steps, take these steps"*. This is a mechanism that makes the answer slower and more expensive, but also much higher quality as it enables the GPTs to reason about tasks.

For instance consider this task:

```python
@gpt_function
def could_have_met(person, celebrities):
    """Return the celebrities in the list that the person could have met,
    considering their birth and death dates"""

# Call:
celebrities = [
    "Napoleon", "Jefferson", "Mozart", "Julius Cesar", "Lady Gaga", "Beethoven"
]
could_have_met("Chopin", celebrities)

# Returns:
['Napoleon', 'Mozart', 'Beethoven']
```

Hmmm "Mozart" is wrong (he died 20 years before Chopin was born), and "Jefferson" is missing. 
One reason it's wrong is because the GPT doesn't take time to think through the information that it actually knows.

Now let's ask for a thoughtful answer:


```python
@gpt_function(think_through=True)
def could_have_met_thoughtful_version(person, celebrities):
    """Return the celebrities in the list that the person could have met,
    considering their birth and death dates"""

# Call:
could_have_met_thoughtful_version("Chopin", celebrities)

# Returns:
['Napoleon', 'Jefferson', 'Beethoven']

```

It did it! Here again, if you ask many times you will have wrong answers, but the probability of success is much higher.
You can see the thinking happening by adding `debug=True` to the function call, which returns the full answer from the GPT:

```python
could_have_met_thoughtful_version("Chopin", celebrities, debug=True)

# prints
"""
(...)
To evaluate whether Frédéric Chopin could have met the celebrities listed, we
need to consider the birth and death dates of Chopin and each of the celebrities
mentioned.

1. **Frédéric Chopin**: Born on March 1, 1810, and died on October 17, 1849.

2. **Celebrities**:
   - **Napoleon Bonaparte**: Born on August 15, 1769, and died on May 5, 1821.
(Could have met)
   - **Thomas Jefferson**: Born on April 13, 1743, and died on July 4, 1826.
(Could have met)
   - **Wolfgang Amadeus Mozart**: Born on January 27, 1756, and died on December
5, 1791. (Could not have met)
   - **Julius Caesar**: Born on July 12, 100 BC, and died on March 15, 44 BC.
(Could not have met)
   - **Lady Gaga**: Born on March 28, 1986. (Could not have met)
   - **Ludwig van Beethoven**: Born on December 17, 1770, and died on March 26,
1827. (Could have met)

Based on the analysis, the celebrities that Chopin could have met (those who
lived during his lifespan) are Napoleon Bonaparte, Thomas Jefferson, and Ludwig
van Beethoven.
(...)
"""
```

Where the `think_through` option shines is when you explicitly guide the GPT bot through the steps of a process.

```python

@gpt_function(think_through=True)
def shopping_list_for_national_day_food(country):
    """Return a shopping list for the national day of this country
    
    Step 1: List a starter, a mains and a dessert from this country.
    Step 2: List the ingredients for each dish of Step 1
    Step 3: Generate a shopping list where each Step 2 ingredient only appears once.
    Step 4: Generate a final shopping list without any unhealthy ingredient of Step 3.
    
    Example
    -------
    
    >>> shopping_list_for_national_day_food("France")
    >>> {
        "starter": "friand",
        "main": "frog legs",
        "dessert": "creme-brulee",
        "shopping_list": ["flour", "frog legs", "eggs", ...]
    }
    """

# Call:
shopping_list_for_national_day_food("Italy", debug=True)

# Returns:
{'starter': 'Bruschetta',
 'main': 'Pasta Carbonara',
 'dessert': 'Tiramisu',
 'shopping_list': ['Bread',
  'Tomatoes',
  'Basil',
  '...'
]}
# ... and prints the reasoning over all steps.
```

Another application of the step process is the rewriting of a text until it fits some specs. For instance GPT4 will edit very freely if you ask it to "add humor to a text" (it may write a much longer text, lose facts, joke about tragic events etc.) but we can control the output more finely by commanding a series of rewrites:


```python
@gpt_function(think_through=True, gpt_model="gpt-4o")
def add_humor(text):
    """Rewrite the text with more humor.
    
    Step 1: Rewrite the text with humor. Be funny!
    Step 2: Copy Step 1 without any joke about tragic events.
    Step 3: Copy Step 2 without the weakest jokes if the text is over 60 words
    Step 4: Copy Step 3 with any information from the original that got lost.
    """
    
add_humor("""
In 1806, at the age of 15, Carl Czerny was selected by Beethoven
to perform the premiere of his Piano Concerto No. 1 in Vienna, Austria.
""")


# Response

"""
In 1806, a 15-year-old Carl Czerny probably had bigger worries than what to
wear to prom — he was chosen by Beethoven himself to premiere the Piano
Concerto No. 1 in Vienna, Austria. Imagine the pressure! And this was before
TikTok fame, so Carl had to rely on pure talent.
"""
```

(there's probably funnier jokes to crack, but you can't expect much from a
chatbot going by a spec sheet. ChatGPT can actually be pretty funny if you let
it riff freely)

### Retries

It can happen that the GPT, in a moment of confusion, the GPT doesn't forgets its core instructions and doesn't return valid JSON, or more generally an answer that can be parsed. This is a relatively rare case that is easily solved by re-asking the same query to the GPT.

To simplify this task, `gpt_function` add a parameter `retries`. For instance `retries=2` asks the function to attempt the evaluation at least 3 times in total before erroring.


## How gpt-functions-decorator works

This library doesn't do much, really, all the magic is in how good GPTs have become.
When you define the following function and call:

```python
@gpt_function
def translate(text: str, target="english"):
    """Detect the source language and translate to the target.
    
    >>> translate("Bonjour tout le monde!")
    {"lang": "french", translation: "Hi everyone!"}
    """
```

Then `gpt_function` generates the following system prompt, in which it injects the whole function definition, asks GPT to simulate the function, and makes sure that the output will be easy to find and parse:


```
For the following python function, evaluate the user-provided input.

`` `
@gpt_function
def translate(text: str, target_language="english"):
    """Detect the source language, then translate to the target language.

    >>> translate("Bonjour tout le monde!")
    {"lang": "french", translation: "Hi everyone!"}
    """
`` `

Write the result directly without providing any explanation.
Provide the final output at the end as follows,
where FUNCTION_OUTPUT is in JSON format:

<ANSWER>
{"result": FUNCTION_OUTPUT}
</ANSWER>
```

Then when the user calls
```python
translate("Eine Katze, ein Hund und zwei Mäuse", target="spanish")
```

The user input sent to the GPT is simply

```
"Eine Katze, ein Hund und zwei M\u00e4use", target="spanish"
```

And the GPT answer:

```
<ANSWER>
{"result": {"lang": "german", "translation": "Un gato, un perro y dos ratones"}}
</ANSWER>
```

Which is then parsed using a regex and python's json parser.

## Limitations

Ye be warned:

- Only people who have an OpenAI API key will be able to use these functions.
- GPTs have a token size limit so these functions will fail if your inputs or outputs are too large (long lists, etc.)
- GPT answers can be changing and unreliable.
- Calls to OpenAI-powered functions generally have a ~0.5-1 second of overhead then get slower as the input and output increase in size. So pure-python solutions will often beat GPT-based solutions. Sometimes it's better to just ask ChatGPT for python code and run the python code.

## A future with GPT-powered functions?

GPTs are not yet fast and cheap enough to be used anywhere, but when they are it will transform a lot of how we write code (assuming we still code).

For instance instead of having developers write zillions of messages to help users troubleshoot errors, we'll use a function like this:

```python
@gpt_function(think_through=True)
def help_troubleshoot(error_traceback: str) -> str:
    """Return a short analysis of the Python error from the provided traceback.
    
    Example
    ------ 
    >>> help_troubleshoot("some\ntraceback")
    "This error generally happens (...). Maybe the variable `x` is not set (...)"
    """
```

With this we can write a function that queries webpages and looks into the issue if need be:

```python
import requests
import traceback


def query_webpages_and_help_troubleshoot(url):
    try:
        requests.get(url)
    except Exception as error:
        troubleshooting = help_troubleshoot(traceback.format_exc())
        raise ValueError(troubleshooting) from error
```

And now we can run it into a wall:

```python
query_webpages_and_help_troubleshoot("https://wykipedia.com")

# Raises:
"""
< traceback with ConnectionError, MaxRetryError, etc... />

ValueError: The error indicates a failure to resolve the hostname
`wykipedia.com`. This generally means that the domain name is either
incorrect or does not exist. A common typo might be confusing it with
the correct URL `wikipedia.com`. Please verify the URL and try again.
"""
```


## Development

To contribute to this library, first checkout the code.

Then create a new virtual environment:

```bash
cd gpt-function-decorator
python -m venv venv
source venv/bin/activate
```
Now install the dependencies and test dependencies:
```bash
pip install -e '.[test]'
```
To run the tests:
```bash
pytest
```

## Contribute!

This open-source project is hosted on Github under the Apache 2.0 license. Everyone is welcome to contribute!

## Thanks

Thanks to Simon Willison for his [python library project template](https://github.com/simonw/python-lib).