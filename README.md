# `build-lambda-py.js`

Node CLI for building Python Lambda packages using Poetry

## Help

```
> node build-lambda-py help build
Usage: build-lambda-py build [options] <parent>

Builds a Python Lambda package using Poetry

Arguments:
  parent                [relative to script] Source directory containing all dependencies...

  Suggested parent structure:

      parent
      ├── src
      │   ├── __init__.py
      │   └── local_dep.py
      ├── handler.py
      ├── pyproject.toml
      └── poetry.lock


Options:
  -h, --handler <file>  [relative to parent] Lambda handler file (default: "handler.py")
  -t, --target <dir>    [relative to parent] Target director containing code to bundle (default: "src")
  -o, --out-dir <dir>   [relative to parent] DEDICATED zip file output directory (default: "zipped")
  -d, --dev-deps        Include Poetry `group.dev` dependencies (default: false)
  --help                display help for command
```

## Usage

```
> node build-lambda-py build ../terraform/lambdas/upload_mp

==== Building: ...terraform/lambdas/upload_mp ====

exporting    : requirements.txt...
building     : upload_mp from poetry.lock file...
rolling      : wheels for dependencies...
copying      : handler and src into package root...
touching     : __init__.py into package root...
zipping      : package as: upload_mp.zip

==== Zipped: ...upload_mp/zipped/upload_mp.zip ====
```

## Dependencies

- [Node.js](https://nodejs.org/en/)
- [Commander.js](https://www.npmjs.com/package/commander)
- [Python](https://www.python.org/)
- [Poetry](https://python-poetry.org/)