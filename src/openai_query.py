# Note: The openai-python library support for Azure OpenAI is in preview.
import os
import re

import openai
from dotenv import load_dotenv
from openai.openai_object import OpenAIObject

# load environment variables
load_dotenv()

openai.api_type = os.getenv("OPENAI_API_TYPE")
openai.api_base = os.getenv("OPENAI_API_BASE")
openai.api_version = os.getenv("OPENAI_API_VERSION")
openai.api_key = os.getenv("OPENAI_API_KEY")


MEDICAL_PROMPT = (
    "Suggest medical specialists for a patient to see based on "
    "their described symptoms in the format of {{specialist 1}},"
    " {{specialist 2}}, ..., {{specialist n}}.\nPatient:"
)


def parse_response(response: OpenAIObject) -> str:
    """Parse the response from OpenAI's API.

    Args:
        response (OpenAIObject): The response object from OpenAI's API.

    Returns:
        str: The text of the first choice in the response, or None if there are no choices.
    """
    choices = response["choices"]
    if not choices:
        return None
    choice = choices[0]
    return choice["text"]


def strip_string(string):
    """Strip newlines from the start and end of a string."""
    if string[0] == "\n":
        return strip_string(string[1:])
    elif string[-1] == "\n":
        return strip_string(string[:-1])
    else:
        return string


def call_openai(prompt: str) -> str:
    """Summarise the text using OpenAI's API."""
    response = openai.Completion.create(
        engine="text-davinci-003",
        prompt=prompt,
        temperature=0,
        max_tokens=4000,
        top_p=0.5,
        frequency_penalty=0,
        presence_penalty=0,
        best_of=3,
        stop=None,
    )
    return strip_string(parse_response(response))


if __name__ == "__main__":
    # create a prompt for the user to enter their medical problem
    medical_problem = input("Enter your medical problem: ")
    prompt = MEDICAL_PROMPT + medical_problem
    print(MEDICAL_PROMPT)

    # get the response from OpenAI's API
    response = call_openai(prompt)
    response = strip_string(response)
    print(response)

    # extract the specialist names from the response
    medical_specialists = values = re.findall(r"{{(.*?)}}", response)
    print(medical_specialists)
