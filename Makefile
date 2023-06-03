.PHONY: all zip ankiweb fix mypy pylint vendor clean

all: zip ankiweb

zip:
	python -m ankiscripts.build --type package --qt all --exclude user_files/**/

ankiweb:
	python -m ankiscripts.build --type ankiweb --qt all --exclude user_files/**/

fix:
	python -m black src tests --exclude="forms|vendor"
	python -m isort src tests

mypy:
	python -m mypy src tests

pylint:
	python -m pylint src tests

vendor:
	pip install -r requirements.txt -t src/vendor
clean:
	rm -rf build/
