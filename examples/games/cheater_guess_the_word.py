"""This is a variation of the "guess the word" game, where the computer cheats
by changing the secret word if the user guesses it, until it cannot change it
anymore without contradicting previous questions/answers.
"""

from gpt_function_decorator import gpt_function
from pydantic import BaseModel, Field


class RandomWordSelection(BaseModel):
    selected_word: str
    could_find_a_word: bool


@gpt_function(reasoning=True)
def select_random_word(avoided_words=None, answers=None) -> RandomWordSelection:
    """If it is possible, pick a word not in {avoided_words} for which you  ALL
    of these answers are strictly true: {answers}. If not possible, set
    could_find_a_word=False"""


class InputEvaluation(BaseModel):
    answer_is_yes: bool = Field(
        description="If the user asked a question or made a statement about the "
        "secret word, is the answer to that question yes or no?"
    )
    user_guessed_the_secret_word: bool = Field(
        description="From the user input, does it look like the user guessed the "
        "secret word?"
    )
    user_asked_to_quit: bool = Field(description="Does the user want to quit?")

    @gpt_function(reasoning=True)
    def from_guess(text: str, secret_word: str) -> "InputEvaluation":
        """In trying to guess secret word "{secret_word}", the user said "{text}".
        Evaluate this input
        """


def play_cheater_guess_the_word(subject):
    print(
        f"Welcome! You have 50 turns to guess a {subject}. Each turn, you can "
        "ask a question about the word, guess the word, or ask to quit. I WILL "
        "cheat and try to change the word to avoid losing, until I get cornered."
    )
    previous_answers = [f"Is it a {subject}? Yes."]
    selection = select_random_word(answers=previous_answers)
    secret_word = selection.selected_word
    logs = f"Secret word: {secret_word}\n"

    for turns_left in range(50, 0, -1):
        user_input = input(f"\nGuess the word ({turns_left} turns left): ")
        logs += f"INPUT: {user_input}\n"
        evaluation = InputEvaluation.from_guess(user_input, secret_word=secret_word)
        evaluation = evaluation
        if evaluation.user_guessed_the_secret_word:
            # The user is about to win! We'll try changing the secret word.
            selection = select_random_word(
                answers=previous_answers,
                avoided_words=[secret_word],
                gpt_model="gpt-4o",
            )
            if selection.could_find_a_word and (secret_word != selection.selected_word):
                secret_word = selection.selected_word
                logs += f"Changed the secret word to {secret_word}.\n"
                evaluation = evaluate_guess(
                    text=user_input,
                    secret_word=secret_word,
                )
            elif evaluation.user_guessed_the_secret_word:
                print("Congratulations, you won!", f"It was indeed {secret_word}")
                break
        if evaluation.user_asked_to_quit:
            print("Quitter! The word was", secret_word)
            break
        else:
            answer = "Yes" if evaluation.answer_is_yes else "No"
            previous_answers.append(f"{user_input}? {answer}")
            logs += f"A: {answer}\n"
            print(answer)
    print(f"\nGame over!", "Logs:")
    print(logs)


if __name__ == "__main__":
    play_cheater_guess_the_word(subject="european country")
