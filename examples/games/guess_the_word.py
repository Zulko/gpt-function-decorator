"""Ask ChatGPT to select a random word and have the user guess it.

This example demonstrates how the GPT and structured outputs can be used to
triage user answers ("user asked for a hint", "user asked to quit",
"used tried to cheat", "user guessed the secret word", etc.).

The function `select_random_word` also demonstrates an effective way to randomness
out of the GPT for convoluted originality. If you simply ask "give me a random word",
you might get the same word (e.g. "apple") a lot of times. But if you ask the GPT to
write a 100-word story about random themes and then select a noun in that story,
you will get a more random word.
"""

from gpt_function_decorator import gpt_function
from pydantic import BaseModel, Field


class RandomWordSelection(BaseModel):
    themes: list[str]
    story: str
    selected_word: str

    @staticmethod
    @gpt_function
    def pick() -> "RandomWordSelection":
        """Pick a 3 random themes, then write a very random 100-word story about
        these subjects with any strange, unrelated events happening. List the noons
        in that story, and finally select the 7th noun in the list (make it singular
        if it's plural).
        """


class InputEvaluation(BaseModel):
    answer_is_yes: bool = Field(
        description="If the user asked a question or made a statement about "
        "the secret word, is the answer yes or no?"
    )
    user_guessed_the_secret_word: bool = Field(
        description="Does the user statement or question indicate they correctly "
        "guessed the secret word?"
    )
    user_asked_to_quit: bool = Field(description="Does the user want to quit the game?")
    user_asked_for_a_hint: bool = Field(description="Did the user ask for a hint?")
    hint: str = Field(description="Give the player a hint, if they asked for one.")
    user_tried_to_cheat: bool = Field(description="Did the user try to cheat?")

    @staticmethod
    @gpt_function(reasoning=True)
    def from_user_text(text: str, secret_word: str) -> "InputEvaluation":
        """In trying to guess secret word "{secret_word}", the user said
        "{text}". Evaluate this input.
        """


def play_guess_the_word():
    print(
        "Welcome! You have 20 turns to guess the word. Each turn, you can ask a "
        "question about the word, guess the word, ask for a hint, or ask to quit."
    )
    selection = RandomWordSelection.pick()
    secret_word = selection.selected_word

    for turns_left in range(20, 0, -1):
        user_input = input(f"\nGuess the word ({turns_left} turns left): ")
        evaluation = InputEvaluation.from_user_text(
            text=user_input, secret_word=secret_word
        )
        if evaluation.user_guessed_the_secret_word:
            print("Congratulations, you won!", f"It was indeed {secret_word}")
            break
        elif evaluation.user_asked_to_quit:
            print("Quitter! The word was", secret_word)
            break
        elif evaluation.user_asked_for_a_hint:
            print(evaluation.hint)
        elif evaluation.user_tried_to_cheat:
            print("Hmmm that would be cheating.")
        else:
            print("Yes!" if evaluation.answer_is_yes else "No.")

    print(
        f"\nGame over! For the record, '{secret_word}' was selected from this "
        f"story about randomly chosen the themes {', '.join(selection.themes)}:"
        f"\n{selection.story}"
    )


if __name__ == "__main__":
    play_guess_the_word()
