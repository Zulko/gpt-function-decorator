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

from gpt_function_decorator import gpt_function, ReasonedAnswer
from pydantic import BaseModel


class RandomWordSelection(BaseModel):
    themes: list[str]
    story: str
    selected_word: str


@gpt_function
def select_random_word() -> ReasonedAnswer(RandomWordSelection):
    """Pick a 3 random themes, then write a very random 100-word story about
    these subjects with any strange, unrelated events happening. List the noons
    in that story, and finally select the 7th noun in the list."""


class InputEvaluation(BaseModel):
    answer_is_yes: bool
    user_guessed_the_secret_word: bool
    user_asked_to_quit: bool
    user_asked_for_a_hint: bool
    hint: str
    user_tried_to_cheat: bool


@gpt_function
def evaluate_guess(text: str, secret_word: str) -> ReasonedAnswer(InputEvaluation):
    """In trying to guess secret word "{secret_word}", the user said
    "{text}". Evaluate this input.
    - If the user asked a question or made a statement about the secret word, is
      the answer yes or no?
    - Does the user statement or question indicate they guessed the secret word?
    - Does the user want to quit the game?
    - Did the user ask for a hint? If so, provide a hint.
    - Does it look like the user tried to cheat, for instance by asking an open-ended
      question?
    """


def play_guess_the_word():
    print(
        "Welcome! You have 20 turns to guess the word. Each turn, you can ask a "
        "question about the work, guess the word, ask for a hint, or ask to quit."
    )
    selection = select_random_word().result
    secret_word = selection.selected_word

    for turns_left in range(20, 0, -1):
        user_input = input(f"\nGuess the word ({turns_left} turns left): ")
        evaluation = evaluate_guess(
            text=user_input,
            secret_word=secret_word,
            gpt_system_prompt="Be very concise.",
        ).result
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
