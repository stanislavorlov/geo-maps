# geo-maps
Implementation of online maps using data structures

## Run a service
```bash
uv run fastapi dev
```

## Run tests

```bash
PYTHONPATH=app .venv/bin/pytest tests/test_routing_algorithms.py -v
```


## Run a parser
```bash
cd geo-maps
PYTHONPATH=. ./.venv/bin/python data/parser/osm_parser.py --mode file --output graph.json
```