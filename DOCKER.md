Docker
====================

Build the container

```bash
docker build -t matterbot .
```

Run it

Default environement variable are : 
- MATTERBOT_URL : url of your mattermost server
- MATTERBOT_LOGIN : login name of your bot
- MATTERBOT_PASSWORD : password of the login
- MATTERBOT_TEAM : name of your team on mattermost
- MATTERBOT_IGNORE : disabled notification for the bot to answer (@here, @channel)

Jira environement variable are : 
- MATTERBOT_JIRA_URL : url of your jira server
- MATTERBOT_JIRA_PROJECT : name of the jira project
- MATTERBOT_JIRA_LOGIN : login name of the jira account
- MATTERBOT_JIRA_PASSWORD : password for the jira account

Full command

```bash
docker run -d --rm --name matterbot \
    -e MATTERBOT_URL=http://mattermost.myurl.com \
    -e MATTERBOT_LOGIN=Matterbot \
    -e MATTERBOT_PASSWORD=MyStr0ngP4ssw0rd! \
    -e MATTERBOT_TEAM=MATTERMOST_TEAM_NAME \
    -e MATTERBOT_IGNORE=true \
    -e MATTERBOT_JIRA_URL=http://jira.myurl.com \
    -e MATTERBOT_PRJECT=PRJ \
    -e MATTERBOT_LOGIN=Matterbot \
    -e MATTERBOT_PASSWORD=MyStr0ngP4ssw0rd! \
    matterbot
```