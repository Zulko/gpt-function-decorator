"""This example demonstrates how to use the `gpt_function` decorator with
async functions. We define an async function `write_story` that generates a
short story about a given subject. We then run that story on three different
subjects asynchronously using `asyncio.as_completed`, so that OpenAI's API
generates the stories in parallel.
"""

from gpt_function_decorator import gpt_function
import asyncio


@gpt_function
async def write_story(subject: str) -> str:
    """Tell a short one-paragraph story (100-word max) about {subject}"""


async def print_stories(subjects: list[str]):
    """Print stories generated asynchronously (in "parallel") from the subjects"""
    stories = [write_story(subject) for subject in subjects]
    for story in asyncio.as_completed(stories):
        print((await story) + 2 * "\n")


if __name__ == "__main__":
    subjects = ["dogs and cats", "the perils of AI", "the dove queen"]
    asyncio.run(print_stories(subjects))
