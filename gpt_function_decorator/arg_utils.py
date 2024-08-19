import string
import inspect
from functools import wraps
from textwrap import dedent


def add_kwargs(**new_kwargs):
    """Decorator to add keyword arguments to a function's signature."""

    def decorator(func):
        # Get the original function's signature
        sig = inspect.signature(func)
        params = list(sig.parameters.values())

        # Add new kwargs to the parameters
        parameter_type = inspect.Parameter.POSITIONAL_OR_KEYWORD
        keyword_only = inspect.Parameter.KEYWORD_ONLY
        if any([param.kind == keyword_only for param in params]):
            parameter_type = keyword_only

        new_params = [
            inspect.Parameter(name, parameter_type, default=value)
            for name, value in new_kwargs.items()
        ]

        # Update the function's signature
        params.extend(new_params)
        new_sig = sig.replace(parameters=params)

        @wraps(func)
        def wrapper(*args, **kwargs):
            # The new kwargs are already added to the signature, so they will
            # be available in kwargs when the function is called.
            kwargs = {**new_kwargs, **kwargs}
            return func(*args, **kwargs)

        # Update the signature of the wrapper function
        wrapper.__signature__ = new_sig

        return wrapper

    return decorator


def name_all_args_and_defaults(func, args, kwargs):
    args_names = [
        name
        for name, param in inspect.signature(func).parameters.items()
        if param.default == inspect.Parameter.empty
    ]
    named_args = dict(zip(args_names, args))

    all_named_args = {**named_args, **kwargs}

    unspecified_kwargs = {
        name: param.default
        for name, param in inspect.signature(func).parameters.items()
        if param.default != inspect.Parameter.empty and name not in all_named_args
    }
    return {**all_named_args, **unspecified_kwargs}


def generate_prompt_from_docstring(docstring, named_args):
    # Step 3: try applying to the docstring
    first_line, *rest = docstring.split("\n")
    docstring = "\n".join([dedent(first_line), dedent("\n".join(rest))])
    # This allows the user to define an interpolated string.
    try:
        prompt = docstring.format(**named_args)
        formatter = string.Formatter()
        used_args = {
            field_name
            for _, field_name, _, _ in formatter.parse(docstring)
            if field_name
        }
    except:
        prompt = docstring
        used_args = set()
    unused_args = set(named_args.keys()) - used_args
    unused_args_w_values = {k: named_args[k] for k in unused_args}
    if unused_args_w_values:
        prompt += f"\nUse these values, represented in JSON: {unused_args_w_values}"
    return prompt
