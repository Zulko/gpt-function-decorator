"""In this example, we create a role-playing game where the player makes decisions
that affect the story. The game has a "state" (the character's health and inventory)
that is carried over from one turn to the next, and updated after each turn.
"""

from gpt_function_decorator import gpt_function
from pydantic import BaseModel, Field


class Character(BaseModel):
    name: str
    profession: str
    personality: str
    physical_appearance: str
    ultimate_goal: str = Field(description="What the character aims to achieve in life")


class Status(BaseModel):
    condition: str = Field(
        description="Whether the character is injured, sick, tired, stressed, etc."
    )
    inventory: list[str] = Field(
        description="Any item, money, etc. the character possesses."
    )


class Setup(BaseModel):
    character: Character = Field(description="Description of the hero")
    status: Status
    narration: str = Field(
        description="Introduction to the story, up until the hero's first decision. "
        "Present tense, second person ('You do this, this happens, etc.')."
    )

    @staticmethod
    @gpt_function
    def from_subject(subject: str) -> "Setup":
        """Set up a role-playing-game story about {subject}."""


class Update(BaseModel):
    narration: str = Field(
        description="short 100-words narration of events unfolding from the hero's "
        "decision, using present tense and second person ('You do this, this happens, "
        "etc.'). Only if the hero dies, or reaches their ultimate goal, should the "
        "narration end with 'The end.'"
    )
    new_status: Status = Field(description="The hero's updated status")

    @staticmethod
    @gpt_function
    def from_decision(hero_decision, previous_action, hero, status) -> "Update":
        """Update the story based on the previous action and the hero's decision,
        taking into account the hero's status"""


@gpt_function
def summarize_narration(narration: str) -> str:
    """Summarize the narration in a maximum of 300 words. Keep the narration in
    present tense and second person ('You do this, this happens, etc.')."""


def play(subject):
    """Start a story then iterate through turns where the player makes decisions."""

    setup = Setup.from_subject(subject)
    print(f"\n\n{setup.narration}\n")

    while True:
        print(f"Goal: {setup.character.ultimate_goal}")
        print(f"Status: {setup.status.condition}")
        print(f"Inventory: {', '.join(setup.status.inventory)}")

        user_decision = input("\nWhat do you do next? ")
        update = Update.from_decision(
            hero_decision=user_decision,
            previous_action=setup.narration,
            hero=setup.character,
            status=setup.status,
        )
        print(f"\n\n{update.narration}\n")

        if "The end." in update.narration:
            break
        setup.narration += "\n\n" + update.narration
        if len(setup.narration) > 5000:
            print("Compressing the context, please be patient...")
            setup.narration = summarize_narration(setup.narration)

        setup.status = update.new_status


if __name__ == "__main__":
    play(subject="a very shy princess who wants to become a pirate")
