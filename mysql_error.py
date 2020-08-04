import os
import re
from typing import TypedDict, List

import requests
from git import Repo
from jinja2 import Environment, PackageLoader
from lxml import html


class MysqlError(TypedDict):
    message: str
    name: str
    code: int
    state: str


def template(errors: List[MysqlError]):
    env = Environment(loader=PackageLoader("mysql_error", ""))
    tmplte = env.get_template("mysql_error.ts.j2")

    with open("mysql_error.ts", "w") as result_file:
        result_file.write(tmplte.render(errors=errors))


def scrape():
    response = requests.get("https://dev.mysql.com/doc/mysql-errors/8.0/en/server-error-reference.html")
    document = html.fromstring(response.text)
    error_tags = document.cssselect("div.chapter > div > ul > li")
    first_pattern = re.compile("^\\s*Error number: (\\d+); Symbol: (.+); SQLSTATE: (.+)\\s*$")
    second_pattern = re.compile("^\\s*Message: (.+)\\s*$")

    errors = []

    for error_element in error_tags:
        paragraphs = [e for e in error_element if e.tag == "p"]
        first_paragraph = " ".join(str(paragraphs[0].text_content()).split())
        match = first_pattern.match(first_paragraph)

        if not match:
            # print(f"Does not match first: {error_element.text_content()}")
            continue

        error_code = int(match[1])
        error_symbol = match[2]
        error_state = match[3]

        second_paragraph = " ".join(str(paragraphs[1].text_content()).split())
        match = second_pattern.match(second_paragraph)

        if not match:
            # print(f"Does not match second: {error_element.text_content()}")
            continue

        error_message = match[1]
        errors.append(MysqlError(message=error_message, name=error_symbol, code=error_code, state=error_state))
    return errors


def update_git():
    cwd = os.getcwd()
    git_path = os.path.join(cwd, ".git")

    if not os.path.exists(git_path):
        repo = Repo.init()
    else:
        repo = Repo(git_path)

    if repo.untracked_files:
        repo.index.add(repo.untracked_files)
        repo.index.commit("Add untracked files")

    if repo.is_dirty():
        repo.index.commit("Update changed files")

    # try:
    #     remote = repo.remote("origin")
    # except ValueError:
    #     remote = repo.create_remote("origin", "https://github.com/mytlogos/common.git")


def main():
    # errors = scrape()
    # template(errors)
    update_git()


if __name__ == '__main__':
    main()
