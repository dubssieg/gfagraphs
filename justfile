build:
  @rm dist/* && python -m build && twine upload dist/*

and:
  @pip install gfagraphs --upgrade

run:
  @pip install gfagraphs --upgrade

local:
  @python -m pip install .