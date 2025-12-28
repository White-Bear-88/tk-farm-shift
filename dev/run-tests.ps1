# Install dev requirements and run pytest
python -m pip install -r dev/dev-requirements.txt
python -m pytest -q --disable-warnings --maxfail=1
