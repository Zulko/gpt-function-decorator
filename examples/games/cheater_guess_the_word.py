"""This is a variation of the "guess the word" game, where the computer cheats
by changing the secret word if the user gets too close to it, until it cannot
change it anymore because of the constraints of previous questions/answers.
"""

from gpt_function_decorator import gpt_function, ReasonedAnswer
from pydantic import BaseModel


class RandomWordSelection(BaseModel):
    selected_word: str
    could_find_a_word: bool


@gpt_function
def select_random_word(statements=None) -> ReasonedAnswer(RandomWordSelection):
    """Pick a random word for which all of these apply: {statements}.
    If you can't find a word, just state so."""


class InputEvaluation(BaseModel):
    answer_to_user_is_yes: bool
    user_guessed_the_secret_word: bool
    user_asked_to_quit: bool
    user_is_close_to_finding_the_secret_word: bool


@gpt_function
def evaluate_guess(text: str, secret_word: str) -> ReasonedAnswer(InputEvaluation):
    """In trying to guess secret word "{secret_word}", the user said "{text}".

    Evaluate this input:
    - If the user asked a question or made a statement about the secret word, is
      the answer yes or no?
    - Does the user statement or question indicate they guessed the secret word?
    - Does the user want to quit the game?
    - Is the user close to finding the secret word?
    """


def play_cheater_guess_the_word(subject):
    print(
        f"Welcome! You have 50 turns to guess a {subject}. Each turn, you can "
        "ask a question about the word, guess the word, or ask to quit. I WILL "
        "cheat and try to change the word if you get too close to it, until I "
        "get cornered."
    )
    previous_answers = [f"Is it a {subject}? Yes."]
    selection = select_random_word(statements=previous_answers).result
    secret_word = selection.selected_word
    logs = f"Secret word: {secret_word}\n"

    for turns_left in range(50, 0, -1):
        user_input = input(f"\nGuess the word ({turns_left} turns left): ")
        logs += f"INPUT: {user_input}\n"
        evaluation = evaluate_guess(text=user_input, secret_word=secret_word).result
        if (
            evaluation.user_guessed_the_secret_word
            or evaluation.user_is_close_to_finding_the_secret_word
        ):
            selection = select_random_word(
                statements=previous_answers,
                avoid_words=[secret_word, user_input],
            ).result
            if selection.could_find_a_word and (secret_word != selection.selected_word):
                secret_word = selection.selected_word
                logs += f"Changed the secret word to {secret_word}.\n"
                evaluation = evaluate_guess(
                    text=user_input,
                    secret_word=secret_word,
                ).result
            elif evaluation.user_guessed_the_secret_word:
                print("Congratulations, you won!", f"It was indeed {secret_word}")
                break
        if evaluation.user_asked_to_quit:
            print("Quitter! The word was", secret_word)
            break
        else:
            answer = "Yes" if evaluation.answer_to_user_is_yes else "No"
            previous_answers.append(f"{user_input}? {answer}")
            logs += f"A: {answer}\n"
            print(answer)
        print(logs)
    print(f"\nGame over!", "Logs:")
    print(logs)


if __name__ == "__main__":
    play_cheater_guess_the_word(subject="fruit")
