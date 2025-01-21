# Combine

Assumes you have python ^3.12 and poetry installed already

# Installation
```bash
poetry install
```

```bash
poetry add poetry-plugin-export
poetry export -f requirements.txt --output requirements.txt
```

## Rabbit MQ

Add a user with the permissions
```bash
rabbitmqctl add_user <user> <password>
rabbitmqctl set_user_tags <user> administrator
rabbitmqctl set_permissions -p "/" "<user>" ".*" ".*" ".*"
```
