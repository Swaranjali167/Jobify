import helper
import requests
from bs4 import BeautifulSoup
import traceback


def get_jobs(role, location, no_of_jobs_to_retrieve, all_skills):
    url = "https://www.linkedin.com/jobs/jobs-in-" + location + "?keywords=" + role
    url = url.replace(' ', '%20')
    k1 = requests.get(url)
    if k1.status_code != 200:
        print(url)
        print("Connection Failed")
    soup1 = BeautifulSoup(k1.content, 'html.parser')
    string1 = soup1.find_all("a", {"class": "base-card__full-link"})
    jobs = []
    job_role = []
    job_details = {}
    try:
        for i in range(len(string1)):
            if no_of_jobs_to_retrieve > 0:
                job = {}
                job["title"] = string1[i].get_text().replace('\n', ' ').replace(' ', '')
                job["url"] = string1[i]['href']
                job_details[job["url"]] = [job["title"], ""]
                job_role.append(string1[i].get_text().replace('\n', ' ').replace(' ', ''))
                no_of_jobs_to_retrieve -= 1
                k = requests.get(string1[i]['href']).text
                soup = BeautifulSoup(k, 'html.parser')
                str2 = soup.find_all("div", {"class": "description__text"})
                skills = []
                if len(str2) > 0:
                    str3 = str2[0].get_text()
                    skills = helper.extract_skills(str3, all_skills)
                job["skills"] = skills
                jobs.append(job)
    except Exception:
        traceback.print_exc()
    return jobs


if __name__ == '__main__':
    ans = get_jobs("Software Engineer", "Raleigh", 200, helper.get_all_skills())
    print(ans)
