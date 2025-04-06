"""
parse contacts gathered via Google Form
"""

import os
from pathlib import Path
from logging import Logger, getLogger
from typing import Any

from freq_used.logging_utils import set_logging_basic_config
from freq_used.google.contacts.utils import get_label_str, is_home_email
from pandas import read_csv, DataFrame, Series

logger: Logger = getLogger()


def get_most_recent_file(directory: str) -> str | None:
    # List all files (not directories) in the given directory
    files: list[str] = [
        os.path.join(directory, file)
        for file in os.listdir(directory)
        if os.path.isfile(os.path.join(directory, file)) and not file.startswith(".")
    ]

    if not files:
        return None

    # Sort files by creation time (most recent first)
    most_recent_file = max(files, key=os.path.getctime)
    return most_recent_file


def convert_person_info_to_google_contact_dict(person: Series) -> dict[str, Any]:
    assert isinstance(person, Series), person.__class__

    name: str = person["한글 이름"]
    assert isinstance(name, str) and len(name) >= 2 and len(name) <= 3, (name, len(name))

    personal_email: str = person["개인 이메일"]
    assert isinstance(personal_email, str), (personal_email, personal_email.__class__)

    mobile_number: str = person["핸드폰 번호"]
    assert isinstance(mobile_number, str), (mobile_number, mobile_number.__class__)

    birthday: str | float = person["생일"]
    assert isinstance(birthday, (str, float)), (name, birthday, birthday.__class__)

    org: str | float = person["Company or Organization"]
    assert isinstance(org, (str, float)), (org, org.__class__)

    job_title: str | float = person["Job Title"]
    assert isinstance(job_title, (str, float)), (job_title, job_title.__class__)

    linkedin: str | float = person["LinkedIn URL"]
    assert isinstance(linkedin, (str, float))

    other_urls: str | float = person["그 외 websites - 개인 website, 회사 website 등등"]
    assert isinstance(other_urls, (str, float))

    class_number: str = person["6학년 반"]
    assert isinstance(class_number, str)

    gender: str = person["성별"]
    assert isinstance(gender, str) and gender in ["남", "여"]

    res: dict[str, Any] = dict()

    res["Last Name"] = name[0]
    res["First Name"] = name[1:]

    res["E-mail 1 - Label"] = "* Home" if is_home_email(personal_email) else "* Work"
    res["E-mail 1 - Value"] = personal_email

    res["Phone 1 - Label"] = "Mobile"
    res["Phone 1 - Value"] = convert_phone_number(mobile_number)
    # print(name, f'|{res["Phone 1 - Value"]}|')

    if isinstance(org, str):
        res["Organization Name"] = org

    if isinstance(job_title, str):
        res["Organization Title"] = job_title

    if isinstance(birthday, str):
        res["Birthday"] = get_proper_birthday_str(birthday)
        # print(res["Birthday"])

    if isinstance(linkedin, str) or isinstance(other_urls, str):
        urls: list[str] = list()
        if isinstance(linkedin, str):
            urls.append(linkedin)

        if isinstance(other_urls, str):
            for url in other_urls.split(","):
                urls.append(url.strip())

        res["Website 1 - Label"] = None
        res["Website 1 - Value"] = " ::: ".join([get_proper_url(url) for url in urls])

    res["Name Suffix"] = f" kb-23-{class_number[0]}-{'M' if gender == '남' else 'F'}"
    # print(name, f'|{res["Name Suffix"]}|')
    res["Labels"] = get_label_str("kyungbok 23 (Shared)")

    return res


def convert_phone_number(mobile_number: str) -> str:
    if mobile_number.startswith("010"):
        return "+82 " + mobile_number[1:]

    if mobile_number == "+71452586486":
        return "+61 452586486"
    if mobile_number == "9194236985":
        return "+1 " + mobile_number
    if mobile_number == "491627231874":
        return "+49 " + mobile_number[2:]
    if mobile_number.strip() == "213-675-6905":
        return "+1 " + mobile_number.strip()
    if mobile_number == "1-213-503-9802":
        return "+" + mobile_number
    if mobile_number == "+19032763246":
        return "+1 " + mobile_number[2:]
    if mobile_number.startswith("82-10"):
        return "+" + mobile_number

    return mobile_number


def get_proper_url(url: str) -> str:
    return url.split("?")[0]


def get_proper_birthday_str(birthday: str) -> str:
    month, day, year = birthday.split("/")
    return f"{year}-{month.zfill(2)}-{day.zfill(2)}"


if __name__ == "__main__":
    set_logging_basic_config(__file__)

    home_dir: str = str(Path.home())
    dir: str = os.path.join(home_dir, "workspace/kyungbok-elementary.github.io/resource/contacts/")
    tsv_file_path: str | None = get_most_recent_file(dir)
    google_contacts_csv_filepath: str = os.path.join(
        dir, "google-contacts", "kb-23-google-contacts.csv"
    )

    assert tsv_file_path is not None and os.path.splitext(tsv_file_path)[1] == ".tsv", tsv_file_path

    logger.info(f"`{tsv_file_path}' is selected as the most recent TSV file.")
    logger.info(f"read from `{tsv_file_path}' ...")
    df: DataFrame = read_csv(tsv_file_path, sep="\t")

    logger.info(f"write to `{google_contacts_csv_filepath}' ...")
    DataFrame(
        [
            convert_person_info_to_google_contact_dict(df.iloc[row_idx])
            for row_idx in range(df.shape[0])
        ]
    ).to_csv(google_contacts_csv_filepath)
