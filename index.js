#! /usr/bin/env node
import fs from 'fs'
import path from 'path'
import { spawn } from 'child_process'
import { Command } from 'commander'
const program = new Command()

program
    .name('build-lambda-py')
    .description('Build a Python Lambda package using Poetry')
    .version('0.0.1')

const runs = async (
    { cmd, args, log = '', name } = {
        cmd: 'cmd',
        args: [''],
        name: 'name of function',
    }
) => {
    log && console.log(name, log)
    return new Promise((resolve, reject) => {
        spawn(cmd, args).on('exit', (code) => {
            if (code !== 0) {
                console.error(`\`${name}\` failed with exit code ${code}.`)
                reject(code)
                process.exit(1)
            }
            resolve(true)
        })
    })
}

const exporting = (devDeps = false) =>
    runs({
        name: 'exporting',
        cmd: 'poetry',
        args: [
            'export',
            '-f',
            'requirements.txt', // default format
            '-o',
            'requirements.txt', // output path (relative to parent)
            '--without-hashes',
            ...(!devDeps ? ['--without', 'dev'] : []),
        ],
        log: '   : requirements.txt...',
    })

const building = (directory) =>
    runs({
        name: 'building',
        cmd: 'poetry',
        args: ['build'],
        log: `    : ${directory} from poetry.lock file...`,
    })

const rolling = (tempDir) =>
    runs({
        name: 'rolling',
        cmd: 'poetry',
        args: [
            'run',
            'pip',
            'install',
            '-r',
            'requirements.txt', // input path (relative to parent)
            '--upgrade',
            '--only-binary',
            ':all:',
            '--platform',
            'manylinux2014_x86_64',
            '--target',
            tempDir, // default for poetry build step
        ],
        log: '     : wheels for dependencies...',
    })

const copying = async (handler, tempDir, target) =>
    runs({
        name: 'copying',
        cmd: 'cp',
        args: ['-r', handler, target, tempDir],
        log: `     : handler and ${target} into package root...`,
    })

const touching = async (tempDir) =>
    runs({
        name: 'touching',
        cmd: 'touch',
        args: [`${tempDir}/__init__.py`],
        log: '    : __init__.py into package root...',
    })

const zipping = (outFile, outDir) =>
    runs({
        name: 'zipping',
        cmd: 'zip',
        args: ['-r', '-q', outFile, '.', '-x', '*.pyc', outDir],
        log: `     : package as: ${outFile.split('/').slice(-1)}`,
    })

const housekeeping = async (...temps) =>
    runs({
        name: 'housekeeping',
        cmd: 'rm',
        args: ['-rf', ...temps],
    })

const suggestion = `
    
Suggested parent structure:

    parent
    ├── src
    │   ├── __init__.py
    │   └── local_dep.py
    ├── handler.py
    ├── pyproject.toml
    └── poetry.lock
`

const main = async () => {
    program
        .command('build ')
        .description('Builds a Python Lambda package using Poetry')
        .argument(
            '<parent>',
            `\`relative\`to script] Source directory containing all dependencies... ${suggestion}`
        )
        .option('-h, --handler <file>', '[relative to parent] Lambda handler file', 'handler.py')
        .option(
            '-t, --target <dir>',
            '[relative to parent] Target director containing code to bundle',
            'src'
        )
        .option(
            '-o, --out-dir <dir>',
            '[relative to parent] DEDICATED zip file output directory',
            'zipped'
        )
        .option('-d, --dev-deps', 'Include Poetry `group.dev` dependencies', false)
        .action(async (parent, options) => {
            const { outDir, target, devDeps, handler } = options
            const [directory] = parent.split('/').reverse()
            if (!fs.existsSync(parent)) {
                console.error(`Source directory not found: ${parent}`)
                process.exit(1)
            } else {
                console.log(`==== Building: ...${parent.split('/').slice(-3).join('/')} ====\n`)
            }
            const projectPath = path.join(process.cwd(), parent)
            const outputPath = path.join(projectPath, outDir)
            const outFile = path.join(outputPath, `${directory}.zip`)
            const tempDir = '__package'
            const tmpPath = path.join(projectPath, tempDir)

            if (fs.existsSync(outputPath)) {
                fs.rmSync(outputPath, { recursive: true })
            }
            fs.mkdirSync(outputPath)
            if (!fs.existsSync(tmpPath)) {
                fs.mkdirSync(tmpPath)
            }
            const diving = async () => Promise.resolve((process.chdir(tmpPath), true))
            const surfacing = async () => Promise.resolve((process.chdir(projectPath), true))

            const HERES_THE_PLAN = [
                surfacing,
                () => exporting(devDeps),
                () => building(directory),
                () => rolling(tempDir),
                () => copying(handler, tempDir, target),
                () => touching(tempDir),
                diving,
                () => zipping(outFile, outDir),
                surfacing,
                () => housekeeping(tempDir, 'dist', 'requirements.txt'),
            ]

            // @ts-ignore
            const success = await HERES_THE_PLAN.reduce(async (acc, cur) => {
                const a = await acc
                const result = await cur()
                const name = result.name || cur.name
                if (!result) {
                    console.error('Failed function:', name)
                    return a
                }
                return [...a, result]
            }, Promise.resolve([]))

            // @ts-ignore
            const completed = (success.filter((x) => x).length / HERES_THE_PLAN.length) * 100
            if (completed === 100) {
                console.log(`\n==== Zipped: ...${outFile.split('/').slice(-3).join('/')} ====\n`)
            } else {
                console.log(`\n==== FAILED: ${completed}% ====\n`)
            }
        })
    await program.parse(process.argv)
}

main()
