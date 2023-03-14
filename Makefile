initialise:
	@echo "Initializing git..."
	git init
	@echo "Initializing Poetry"
	poetry init
	poetry env use /bin/python3.10
	
install: 
	@echo "Installing..."
	poetry install
	poetry run pre-commit install

activate:
	@echo "Activating virtual environment"
	poetry env use /bin/python3.10
	poetry shell

run_app:
	@echo "Running app"
	streamlit run app.py

scrape:
	@echo "Scraping websites"
	python ./src/scraper.py

format:
	@echo "Formatting..."
	black ./
	flake8 ./
	isort ./
	interrogate -vv ./

test:
	pytest

## Delete all compiled Python files
clean:
	find . -type f -name "*.py[co]" -delete
	find . -type d -name "__pycache__" -delete
	rm -rf .pytest_cache
	