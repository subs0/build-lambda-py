# `@-0/build-lambda-py`

Node CLI for building Python Lambda packages using Poetry
## Installation

### Add CLI as a `file` Dependency for NPM Scripts

```
npm install -D @-0/build-lambda-py
```

You will see a working example in the [example](./example) directory.

### `example/package.json`
```json
{
    ...
    "scripts": {
        "build": "lambda build parent"
    },
    "dependencies": {
        "lambda": "file:./node_modules/@-0/build-lambda-py"
    },
    "devDependencies": {
        "@-0/build-lambda-py": "^1.0.4"
    }
    ...
}
```

### In Use
From inside the [`example`](./example) directory. Running `npm run build` will produce the following output:

```
npm run build

> example-build-lambda-py-cli@1.0.0 build
> lambda build parent

==== Building: ...parent ====

exporting    : requirements.txt...
building     : parent from poetry.lock file...
rolling      : wheels for dependencies...
copying      : handler and src into package root...
touching     : __init__.py into package root...
zipping      : package as: parent.zip

==== Zipped: ...parent/zipped/parent.zip ====
```

You will then have a nicely zipped Python Lambda package in the `zipped` directory.

## Running the CLI Directly
From inside the [`example`](./example) directory

```diff
> npx @-0/build-lambda-py build parent
```

### Help

```diff
> npx @-0/build-lambda-py help build
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

## Dependencies

- [Node.js](https://nodejs.org/en/)
- [Commander.js](https://www.npmjs.com/package/commander)
- [Python](https://www.python.org/)
- [Poetry](https://python-poetry.org/)


