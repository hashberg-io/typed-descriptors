@echo off
mypy --strict typed_descriptors
pytest test --cov=./typed_descriptors
coverage html
@pause
