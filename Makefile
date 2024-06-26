
help:	## Show all Makefile targets.
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[33m%-30s\033[0m %s\n", $$1, $$2}'

install: ## install package
	@pip3 install .

install-build-deps: ## install build dependecied
	@pip3 install black pylint build twine

pylint:	## test pylint score
	@pylint $(shell git ls-files '*.py') 

format:	## format code 
	@python3 -m black .

build-wheel: ## build wheel
	@rm -rf dist
	@python3 -m build .

publish:	dist	## publish build
	@python3 -m twine upload  dist/*
