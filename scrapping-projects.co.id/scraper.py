import json
from dataclasses import asdict, dataclass

import httpx
from selectolax.parser import HTMLParser


@dataclass
class Job:
    title: str
    list_label: str
    link: str
    salary: str
    finish_days: int


def total_page():
    try:
        limit = (
            get_html(1)
            .css_first("ul.pagination > li:last-child > a")
            .attributes["paramval"]
        )
        return int(limit)
    except ValueError:
        return 1


def get_html(page):
    url = f"https://projects.co.id/public/browse_projects/listing?page={page}&ajax=1"
    response = httpx.get(url)
    return HTMLParser(response.text)


def parse_data(html):
    jobs = []
    for job in html.css("div.row > div.col-md-10"):
        try:
            title = job.css_first("h2 a").text()
            title = " ".join(title.split())
            title = title.replace(",", "|")
        except AttributeError:
            title = "--"

        try:
            list_label = "| ".join([label.text() for label in job.css("p > span > a")])
        except AttributeError:
            list_label = "--"

        try:
            link = job.css_first("h2 a").attributes["href"]
        except AttributeError:
            link = "--"

        try:
            salary = job.css_first(".well > .row > div").text()
            spit = salary.split("      ")
            salary = spit[1].replace("Published Budget:\n    ", "").replace(",", ".")
            finish_days = int(spit[4].replace("Finish Days:\n    ", ""))
        except AttributeError:
            salary = "--"
            finish_days = 0

        jobs.append(
            Job(
                title=title,
                list_label=list_label,
                link=link,
                salary=salary,
                finish_days=finish_days,
            )
        )
    return jobs


def to_json(jobs):
    with open("data.json", "w", encoding="utf-8") as f:
        f.write(json.dumps([asdict(job) for job in jobs], indent=4))


def to_csv(jobs):
    with open("data.csv", "w", encoding="utf-8") as f:
        f.write("title,list_label,link,salary,finish_days\n")
        for job in jobs:
            f.write(
                f"{job.title},{job.list_label},{job.link},{job.salary},{job.finish_days}\n"
            )


def main():
    jobs = []

    for page in range(1, total_page() + 1):
        html = get_html(page)
        job = parse_data(html)
        jobs.extend(job)

    to_json(jobs)
    to_csv(jobs)


if __name__ == "__main__":
    main()
