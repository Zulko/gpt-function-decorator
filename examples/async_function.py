from gpt_function_decorator import gpt_function
import asyncio


@gpt_function
async def write_story(subject: str) -> str:
    """Tell a short one-paragraph story (100-word max) about {subject}"""


async def print_stories(subjects: list[str]):
    """Print stories generated asynchronously (in "parallel") from the subjects"""
    stories = [write_story(subject) for subject in subjects]
    for story in asyncio.as_completed(stories):
        print(await story + 2 * "\n")


if __name__ == "__main__":
    subjects = ["dogs and cats", "the perils of AI", "the dove queen"]
    asyncio.run(print_stories(subjects))
