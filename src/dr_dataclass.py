import re
from dataclasses import dataclass


@dataclass
class EnZhText:
    """Stores text and can extract both English alphabet and Chinese characters"""

    text: str

    def __init__(self, text: str):
        self.text = text.strip()

    def extract_en(self):
        """Regex that captures alphabet, numbers and basic punctuation .,!?"""
        return " ".join(re.findall(r"[a-zA-Z0-9.,!?]+", self.text))

    def extract_zh(self):
        """
        Note: This is quite crude and only extracts purely
        chinese characters.
        """
        return "".join(re.findall(r"[\u4e00-\u9fff]", self.text))


@dataclass
class Qualification:
    """Class to store qualification of medical practitioner"""

    nature: EnZhText | None  # nature of the qualification
    tag: str | None
    year: int

    def __init__(self, nature_tag: str, year: str):
        """Parse qualification item to class.
        We separate the tag from nature_tag, which is the string inside
        the brackets, and remove the brackets from nature_tag to get nature.
        Args:
            - nature_tag (str): Eg. MB BS (Lond)
            - year (str): year of study
        """
        self.nature = EnZhText(re.sub(r"\[[^]]*\]|\([^)]*\)", "", nature_tag))

        tag = re.findall(r"\[[^]]*\]|\([^)]*\)", nature_tag)
        tag = [match.strip("()") for match in tag]
        self.tag = tag[0] if tag else None

        self.year = int(year)


@dataclass
class Practitioner:
    """Class to store practitioner information, and parse from __init__"""

    registration_no: str
    name: EnZhText
    address: EnZhText
    qualifications: list[Qualification]
