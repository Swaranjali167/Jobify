from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from socket import gaierror
import smtplib
import linkedin_scraper
import indeed_scraper
import monster_scraper
import going_global_scraper
import simplyhired_scraper
import helper
import time

def run():
    connection = helper.db_connect()
    data = get_user_notification_info(connection)
    user_info = generate_user_info(data)
    user_job_board_list = generate_user_job_board_list(data)
    # print(user_info)
    # print(user_job_board_list)
    job_board_role_mp = generate_job_board_role_mp(user_job_board_list, user_info)

    all_skills = helper.get_all_skills()
    job_map = generate_job_map(job_board_role_mp, all_skills)

    user_jobs = generate_user_jobs_mp(user_info, user_job_board_list, job_map)

    user_skills_map = helper.get_user_skills_map()
    user_jobs = helper.filter_jobs(user_jobs, user_skills_map)
    send_mail(user_jobs, user_info, user_skills_map)


def generate_user_info(data):
    user_info = {}
    for d in data:
        user_info[d[0]] = (d[3], d[2], d[1])
    return user_info


def generate_user_job_board_list(data):
    list = []
    for d in data:
        list.append((d[0], d[4]))
    return list


def generate_user_jobs_mp(user_info, user_job_board_list, job_map):
    user_jobs = {}
    for uj in user_job_board_list:
        user = uj[0]
        if user not in user_jobs:
            user_jobs[user] = []
        user_job_req = (user_info[user][0], user_info[user][1])
        jobs = job_map[uj[1]][user_job_req]
        user_jobs[user].extend(jobs)
    return user_jobs


# This function generates a map of job board and map of pair of role and location
# and jobs with that role and Location
# example:
#     {'LINKEDIN' : {
#         ('Software Developer Intern', 'Raleigh'): [{
#             'title': ..,
#             'url':..,
#             'skills':..
#             }]
#         }
#     }
def generate_job_map(job_board_role_mp, all_skills):
    job_map = {}
    for jb in job_board_role_mp.keys():
        job_map[jb] = {}
        for rl in job_board_role_mp[jb]:
            time.sleep(30)
            j = []
            print("Scraping " + jb + " for " + rl[0] + " in " + rl[1] + "...")
            if (jb == 'LINKEDIN'):
                j = linkedin_scraper.get_jobs(rl[0], rl[1], 10, all_skills)
            elif (jb == 'INDEED'):
                j = indeed_scraper.get_jobs(rl[0], rl[1], 10, all_skills)
            elif (jb == 'MONSTER'):
                j = monster_scraper.get_jobs(rl[0], rl[1], 10, all_skills)
            elif (jb == 'GOINGLOBAL'):
                j = going_global_scraper.get_jobs(rl[0], rl[1], 10, all_skills)
            elif (jb == 'SIMPLYHIRED'):
                j = simplyhired_scraper.get_jobs(rl[0], rl[1], 10, all_skills)
            job_map[jb][rl] = j
    return job_map


# This function generates a map of job boards and list of pair of job role and location.
# example:
#   {'LINKEDIN': [('Software Developer Intern', 'Raleigh')]}
def generate_job_board_role_mp(user_job_board_list, user_info):
    job_board_role_mp = {}
    for uj in user_job_board_list:
        if uj[1] not in job_board_role_mp:
            job_board_role_mp[uj[1]] = []
        u_info = user_info[uj[0]]
        job_board_role_mp[uj[1]].append((u_info[0], u_info[1]))
    return job_board_role_mp


def send_mail(user_jobs, user_info, user_skills):
    port = 587
    smtp_server = "smtp.gmail.com"
    login = "srijas.alerts@gmail.com"
    password = "SRIJASGMAILPWD"
    sender = "srijas.alerts@gmail.com"
    for user in user_info.keys():
        receiver = user
        jobs = user_jobs[user]
        if len(jobs) == 0:
            continue
        msg = MIMEMultipart()
        msg['From'] = sender
        msg['To'] = receiver
        msg['Subject'] = 'SRIJAS - Job List'

        body = """\n Hi """ + user_info[user][2] + """,\n Good News !! \n We have found """ + str(len(jobs)) + """ job that match your resume \n"""
        msg.attach(MIMEText(body, 'plain'))

        temp_body = ""
        html_start = """<html><head></head><body><p><ol>"""
        for job in jobs:
            temp_body += "<li>" + job['title'] + "<a href=\"" + job['url'] + "\"> Click to Apply </a><br>"
            temp_body += "Match Percentage: " + helper.match_percentage(user_skills[user], job['skills']) + "<br>"
            temp_body += "Matching Skills: " + helper.print_matching_skills(user_skills[user], job['skills'])
        html_end = """</ol></p></body> </html>"""

        html = html_start + temp_body + html_end

        msg.attach(MIMEText(html, 'html'))

        msg.attach(MIMEText("\n\n Regards, \nTeam SRIJAS", 'plain'))
        text = msg.as_string()

        try:
            server = smtplib.SMTP(smtp_server, port)
            server.connect(smtp_server, port)
            server.ehlo()
            server.starttls()
            server.ehlo()
            print("Sending mail for " + receiver)
            server.login(login, password)
            server.sendmail(sender, receiver, text)
            server.quit()                                                                                # tell the script to report if your message was sent or which errors need to be fixed
            print('Sent')
        except (gaierror, ConnectionRefusedError):
            print('Failed to connect to the server. Bad connection settings?')
        except smtplib.SMTPServerDisconnected as e:
            print('Failed to connect to the server. Wrong user/password?')
            print(str(e))
        except smtplib.SMTPException as e:
            print('SMTP error occurred: ' + str(e))


def get_user_notification_info(connection):
    query = "SELECT um.user_email, um.user_fname, um.location, jm.job_title, jb.name from user_master um, job_board jb, job_master jm, user_notification un where um.user_preferred_job_id = jm.job_id and um.user_id = un.user_id and un.job_board_id = jb.job_board_id"
    cursor = connection.cursor()
    cursor.execute(query)
    return cursor.fetchall()


if __name__ == '__main__':
    run()
