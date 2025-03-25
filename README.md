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

```bash
docker-compose up
docker exec -i combine-mysql mysql -u root -p<password> qfinder < <path to file>

```

## Rabbit MQ

Add a user with the permissions
```bash
rabbitmqctl add_user <user> <password>
rabbitmqctl set_user_tags <user> administrator
rabbitmqctl set_permissions -p "/" "<user>" ".*" ".*" ".*"
```

## Clean up
```bash
find . -type d -name __pycache__ -exec rm -r {} \+
```

### WeasyPrint to work on windows

https://github.com/tschoonj/GTK-for-Windows-Runtime-Environment-Installer/releases
