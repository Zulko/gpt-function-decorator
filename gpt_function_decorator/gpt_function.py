from functools import wraps, lru_cache
import inspect
import re
import json
import textwrap

from openai import OpenAI

# This is a global variable that will store the OpenAI client. This
# enables any user to set the client  under their own terms (key, project...)
# via `gpt_function.SETTINGS["openai_client"] = OpenAI()`.
# If the user doesn't set up the client, it gets set up automatically with
# OpenAI() the first time a client is needed
SETTINGS = {"openai_client": None}


# This is the universal template we'll use. Look how simple it is!
# It mostly works because ChatGPT is great at understanding Python functions.
system_prompt_template = """
For the following python function, evaluate the user-provided input.

```python
{code}
```

{thinking}
Provide the final output at the end as follows,
where FUNCTION_OUTPUT is in JSON format:

<ANSWER>
{{"result": FUNCTION_OUTPUT}}
</ANSWER>
"""

report_template = """
SYSTEM:
-------
{system_prompt}

INPUT:
------

{user_input}

RESPONSE:
---------

{response_content}
"""


def gpt_function(
    gpt_model: str = "gpt-4o-mini",
    think_through: bool = False,
    retries: int = 0,
    debug: bool = False,
):
    """

    Parameters
    ----------

    model: str
        Any OpenAI model, e.g. `gpt-4o`, `gpt-4o-mini`. `gpt-4o-mini` is faster,
        and 10 times less expensive, but the answers can be less good.

    think_through: bool
        If true, this will ask the GPT to go through the steps of its reasoning
        before giving an answer. It does greatly improve the final answer (this
        is the way GPTs work best) and it makes troubleshooting easier, but also
        results in longer and more expensive function calls.

    retries
        It might happen that the GPT, for some reason, produces an answer that
        python cannot parse. In that case retrying often solves the problem.
        Once the maximum number of retries is reached without success, a ValueError
        exception is raised with the content of the response.

    debug
        If True, the full answer from the GPT will be printed. This is practical
        to troubleshoot cases where GPT returns a "valid" answer which is not
        exactly what you expected, and you want to see its reasoning.
    """

    if hasattr(gpt_model, "__call__"):
        # Case where the user wrote @gpt_function without argument nor
        # parenthesis. In this case we understand that the first argument
        # is the function itself and that the user meant to use the decorator
        # with the default parameter values.
        func = gpt_model
        decorator = gpt_function("gpt-4o-mini")
        return decorator(func)

    def decorator(func):
        """A decorator that will run the user-defined function on a GPT"""

        @wraps(func)  # This preserves the docstring and other attributes
        def wrapper(*args, **kwargs):

            # This next block enables users of already-decorated functions to pass
            # extra arguments to the function relative to the GPT execution.
            # This is not the most elegant solution, but it works.

            _gpt_model = kwargs.pop("gpt_model", None) or gpt_model
            _think_through = kwargs.pop("think_through", None) or think_through
            _retries = kwargs.pop("retries", None) or retries
            _debug = kwargs.pop("debug", None) or debug

            # Build the system prompt: add the function's code (definition and
            # docstring) and the method of thinking ("think as you go" vs
            # write the result directly)

            code = inspect.getsource(func)
            if _think_through:
                thinking = (
                    "Think carefully through the answer. "
                    "If the function docstring suggests steps, take these steps"
                )
            else:
                thinking = (
                    "Write the result directly without providing any explanation."
                )
            system_prompt = system_prompt_template.format(code=code, thinking=thinking)

            # Generate the user input. For instance, if the user ran
            # `func(1, 2, c=3)`, this will generate the string "1, 2, c=3"
            args_str = ", ".join(map(str, args))
            kwargs_str = ", ".join([f"{str(k)}={str(v)}" for (k, v) in kwargs.items()])
            user_input = ", ".join([args_str, kwargs_str])

            gpt_messages = [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_input},
            ]

            client = SETTINGS["openai_client"]
            if client is None:
                client = SETTINGS["openai_client"] = OpenAI()
            for retry in range(1 + _retries):
                response = client.chat.completions.create(
                    messages=gpt_messages, model=_gpt_model
                )
                response_content = response.choices[0].message.content

                full_report = report_template.format(
                    system_prompt=system_prompt,
                    user_input=user_input,
                    response_content=response_content,
                )
                lines = full_report.splitlines()
                wrapped_lines = [textwrap.fill(line, width=80) for line in lines]
                full_report = "\n".join(wrapped_lines)

                if _debug:
                    # print a report with the prompt system, user system and response

                    print(full_report)
                try:
                    answer_pattern = "<ANSWER>(.*)</ANSWER>"
                    matches = re.findall(answer_pattern, response_content, re.DOTALL)
                    answer = matches[0]
                    return json.loads(answer)["result"]
                except Exception as e:
                    if retry == retries:
                        raise ValueError(f"GPT transaction: {full_report}") from e

        # Add a text to the docstring so it will be clear to users that the
        # function is actually running on a chatbot.
        wrapper.__doc__ += """

            Function auto-generated by @gpt_function.
            - The execution happens on a chatbot, and may require an API key.
            - The quality and validity are not guaranteed.
            - You can add the following named arguments to this function:
              gpt_model, think_through, retries, debug. (see gpt_function docs)
        """
        return wrapper

    return decorator
