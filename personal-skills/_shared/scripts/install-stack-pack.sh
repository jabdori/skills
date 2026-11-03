#!/usr/bin/env bash
set -euo pipefail
umask 077

if ! command -v python3 >/dev/null 2>&1; then
  printf '설치기에 Python 3가 필요합니다. 응시 환경의 python3를 먼저 확인해 주세요.\n' >&2
  exit 1
fi
shared_dir="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)"
exec python3 -B - "$shared_dir" "$@" <<'PY'
import argparse
import hashlib
import json
import os
from pathlib import Path
import platform
import re
import shutil
import subprocess
import sys
import tarfile
import tempfile
import time
import urllib.request

SHARED = Path(sys.argv[1])
VENDOR = SHARED / 'vendor'
GO_FAILURE = 'Go 설치 실패 — 이미 설치된 Node.js 22나 Python 3.11 스택을 고려'


def require(ok, message):
    if not ok:
        raise ValueError(message)


def sha256(path):
    digest = hashlib.sha256()
    with path.open('rb') as source:
        for block in iter(lambda: source.read(1024 * 1024), b''):
            digest.update(block)
    return digest.hexdigest()


def file_map(directory):
    require(directory.is_dir() and not directory.is_symlink(), '스킬 폴더가 없거나 심볼릭 링크입니다: ' + str(directory))
    result = {}
    for path in sorted(directory.rglob('*')):
        require(not path.is_symlink(), '스킬 안의 심볼릭 링크는 설치하지 않습니다: ' + str(path))
        if path.is_file():
            result[path.relative_to(directory).as_posix()] = sha256(path)
    return result


def verify_files(directory, files):
    for relative, expected in files.items():
        path = directory / relative
        require(not Path(relative).is_absolute() and '..' not in Path(relative).parts,
                '원본 파일 경로 오류: ' + relative)
        require(path.is_file() and not path.is_symlink() and sha256(path) == expected,
                'SHA-256 불일치 또는 파일 누락: ' + str(path))


def copy_files(source, destination, files):
    verify_files(source, files)
    destination.mkdir(parents=True)
    for relative in files:
        target = destination / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source / relative, target)


def check_skill(directory, name):
    text = (directory / 'SKILL.md').read_text(encoding='utf-8')
    front = text.split('---', 2)
    require(len(front) == 3 and not front[0].strip(), name + ': SKILL.md 앞부분 형식 오류')
    found = re.search(r'^name:\s*[\'\"]?([^\n\'\"]+)', front[1], re.M)
    require(found and found[1].strip() == name, name + ': 스킬 이름과 설치 폴더가 다릅니다')
    require(re.search(r'^description:\s*\S', front[1], re.M), name + ': 스킬 설명 누락')


def remote_skills(manifest, cache, offline):
    spec = manifest['remote']
    commit = spec['commit']
    require(re.fullmatch(r'[0-9a-f]{40}', commit), '원격 고정 커밋 형식 오류')
    target = cache / 'remote' / commit
    marker = target / 'snapshot.json'
    if marker.is_file():
        recorded = json.loads(marker.read_text())
        require(recorded['repo'] == spec['repo'] and recorded['commit'] == commit,
                '원격 스킬 캐시의 출처가 다릅니다')
        sources = []
        for name in spec['skills']:
            files = recorded['skills'][name]
            verify_files(target / name, files)
            require(file_map(target / name) == files, '원격 스킬 캐시에 추가·변경된 파일이 있습니다: ' + name)
            check_skill(target / name, name)
            sources.append((name, target / name, files))
        return sources
    require(not offline, '오프라인: React 원격 스킬 캐시가 없습니다. 온라인에서 react 팩을 한 번 설치해야 합니다.')
    require(shutil.which('git'), 'React 원격 스킬 설치에는 git이 필요합니다')
    target.parent.mkdir(parents=True, exist_ok=True)
    env = {**os.environ, 'GIT_TERMINAL_PROMPT': '0', 'GIT_CONFIG_GLOBAL': os.devnull,
           'GIT_CONFIG_NOSYSTEM': '1'}
    with tempfile.TemporaryDirectory(prefix='.fetch-', dir=target.parent) as temporary:
        temporary = Path(temporary)
        checkout = temporary / 'repo'
        def git(*args):
            command = ['git', '-c', 'core.hooksPath=' + os.devnull,
                       '-c', 'http.lowSpeedLimit=1', '-c', 'http.lowSpeedTime=15',
                       '-C', str(checkout), *args]
            result = subprocess.run(command, env=env, capture_output=True, text=True, timeout=90)
            require(result.returncode == 0, '고정 커밋 다운로드 실패: ' + spec['repo'] + '@' + commit[:12])
            return result.stdout.strip()
        checkout.mkdir()
        git('init', '--quiet')
        git('remote', 'add', 'origin', 'https://github.com/' + spec['repo'] + '.git')
        git('fetch', '--depth=1', '--no-tags', 'origin', commit)
        git('checkout', '--quiet', '--detach', 'FETCH_HEAD')
        require(git('rev-parse', 'HEAD') == commit, '다운로드한 Git 커밋이 다릅니다')
        snapshot = temporary / 'snapshot'
        snapshot.mkdir()
        recorded = {'repo': spec['repo'], 'commit': commit, 'skills': {}}
        for name, source_path in spec['skills'].items():
            source = checkout / source_path
            check_skill(source, name)
            files = file_map(source)
            copy_files(source, snapshot / name, files)
            recorded['skills'][name] = files
        (snapshot / 'snapshot.json').write_text(json.dumps(recorded, indent=2) + '\n')
        require(not target.exists(), '원격 캐시가 이미 생겼습니다. 다시 실행해 주세요.')
        snapshot.rename(target)
    return remote_skills(manifest, cache, True)


def go_platform():
    arch = {'aarch64': 'arm64', 'arm64': 'arm64', 'x86_64': 'amd64', 'amd64': 'amd64'}.get(platform.machine())
    require(platform.system() == 'Linux' and arch, 'Go 팩은 Linux amd64/arm64 응시 환경을 지원합니다')
    return 'linux-' + arch


def prepare_go(manifest, home, cache, offline, temporary):
    spec = manifest['go']
    variant = go_platform()
    archive = spec['archives'][variant]
    destination = home / '.local' / 'go'
    marker = destination / '.stack-pack.json'
    env = {**os.environ, 'GOTOOLCHAIN': 'local', 'GOWORK': 'off'}
    if destination.exists() or destination.is_symlink():
        require(not destination.is_symlink() and marker.is_file(),
                '기존 ~/.local/go는 덮어쓰지 않습니다. 별도로 보관한 뒤 다시 설치해 주세요.')
        recorded = json.loads(marker.read_text())
        require(recorded['archiveSha256'] == archive['sha256'] and
                recorded['goBinarySha256'] == sha256(destination / 'bin/go'),
                '기존 Go 설치의 버전 또는 실행 파일이 다릅니다. 기존 설치를 보관한 뒤 다시 설치해 주세요.')
        result = subprocess.check_output([str(destination / 'bin/go'), 'version'], env=env, cwd=temporary, text=True)
        require(result.split()[2] == spec['version'], '기존 Go 버전이 다릅니다')
        return None, destination
    destination.parent.mkdir(parents=True, exist_ok=True)
    require(os.access(destination.parent, os.W_OK | os.X_OK), 'Go 설치 폴더에 쓸 수 없습니다')
    cached = cache / 'downloads' / archive['filename']
    archive_path = cached
    if not archive_path.is_file():
        require(not offline, '오프라인: 고정 Go 공식 압축 파일이 없습니다')
        cached.parent.mkdir(parents=True, exist_ok=True)
        download = temporary / archive['filename']
        request = urllib.request.Request('https://go.dev/dl/' + archive['filename'],
                                         headers={'User-Agent': 'personal-skills-stack-pack'})
        with urllib.request.urlopen(request, timeout=90) as response, download.open('wb') as output:
            shutil.copyfileobj(response, output)
        require(sha256(download) == archive['sha256'], 'Go 공식 tarball SHA-256 불일치')
        shutil.move(str(download), cached)
        archive_path = cached
    require(sha256(archive_path) == archive['sha256'], 'Go 공식 tarball SHA-256 불일치')
    stage = temporary / 'sdk'
    stage.mkdir()
    with tarfile.open(archive_path, 'r:gz') as bundle:
        members = bundle.getmembers()
        require(all(not Path(m.name).is_absolute() and '..' not in Path(m.name).parts and
                    Path(m.name).parts[0] == 'go' and (m.isfile() or m.isdir()) for m in members),
                'Go 압축 파일의 경로 또는 파일 종류 오류')
        bundle.extractall(stage, members=members)
    sdk = stage / 'go'
    result = subprocess.check_output([str(sdk / 'bin/go'), 'version'], env=env, cwd=temporary, text=True)
    require(result.split()[2] == spec['version'], '고정 Go 실행 버전이 다릅니다')
    (sdk / '.stack-pack.json').write_text(json.dumps({'version': spec['version'],
        'archiveSha256': archive['sha256'], 'goBinarySha256': sha256(sdk / 'bin/go')}) + '\n')
    return sdk, destination


def prepare_guidelines_cli(manifest, cache_home, temporary):
    spec = manifest['go']['guidelines_cli']
    variant = go_platform()
    binary = spec['binaries'][variant]
    source = VENDOR / binary['path']
    require(source.is_file() and sha256(source) == binary['sha256'], 'Go 지침 CLI SHA-256 불일치')
    verify_files(VENDOR, spec['licenses'])
    destination = cache_home / 'go-modern-guidelines' / spec['version']
    if destination.exists() or destination.is_symlink():
        require(not destination.is_symlink() and (destination / 'go-modern-guidelines').is_file() and
                sha256(destination / 'go-modern-guidelines') == binary['sha256'],
                '기존 Go 지침 CLI 캐시는 덮어쓰지 않습니다: ' + str(destination))
        return None, destination
    stage = temporary / 'guidelines-cli'
    stage.mkdir()
    shutil.copy2(source, stage / 'go-modern-guidelines')
    (stage / 'licenses').mkdir()
    for relative in spec['licenses']:
        shutil.copy2(VENDOR / relative, stage / 'licenses' / Path(relative).name)
    output = subprocess.check_output([str(stage / 'go-modern-guidelines'), '--version'], text=True).strip()
    require(output == spec['version'], '고정 Go 지침 CLI 버전이 다릅니다')
    return stage, destination


def main():
    parser = argparse.ArgumentParser(description='선택한 스택의 스킬·Go 런타임을 사용자 홈에 설치합니다.')
    parser.add_argument('packs', nargs='+', choices=('common', 'go', 'react', 'python', 'node'))
    parser.add_argument('--offline', action='store_true', help='네트워크를 사용하지 않고 동봉 파일·기존 캐시만 사용')
    args = parser.parse_args(sys.argv[2:])
    started = time.monotonic()
    packs = set(args.packs)
    require(os.environ.get('HOME'), '사용자 HOME이 필요합니다')
    home = Path(os.environ['HOME']).expanduser().absolute()
    cache_home = Path(os.environ.get('XDG_CACHE_HOME', str(home / '.cache'))).expanduser().absolute()
    cache = cache_home / 'stack-packs'
    skills = home / '.agents' / 'skills'
    manifest = json.loads((SHARED / 'stack-packs.lock.json').read_text())
    require(manifest['schema'] == 1, '지원하지 않는 고정 원본 목록입니다')
    if packs & {'node', 'react'}:
        require(shutil.which('node'), 'Node.js가 없습니다. 이 팩은 응시 환경에 준비된 Node.js를 사용합니다.')
        print(subprocess.check_output(['node', '--version'], text=True).strip())
    if 'python' in packs:
        print('Python ' + platform.python_version())
    wanted = {'find-skills'}
    if 'go' in packs:
        wanted.add('use-modern-go')
    if 'react' in packs:
        wanted.add('shadcn')
    payloads = []
    for spec in manifest['skills']:
        if spec['name'] in wanted:
            source = VENDOR / spec['vendor']
            verify_files(source, spec['files'])
            check_skill(source, spec['name'])
            payloads.append((spec['name'], source, spec['files']))
    if 'react' in packs:
        payloads.extend(remote_skills(manifest, cache, args.offline))
    for name, source, files in payloads:
        destination = skills / name
        if destination.exists() or destination.is_symlink():
            require(not destination.is_symlink() and file_map(destination) == files,
                    '기존 스킬과 내용이 달라 덮어쓰지 않습니다: ' + name)
    home.mkdir(parents=True, exist_ok=True)
    # 준비가 끝난 뒤에만 설치 경로로 옮겨 기존 스킬·런타임을 보존합니다.
    with tempfile.TemporaryDirectory(prefix='.stack-pack-', dir=home) as work:
        temporary = Path(work)
        staged = []
        for name, source, files in payloads:
            target = skills / name
            if not target.exists():
                stage = temporary / 'skills' / name
                copy_files(source, stage, files)
                check_skill(stage, name)
                staged.append((stage, target))
        if 'go' in packs:
            try:
                verify_files(VENDOR / 'go-toolchain', {'LICENSE': manifest['go']['license_sha256']})
                sdk, sdk_target = prepare_go(manifest, home, cache, args.offline, temporary)
                cli, cli_target = prepare_guidelines_cli(manifest, cache_home, temporary)
            except (ValueError, OSError, KeyError, subprocess.SubprocessError, tarfile.TarError):
                raise ValueError(GO_FAILURE) from None
            staged += [(s, d) for s, d in ((sdk, sdk_target), (cli, cli_target)) if s is not None]
        for source, target in staged:
            target.parent.mkdir(parents=True, exist_ok=True)
            require(not target.exists() and not target.is_symlink(), '설치 대상이 이미 생겼습니다: ' + str(target))
            source.rename(target)
    print('스킬 설치 위치: ' + str(skills))
    print('스킬: ' + ', '.join(sorted(name for name, _, _ in payloads)))
    if 'go' in packs:
        print('Go: ' + manifest['go']['version'] + ' → ' + str(home / '.local/go'))
        print('현재 셸에서 실행: export PATH="$HOME/.local/go/bin:$PATH"')
        print('도구 체인 자동 변경 방지: export GOTOOLCHAIN=local')
    print(f'설치 완료: {", ".join(sorted(packs))} ({time.monotonic()-started:.3f}초)')


try:
    main()
except (ValueError, OSError, KeyError, subprocess.SubprocessError, tarfile.TarError) as error:
    print(GO_FAILURE if str(error) == GO_FAILURE else '설치 실패: ' + str(error), file=sys.stderr)
    sys.exit(1)
PY
