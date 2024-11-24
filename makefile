# SPDX-FileCopyrightText: Copyright (c) 2024 Dana Runge
#
# SPDX-License-Identifier: Unlicense
install:
	python3 -m venv .venv; \
	source .venv/bin/activate; \
	pip install -Ur requirements.txt; \
	pip install -Ur requirements/dev.txt;

.PHONY: docs
docs:
	source .venv/bin/activate; \
	cd docs; \
	sphinx-build -E -W -b html . _build/html;

check:
	source .venv/bin/activate; \
	pre-commit run --all-files;

deploy:
	source .venv/bin/activate; \
	python3 deploy.py --code=examples/fireworks.py \
	--pin=board.D4

dmx_transmitter/machine_code.py:
	python3 assembly_code/reformat_pioasm.py --sideset-pins 1 --python assembly_code/assembly_code.txt > dmx_transmitter/machine_code.py


clean:
	rm -rf .venv
	find -iname "*.pyc" -delete
	rm -rf docs/_build/html
