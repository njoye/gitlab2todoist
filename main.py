import logging
import re
import yaml
import gitlab
import todoist

# Read configuration values
config = {}
with open("config.yml", "r") as stream:
    try:
        config = yaml.safe_load(stream)
    except:
        logging.error("Error while reading configuration")

# Logger Configuration
logging.basicConfig(format='%(asctime)s %(levelname)-4s %(message)s',
                    level=logging.INFO,
                    datefmt='%Y-%m-%d %H:%M:%S')

logging.info("Logging in to '" + str(config["gitlab_url"]) + "'")
# Create Gitlab & Todoist Instance & authenticate
gl = gitlab.Gitlab(config["gitlab_url"], oauth_token=config["gitlab_oauth_token"])
gl.auth()

logging.info("Authenticating Todoist API")
td = todoist.TodoistAPI(config["todoist_api_key"])
td.sync()

# Get all issues in AGV
group = gl.groups.get(config["gitlab_group_id"])
open_issues = group.issues.list(state='opened', assignee_id=config["gitlab_assignee_id"], all=True)
closed_issues = group.issues.list(state='closed', assignee_id=config["gitlab_assignee_id"], page=1, per_page=config["gitlab_check_closed_issues_amount"])
open_items = td.projects.get_data(config["todoist_project_id"])["items"]

logging.info("Retrieved " + str(len(open_issues)) + " open issues having assignee ID " + str(config["gitlab_assignee_id"]))
logging.info("Retrieved " + str(len(closed_issues)) + " closed issues having assignee ID " + str(config["gitlab_assignee_id"]))
logging.info("Retrieved " + str(len(open_items)) + " open Todoist items.")

# Check all todoist items if the assignee is still in the issue
logging.info("Checking if any Todoist item is not assigned as issue anymore")
for item in open_items:
    gitlab_ids = re.findall("\[GitLabID#(\d+)\]", item["description"])
    if len(gitlab_ids) == 1:
        issues = group.issues.list(id=gitlab_ids[0], page=1, per_page=config["gitlab_check_closed_issues_amount"])
        for issue in issues:
            if int(issue.id) == int(gitlab_ids[0]):
                still_assigned = False
                for assignee in issue.assignees:
                    if int(assignee["id"]) == int(config["gitlab_assignee_id"]):
                       still_assigned = True

                if not still_assigned:
                    logging.info("Not assigned to issue " + str(issue.id) + " anymore, completing it.")
                    td.items.complete(item["id"])

# Get closed issues and match them with existing todoist items to close them
logging.info("Checking if any issue was closed and can be completed in Todoist")
for issue in closed_issues:
    project = gl.projects.get(issue.project_id)
    project_tag = "[" + str(project.name) + "#" + str(issue.iid) + "]"
    gitlab_tag = "[GitLabID#" + str(issue.id) + "]"

    # Test if the issue is already present in Todoist by checking for the Gitlab internal id
    for item in open_items:
        # Check if the ID exists at all in the item description and if ID matches
        gitlab_ids = re.findall("\[GitLabID#(\d+)\]", item["description"])
        if len(gitlab_ids) == 1 and int(gitlab_ids[0]) == issue.id: 
            logging.info("Matched item with Git closed issue ID " + str(issue.id) + " to Todoist ID " + str(item["id"]) + " - closing it")
            td.items.complete(item["id"])

# Get open issues and match them with existing todoist items to either create an item or update one
for issue in open_issues:
    project = gl.projects.get(issue.project_id)
    project_tag = "[" + str(project.name) + "#" + str(issue.iid) + "]"
    gitlab_tag = "[GitLabID#" + str(issue.id) + "]"

    description = " ".join([project_tag, "issue.description", gitlab_tag])
    if issue.description is not None:
        description = " ".join([project_tag, issue.description, gitlab_tag])

    matched = False

    # Test if the issue is already present in Todoist by checking for the Gitlab internal id
    for item in open_items:
        # Check if the ID exists at all in the item description and if ID matches
        gitlab_ids = re.findall("\[GitLabID#(\d+)\]", item["description"])
        if len(gitlab_ids) == 1 and int(gitlab_ids[0]) == issue.id: 
            matched = True
            logging.info("Matched item with Git ID " + str(issue.id) + " to Todoist ID " + str(item["id"]) + " - updating it")
            td.items.update(item["id"], content=issue.title, description=description)

    if not matched:
        # Check if the issue was inside the project and was checked of!
        logging.info("Couldn't match open issue with Gitlab ID " + str(issue.id) + " - creating Todoist item for it")
        td.items.add(issue.title, 
            description=description,
            project_id=config["todoist_project_id"])
        

logging.info("Comitting changes to Todoist")
td.commit() 