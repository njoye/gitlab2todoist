## Gitlab2Todoist
Python script that syncs GitLab instance issues of one user with their Todoist account. I personally use this to automatically create, update & close tasks in Todoist based on their state in the Gitlab instance hosted by my workplace.

### Setup

Clone the repository, `cd` into it and use the package manager [pip](https://pip.pypa.io/en/stable/) to install the requirements. Afterwards you need to create the `config.yml` file (based on the `config.example.yml`).

```bash
git clone https://github.com/njoye/gitlab2todoist

cd gitlab2todoist

pip3 install -r requirements.txt

# Edit the configuration file with your personal values!
```

### Usage
I use this script with a cronjob on my personal server and run it every few minutes so that my Todoist account is always up-to-date. I use the following command.

```
cd /directory/to/script/gitlab2todoist && python3 main.py
```

### Contributing
Pull requests are welcome. For major changes, please open an issue first to discuss what you would like to change.

### License
[MIT](https://choosealicense.com/licenses/mit/)