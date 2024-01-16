python -m build
python -m twine check dist/*
python -m twine upload --verbose --skip-existing dist/*
pause
