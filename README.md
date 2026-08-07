# geo-maps
Implementation of online maps using data structures

## Run a service
```
uv run fastapi dev
```

## Run a parser
```
cd geo-maps
PYTHONPATH=. ./.venv/bin/python data/parser/osm_parser.py --mode file --output graph.json
```