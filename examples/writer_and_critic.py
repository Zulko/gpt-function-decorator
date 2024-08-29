"""In this attempt to generate a great story through iterative improvement.
We have two functions, a "writer" and a "reviewer". The writer writes a story
about a subject, then the reviewer points at possible improvements it, and the
writer improves the story basedvon the review. This process repeats twice, and
the final story is printed."""

from gpt_function_decorator import gpt_function


@gpt_function
def write_a_story(subject) -> str:
    """Write the best possible story about {subject} in under 200 words."""


@gpt_function
def review(story: str) -> str:
    """Poke holes at the story and suggest specific ways to make it better."""


@gpt_function(reasoning=True)
def improve_story(subject, story, review) -> str:
    """Use the review to improve the story about {subject}"""


if __name__ == "__main__":
    subject = "a crossover between Titanic and Batman"
    story = write_a_story(subject)
    for _ in range(2):
        print(f"\n\n\nStory:\n\n{story}")
        opinion = review(story)
        print(f"\n\n\nReview:\n\n{opinion}")
        story = improve_story(subject, story, opinion)
    print(f"\n\n\nFinal story:\n\n{story}")
