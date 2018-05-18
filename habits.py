import os
import re
import logging
from datetime import datetime, timedelta
from dateutil.parser import parse
from todoist.api import TodoistAPI

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


def get_token():
    token = os.getenv('TODOIST_APIKEY')
    return token


def get_project(api):
    project = os.getenv('TODOIST_PROJECT')
    if not project:
        return None
    for p in api.state['projects']:
        if p['name'] == project:
            return p['id']


def is_habit(text):
    return re.search(r'\[day\s(\d+)\]', text)


def update_streak(item, streak):
    days = '[day {}]'.format(streak)
    text = re.sub(r'\[day\s(\d+)\]', days, item['content'])
    item.update(content=text)


def main():
    API_TOKEN = get_token()
    today = datetime.utcnow().replace(tzinfo=None)
    if not API_TOKEN:
        logging.error('Please set the API token in environment variable.')
        exit()
    api = TodoistAPI(API_TOKEN)
    api.sync()
    project_id = get_project(api)
    tasks = api.state['items']
    for task in tasks:
        content = task['content']
        if all([
            task['due_date_utc'],
            is_habit(content),
            not project_id or task['project_id'] == project_id
        ]):
            logger.info("Found task id:%s content:%s", task['id'], content[:20])
            date_string = task['date_string'] or 'ev day'
            task_id = task['id']
            due_at = parse(task['due_date_utc'], ignoretz=True)
            days_left = due_at.date() - today.date()
            if days_left:
                habit = is_habit(content)
                streak = int(habit.group(1)) + 1
                update_streak(task, streak)
                api.notes.add(task_id, '[BOT] Streak extended. Yay!')
            else:
                update_streak(task, 0)
                task.update(date_string=date_string + ' starting tod')
                api.notes.add(task_id, '[BOT] Chain broken :(')
    api.commit()

if __name__ == '__main__':
    main()
