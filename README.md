# gpt-function-decorator

[![PyPI](https://img.shields.io/pypi/v/gpt-function-decorator.svg)](https://pypi.org/project/gpt-function-decorator/)
[![Tests](https://github.com/zulko/gpt-function-decorator/actions/workflows/test.yml/badge.svg)](https://github.com/zulko/gpt-function-decorator/actions/workflows/test.yml)
[![Changelog](https://img.shields.io/github/v/release/zulko/gpt-function-decorator?include_prereleases&label=changelog)](https://github.com/zulko/gpt-function-decorator/releases)
[![License](https://img.shields.io/badge/license-Apache%202.0-blue.svg)](https://github.com/zulko/gpt-function-decorator/blob/main/LICENSE)

This library provides a  lets you write functions that will be "run" by a GPT (right, now, only OpenAI models). The GPT simply looks at the function (parameters definition and docstring) and imagines what it returns for some given inputs. 

```python
from gpt_function_decorator import gpt_function

@gpt_function
def synonym(word, style):
    """Return a synonym of the word in the given language style"""

synonym("man", style="slang") # returns "dude"

synonym("man", style="formal") # returns "gentleman"

synonym("man", style="academic") # returns "individual"
```

Yes GPTs are unreliable, their answer can be different every time, and no you might not want to use this in production at a large bank. But this is fun and leveraging GPTs can replace hundreds of lines of code and save you hours of scripting.

## Installation

Install this library using `pip`:
```bash
pip install gpt-function-decorator
```

## Usage

### Setting up an OpenAI API key

This package requires an OpenAI API key. To get one you need to open an account, add credits to your account (2$ should last you a long time), generate an API key, and store it into an environment variable `OPENAI_API_KEY` (see [the OpenAI docs](https://platform.openai.com/docs/quickstart)).

The key will then be automatically detected by `gpt_function`. If you or your users ever need to juggle OpenAI clients with different API keys, projects, etc. you can override gpt_function's OpenAI client at any point of the execution with the following:

```
import gpt_function
import openai

...

gpt_function.SETTINGS["openai_client"] = OpenAI(api_key="...", project="...")
```

#### Basic usage:

In its most basic form, just import the decorator, and apply it to a function with a docstring:

```python
from gpt_function_decorator import gpt_function

@gpt_function
def fibonacci(n):
    """Return the n first fibonacci numbers"""

fibonacci(10)

# Returns:
[0, 1, 1, 2, 3, 5, 8, 13, 21, 34]
```

Just like any python function, GPT functions can have multiple arguments and keyword arguments.

```python
@gpt_function
def find_words_in_text(text, categories, max_words=10):
    """Return at most max_words of the text from the provided categories"""

text = "The dog in the house ate an apple and a pear from the fridge"
find_words_in_text(text, categories=["animal", "food"])

# Returns:
['dog', 'apple', 'pear']
```

#### Controlling the output format

The inputs and outputs can be any usual format, str, list, dict, number. Think "anything that can be represented through JSON".

The basic way to control the output is to describe it. You can go with a very minimal description and let the GPT decide on the details:

```python
@gpt_function
def country_metadata(country):
    """Return the capital city, language, and calling code of each country"""

country_metadata(["France", "Japan", "Peru"])

# returns
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

country_metadata(["France", "Japan", "Peru"])

# Returns
[{'name': 'France', 'capital': 'Paris', 'lang': 'French', 'code': '+33'},
 {'name': 'Japan', 'capital': 'Tokyo', 'lang': 'Japanese', 'code': '+81'},
 {'name': 'Peru', 'capital': 'Lima', 'lang': 'Spanish', 'code': '+51'}]
```

#### Selecting the GPT model

By default, `gpt_function` uses `gpt-4o-mini` under the hood, which is 10 times cheaper than `gpt-4o`, much faster and just almost as good (although `gpt-4o` knows more, makes less mistakes, and sometimes cracks better jokes).

You can change the GPT model used via the `gpt_model` argument:

```python
@gpt_function(gpt_model="gpt-4o")
def list_life_events(person):
    """Return a list of the person's life events (year, city, long_summary).
    Give as many details as possible in the long summary."""

list_life_events("Mozart")

# Returns
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


#### Asking python to "think through" an answer

By default, `gpt_function` tells the GPT *"answer directly without any explanations"*.
When setting `@gpt_function(think_through=True)`, however, it will tell the GPT *"Think carefully through the answer and if the function docstring suggests steps, take these steps"*. This is a mechanism that makes the answer slower and more expensive, but also much higher quality as it enables the GPTs to reason about tasks.

For instance consider this task:

```python
@gpt_function
def could_have_met(person, celebrities):
    """Return the celebrities in the list that the person could have met,
    considering their birth and death dates"""

celebrities = ["Napoleon", "Jefferson", "Julius Cesar", "Lady Gaga", "Beethoven"]
could_have_met("Chopin", celebrities)

# Result
['Beethoven']
```

Hmmm that's not very complete. To be fair, the answer can change when you ask many times, but it's generally wrong.
One reason it's wrong is because the GPT doesn't take time to think through the information it knows.

Now let's ask for a thoughtful answer:


```python
@gpt_function(think_through=True)
def could_have_met_thoughtful_version(person, celebrities):
    """Return the celebrities in the list that the person could have met,
    considering their birth and death dates"""


could_have_met_thoughtful_version("Chopin", celebrities)

# Result
['Napoleon', 'Jefferson', 'Beethoven']

```

It did it! Here again, if you ask many times you will have wrong answers, but the probability of success is much higher.
You can see the thinking happening by adding `debug=True` to the function call, which returns the full answer from the GPT:

```python
could_have_met_thoughtful_version("Chopin", celebrities, debug=True)

# prints
"""
RESPONSE:
---------

To evaluate the function `could_have_met` with the input provided, we need to
consider the birth and death dates of Frédéric Chopin and the celebrities
listed.

1. **Frédéric Chopin's Lifespan**:
   - Born: March 1, 1810
   - Died: October 17, 1849

2. **Celebrities and Their Lifespans**:
   - **Napoleon Bonaparte**: Born August 15, 1769, died May 5, 1821
   - **Thomas Jefferson**: Born April 13, 1743, died July 4, 1826
   - **Julius Caesar**: Born July 12, 100 BC, died March 15, 44 BC (obviously
long before Chopin)
   - **Lady Gaga**: Born March 28, 1986 (after Chopin's death)
   - **Ludwig van Beethoven**: Born December 17, 1770, died March 26, 1827

3. **Determine Who Chopin Could Have Met**:
   - **Napoleon**: Lived during Chopin's lifetime.
   - **Thomas Jefferson**: Also lived during Chopin's lifetime.
   - **Julius Caesar**: Lived long before Chopin and could not have met him.
   - **Lady Gaga**: Born after Chopin's death and could not have met him.
   - **Ludwig van Beethoven**: Lived during Chopin's lifetime but died two years
before Chopin.

Given this analysis, the people that Chopin could have met are:
- Napoleon
- Thomas Jefferson
- Ludwig van Beethoven
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

shopping_list_for_national_day_food("Italy", debug=True)

# Response
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
""", debug=True)


# Response

"""
In 1806, a 15-year-old Carl Czerny probably had bigger worries than what to
wear to prom — he was chosen by Beethoven himself to premiere the Piano
Concerto No. 1 in Vienna, Austria. Imagine the pressure! And this was before
TikTok fame, so Carl had to rely on pure talent.
"""
```

(yes, there's probably funnier jokes to crack, but you can't expect much from a
chatbot going by a spec sheet. ChatGPT can actually be pretty funny if you let
it riff freely)


## Limitations

Ye be warned:
- Only people who have an OpenAI API key will be able to use these functions.
- GPT answers can be changing and unreliable.
- GPTs have a token size limit so these functions will fail if your inputs or outputs are too large (long lists, etc.)


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

Thanks to Simon Wilkes for his [python library project template](https://github.com/simonw/python-lib).