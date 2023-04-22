Inside a virtualenv

    python -m pip install pip-tools

    pip-sync requirements.txt dev-requirements.txt


Update requirements

    pip-compile --upgrade

    pip-compile dev-requirements.in --upgrade
