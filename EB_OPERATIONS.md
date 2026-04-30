# Elastic Beanstalk Operations Guide

## Deploy

```bash
git add .
git commit -m "your message"
eb deploy
```

> EB deploys using `git archive`, so only committed files are included. Always commit before deploying.

---

## Check Environment Status

```bash
eb status
```

---

## Check Logs

### Stream recent logs
```bash
eb logs
```

### Filter for errors only
```bash
eb logs 2>&1 | grep -A 10 "Error\|Traceback" | head -80
```

### Check the deployment engine log
```bash
eb logs --log-group /aws/elasticbeanstalk/sarah-django-backend-prod/var/log/eb-engine.log
```

### Check the cfn-init log (container command failures)
```bash
eb ssh --command "sudo cat /var/log/cfn-init.log | tail -50"
```

---

## SSH Access

### Open an SSH session
```bash
eb ssh
```
Type `yes` when prompted about the host fingerprint.

### Run a single command without opening a session
```bash
eb ssh --command "sudo cat /var/log/eb-engine.log | tail -50"
```

### Run Django management commands via SSH

SSH into the instance, then source the environment variables and activate the virtualenv:

```bash
eb ssh
source <(sudo cat /opt/elasticbeanstalk/deployment/env | sed 's/^/export /')
source /var/app/venv/*/bin/activate
cd /var/app/current
```

Then run any management command, e.g.:

```bash
python manage.py createsuperuser
python manage.py migrate --noinput
python manage.py shell
```

---

## Set / Update Environment Variables

```bash
eb setenv KEY=value KEY2=value2
```

### View current environment variables
```bash
eb printenv
```

---

## Open the App in the Browser

```bash
eb open
```

---

## Key File Locations on the Instance

| File | Purpose |
|------|---------|
| `/var/log/eb-engine.log` | Deployment engine errors |
| `/var/log/cfn-init.log` | Container command errors (`.ebextensions`) |
| `/var/log/web.stdout.log` | Gunicorn stdout (app logs) |
| `/var/app/current/` | Deployed application code |
| `/var/app/venv/` | Python virtual environment |
| `/opt/elasticbeanstalk/deployment/env` | Environment variables injected by EB |
