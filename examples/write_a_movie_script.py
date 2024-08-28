"""Let's write a movie script!

Well' start from a subject, like "a detective is on the hunt for a lost cat.".
- First the GPT will invent a plot, a synopsis, and a title for the movie.
- Then it will flesh out a couple of characters, their background, personality...
- Next, using the plot and the characters, it will outline the acts of the movie.
- For each act, it will decompose it into scenes (this runs in parallel via async
  functions) and then it writes each scene's script (also async in parallel).
- Finally, it will generate an HTML file with the full movie script.

The whole process takes under 2 minutes and costs around 5c of OpenAI at the
time of writing. 
"""

import asyncio
from pydantic import BaseModel, Field
from gpt_function_decorator import gpt_function, Reasoned


try:
    import jinja2
except ImportError:
    print("This example requires jinja2, install it with `pip install jinja2`")


class MovieOutline(BaseModel):
    "A movie outline"
    plot: str
    synopsis: str
    title: str

    @staticmethod
    @gpt_function
    def from_subject(subject) -> Reasoned[MovieOutline]:
        """Write a plot for a short movie based on the given subject,
        then write a catchy synopsis and find a great movie title to go with it."""


class Character(BaseModel):
    name: str
    background: str
    personality: str
    physical_appearance: str
    relationship_to_other_characters: str
    character_arc_in_the_movie: str

    @staticmethod
    @gpt_function
    def list_from_plot(n: int, plot: str) -> Reasoned[list[Character]]:
        """Flesh out {n} main characters for the given plot. Be concise."""


class ActOutline(BaseModel):
    title: str
    summary: str
    character_names: list[str]

    @gpt_function
    def list_from_plot(
        n: int, plot: str, characters: list[Character]
    ) -> Reasoned[list["ActOutline"]]:
        """Come up with {n} acts for the movie, with for each a title and a summary
        explaining which characters are involved (use full names) and what they do."""


### Act scene outlines


class SceneOutline(BaseModel):
    title: str
    summary: str
    character_names: list[str]


@gpt_function
def write_act_scenes_outline(
    act_outline: ActOutline,
    full_story_plot: str,
    background_on_characters: list[Character],
) -> Reasoned[list[SceneOutline]]:
    """Decompose the act into scenes, and for each scene provide a summary.
    The summary should use characters (with their full name) mentioned in the
    act outline, and from the provided list.
    Each outline should explain what the characters do.
    For context we also provide background full story plot and the characters."""


### Act text


@gpt_function
async def write_scene_text(
    scene_outline: SceneOutline,
    act_outline: ActOutline,
    background_on_characters: list[Character],
) -> Reasoned[str]:
    """Write the movie script for the scene.
    Follow the provided scene outline. The full act outline is also provided
    but only for context.

    When writing about the characters, refer to their physical appearance
    or personality traits, as provided.

    Use HTML for any formatting such as italics, bold text, but do not
    include any CSS styles, nor title, nor sections, nor paragraphs.
    """


class Scene(BaseModel):
    outline: SceneOutline
    text: str


class Act(BaseModel):
    outline: ActOutline
    scenes: list[Scene]


async def write_act(
    act_outline: ActOutline,
    plot: str,
    characters: list[Character],
    gpt_system_prompt: str,
    async_semaphore: asyncio.Semaphore,
) -> list[Act]:
    scene_outlines = write_act_scenes_outline(
        act_outline.summary,
        full_story_plot=plot,
        background_on_characters=characters,
        gpt_system_prompt=gpt_system_prompt,
    )
    scene_text_futures = [
        write_scene_text(
            scene_outline=scene_outline.summary,
            act_outline=act_outline.summary,
            background_on_characters=[
                c for c in characters if c.name in scene_outline.character_names
            ],
            gpt_system_prompt=gpt_system_prompt,
            semaphore=async_semaphore,
        )
        for scene_outline in scene_outlines
    ]
    scene_texts = [e for e in await asyncio.gather(*scene_text_futures)]

    scenes = [
        Scene(outline=outline, text=text)
        for (outline, text) in zip(scene_outlines, scene_texts)
    ]
    return Act(outline=act_outline, scenes=scenes)


class Movie(BaseModel):
    outline: MovieOutline
    characters: list[Character]
    acts: list[Act]

    def html(self) -> str:
        template = """
        <link rel="stylesheet" href="https://cdn.simplecss.org/simple.min.css">
        <h1>{{ movie.outline.title }}</h1>
        <p><i>{{movie.outline.synopsis }}</i></p>
        <h2>Characters</h2>
        {% for char in movie.characters %}
          <p><b>{{ char.name }}</b></p>
          <ul>
            <li>{{ char.background }}</li>
            <li>{{ char.personality }}</li>
            <li>{{ char.physical_appearance }}</li>
            <li>{{ char.relationship_to_other_characters }}</li>
            <li>{{ char.character_arc_in_the_movie }}</li>
          </ul>
        {% endfor %}

        <h2>Outline</h2>
        {% for act in movie.acts %}
          <p><b>{{ act.outline.title }}</b></p>
          <ul>
            {% for scene in act.scenes %}
                <li>{{ scene.outline.summary }}</li>
            {% endfor %}
          </ul>
        {% endfor %}
            
        <h2>Script</h2>
        {% for act in movie.acts %}
          <h3>{{ act.title }}</h3>
            {% for scene in act.scenes %}
              <span style="white-space: pre-wrap; font-family: monospace;">
                {{ scene.text }}
              </span>
            {% endfor %}
        {% endfor %}
        """
        return jinja2.Template(template).render(movie=self)


async def write_a_movie(
    subject: str = None,
    n_characters: int = 5,
    n_acts: int = 6,
    system_prompt: str = None,
) -> Movie:

    kwargs = {"gpt_system_prompt": system_prompt}
    outline = MovieOutline.from_subject(subject=subject, gpt_model="gpt-4o", **kwargs)
    print("Title:", outline.title)
    print("Synopsis:", outline.synopsis)
    print("\nWriting that story...")
    characters = Character.list_from_plot(
        n=n_characters, plot=outline.plot, gpt_model="gpt-4o", **kwargs
    )
    act_outlines = ActOutline.list_from_plot(
        n_acts, outline.plot, characters, gpt_model="gpt-4o", **kwargs
    )

    async_semaphore = asyncio.Semaphore(10)

    act_futures = [
        write_act(
            act_outline=act_outline,
            plot=outline.plot,
            characters=[c for c in characters if c.name in act_outline.character_names],
            async_semaphore=async_semaphore,
            **kwargs,
        )
        for act_outline in act_outlines
    ]
    acts = await asyncio.gather(*act_futures)

    print("All done!")
    return Movie(acts=acts, outline=outline, characters=characters)


async def main():
    subject = """
    A biotech engineer is working in her lab at the top floor of a 10-story
    company building, when an experiment turned wrong causes a zombie outbreak
    on the first floor. She will have to make it out of the building alive.
    """
    system_prompt = """
    You are a brilliant screenwriter, your stories are full of action, suspense,
    and witty dialogue."""

    movie = await write_a_movie(
        subject=subject,
        n_characters=4,
        n_acts=3,
        system_prompt=system_prompt,
    )
    with open("movie_script.html", "w") as f:
        f.write(movie.html())


if __name__ == "__main__":
    asyncio.run(main())
