import string
import json
import inspect
from textwrap import dedent
from typing import List, Optional, Set

import yaml
from pydantic import BaseModel


def generate_prompt(func, args, kwargs, requested_format):

    # Build a prompt by interpolating the docstring with the provided args:
    named_args = name_all_args_and_defaults(func, args, kwargs)
    prompt, unused_args = format_docstring(func.__doc__, named_args)

    # Any arg not used in the docstring will be added as JSON at the end:
    if unused_args:
        unused_args_yaml = get_args_as_yaml({k: named_args[k] for k in unused_args})
        prompt += f"\nUse these values (provided in YAML):\n{unused_args_yaml}"

    output_descriptions = get_output_type_descriptions(requested_format)
    if output_descriptions:
        prompt += (
            f"\n\nUse these output schema fields:\n{yaml.dump(output_descriptions)}"
        )

    return prompt


def name_all_args_and_defaults(func, args, kwargs):
    """Return a dict where all arguments (args and kwargs) are represented as
    {name: value}.

    This is used to ensure that when users pass args to GPT functions, these
    are represented with their name in the prompt (or used appropriately in the
    doctring template).
    """
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


def format_docstring(docstring, named_args):
    docstring = dedent_string(docstring)
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
    return prompt, unused_args


def dedent_string(string: str) -> str:
    first_line, *rest = string.split("\n")
    return "\n".join([dedent(first_line), dedent("\n".join(rest))])


def pydantic_aware_json_dumper(obj):
    """A JSON dumper that can handle Pydantic models."""
    if hasattr(obj, "dict"):  # Pydantic models
        return obj.dict()
    if hasattr(obj, "__json__"):
        return obj.__json__()
    if hasattr(obj, "toJSON"):
        return obj.toJSON()
    return obj.__dict__


def get_args_as_yaml(named_args):
    json_data = json.dumps(named_args, default=pydantic_aware_json_dumper)
    return yaml.dump(json.loads(json_data))


def find_nested_pydantic_models(
    some_type, found_models: Optional[Set[BaseModel]] = None
) -> Set[BaseModel]:
    """Return all the models found in the given type.

    For instance if you have a type House[dogs=List[Dog], name=str] the function
    called on list[House] will find {House, Dog}.
    """
    if found_models is None:
        found_models = set()

    if hasattr(some_type, "__origin__") and some_type.__origin__ in {list, List}:
        sub_type = some_type.__args__[0]
        if isinstance(sub_type, type) and issubclass(sub_type, BaseModel):
            if sub_type not in found_models:
                find_nested_pydantic_models(sub_type, found_models)

    elif isinstance(some_type, type) and issubclass(some_type, BaseModel):
        if some_type.__name__ not in ["ReasoningFormatWrapper", "PydanticWrapper"]:
            found_models.add(some_type)
        for field_name, field_type in some_type.__annotations__.items():
            if field_type not in found_models:
                find_nested_pydantic_models(field_type, found_models)

    return found_models


def get_output_type_descriptions(requested_format):
    """Return a list of descriptions for the types of the named arguments."""

    models_set = find_nested_pydantic_models(requested_format)

    def field_description(field_name, field):
        description = ""
        if hasattr(field, "description") and field.description:
            description += field.description
        if hasattr(field, "example") and field.example:
            description += f" Example: {field.example}"
        return field_name if not description else {field_name: description}

    def model_description(model):
        fields = [field_description(*item) for item in model.model_fields.items()]
        return [model.__doc__] if model.__doc__ else [] + fields

    models_and_fields = {
        model.__name__: model_description(model) for model in models_set
    }
    return models_and_fields
