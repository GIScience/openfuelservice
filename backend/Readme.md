# Openfuelservice Backend
## Requirements
```text
- Python >= 3.8
- Poetry
- Docker
- Docker-Compose
```
## Production - TBD
## Development
### Install
```shell
cd backend/
python3 -m venv .venv
source .venv/bin/activate
poetry install
```
### Testing with tox:
List all tox test envs
```shell
$ tox -a
lint # Check with several code linters.
format # Format the code to pass the lint stage
pytest-local-py38 # Testing env with a local dockerized database from `docker-compose-debug.yml`
pytest-local-py39 # Testing env with a local dockerized database from `docker-compose-debug.yml`
pytest-local-py310 # Testing env with a local dockerized database from `docker-compose-debug.yml`
pytest-docker-py38 # Let tox take care of all the necessary docker containers. They're deleted after the runs.
pytest-docker-py39 # Let tox take care of all the necessary docker containers. They're deleted after the runs.
pytest-docker-py310 # Let tox take care of all the necessary docker containers. They're deleted after the runs.
pytest-github-py38 # Run pytest-local-pyxx instead. The testing env for the github actions. Can be run locally. Outputs an xml without readable stats.
pytest-github-py39 # Run pytest-local-pyxx instead. The testing env for the github actions. Can be run locally. Outputs an xml without readable stats.
pytest-github-py310 # Run pytest-local-pyxx instead. The testing env for the github actions. Can be run locally. Outputs an xml without readable stats.
```

Default: Option 1 - pytest-local-py{38,39,310}:
```shell
docker-compose -f docker-compose-debug.yml up -d
cd backend/
tox --parallel
```
Option 2 - pytest-docker-py{38,39,310}:
Do not use --parallel until https://github.com/tox-dev/tox-docker/pull/121 is merged and tox-docker updated in the deps!
Else the container names will collide.
```shell
cd backend/
tox -e pytest-docker-py38,pytest-docker-py39,pytest-docker-py310
```

Option 3 - pytest-github-py{38,39,310}:
It's runnable locally but it doesn't make much sense, since its target is the GitHub environment.
Does the same as option 1 but outputs the statistics to xml instead of printing it to console.
This is useful for codecov changes.
Can be run in parallel.
```shell
docker-compose -f docker-compose-debug.yml up -d
cd backend/
tox --parallel -e pytest-github-py38,pytest-github-py39,pytest-github-py310
```
