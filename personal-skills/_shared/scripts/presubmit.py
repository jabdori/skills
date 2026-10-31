#!/usr/bin/env python3
"""Git 작업 폴더의 제출 후보를 읽기 전용으로 점검한다."""

import argparse
import os
import re
import shlex
import subprocess
from pathlib import Path


CODE_EXTENSIONS = {'.py', '.js', '.mjs', '.cjs', '.ts', '.tsx', '.jsx', '.go', '.rs', '.java', '.rb', '.sh', '.html', '.css'}
LARGE_BYTES = 5 * 1024 * 1024


def git(root, *args):
    return subprocess.run(['git', '--no-optional-locks', *args], cwd=root, capture_output=True)


def base_commit(root, ref):
    if ref is None:
        result = git(root, 'rev-list', '--first-parent', '--max-parents=0', 'HEAD')
        commits = result.stdout.splitlines()
        if result.returncode or len(commits) != 1:
            raise ValueError('과제 시작 상태의 최초 커밋을 찾지 못했습니다. --base로 기준을 지정하세요.')
        return commits[0].decode('ascii')
    result = git(root, 'rev-parse', '--verify', '--end-of-options', f'{ref}^{{commit}}')
    if result.returncode:
        raise ValueError(f'기준 커밋을 찾지 못했습니다: {ref}')
    return result.stdout.splitlines()[0].decode('ascii')


def changes(root, base):
    result = git(root, 'diff', '--no-renames', '--name-status', '-z', base, '--')
    if result.returncode:
        raise ValueError('기준 커밋과 작업 트리의 차이를 읽지 못했습니다.')
    entries = result.stdout.split(b'\0')
    found = []
    for status, path in zip(entries[::2], entries[1::2]):
        kind = '삭제' if status.startswith(b'D') else '신규' if status.startswith(b'A') else '수정'
        found.append((kind, os.fsdecode(path)))
    untracked = git(root, 'ls-files', '--others', '--exclude-standard', '-z')
    if untracked.returncode:
        raise ValueError('미추적 파일을 읽지 못했습니다.')
    found.extend(('신규', os.fsdecode(path)) for path in untracked.stdout.split(b'\0') if path)
    return sorted(found, key=lambda item: item[1])


def protect_path(value):
    value = value.strip().strip('`')
    path = Path(value)
    if not value or path.is_absolute() or '..' in path.parts:
        raise ValueError(f'수정 금지 파일 경로가 작업 폴더 밖이거나 비어 있습니다: {value}')
    return path.as_posix()


def project_protected(root):
    agents = root / 'AGENTS.md'
    if not agents.is_file():
        return set()
    try:
        lines = agents.read_text(encoding='utf-8').splitlines()
    except (OSError, UnicodeError) as error:
        raise ValueError('AGENTS.md를 읽지 못했습니다.') from error
    protected = set()
    in_project = False
    list_items = False
    for line in lines:
        if line.startswith('## '):
            in_project = line.strip() == '## 이 프로젝트'
            list_items = False
            continue
        if not in_project:
            continue
        match = re.match(r'^\s*(?:[-*]\s*)?수정 금지(?: 파일| 목록)?\s*:\s*(.*)$', line)
        if match:
            value = match.group(1)
            list_items = not value.strip()
        elif list_items and re.match(r'^\s{2,}[-*]\s+', line):
            value = re.sub(r'^\s*[-*]\s+', '', line)
        else:
            list_items = False
            continue
        entries = re.findall(r'`([^`]+)`', value) or value.split(',')
        protected.update(protect_path(entry) for entry in entries if entry.strip() and entry.strip() not in {'없음', '미확인'})
    return protected


def protection_warnings(root, base, changed, extra):
    protected = {'README.md'} | project_protected(root) | {protect_path(value) for value in extra}
    warnings = set()
    for _, name in changed:
        if name not in protected:
            continue
        existing = git(root, 'cat-file', '-e', f'{base}:{name}').returncode == 0
        hint = (f'git checkout {base} -- {shlex.quote(name)}' if existing
                else '기준 커밋에 파일이 없어 직접 확인이 필요합니다')
        warnings.add(f'수정 금지 파일 변경: {name} (되돌리기 안내: {hint})')
    return warnings


def commit_warnings(root, base):
    warnings = set()
    status = git(root, 'status', '--porcelain=v1', '-z', '--untracked-files=all')
    if status.returncode:
        raise ValueError('커밋 안 된 변경을 읽지 못했습니다.')
    if status.stdout:
        warnings.add('커밋 안 된 변경이 있습니다.')
    history = git(root, 'rev-list', '--reverse', f'{base}..HEAD')
    if history.returncode:
        raise ValueError('시작 커밋 이후 이력을 읽지 못했습니다.')
    commits = history.stdout.splitlines()
    if not commits:
        warnings.add('검증된 단위 커밋 없음: 시작 커밋 뒤의 커밋이 없습니다.')
    for sha in commits:
        subject = git(root, 'log', '-1', '--format=%s', sha.decode('ascii'))
        if subject.returncode:
            raise ValueError('커밋 메시지를 읽지 못했습니다.')
        message = subject.stdout.decode('utf-8', errors='replace').strip()
        match = re.fullmatch(r'[a-z][a-z0-9-]*(?:\([^()\n]+\))?!?: (.+)', message)
        if not match or not re.search(r'[가-힣]', match.group(1)):
            warnings.add(f'커밋 메시지 형식 또는 한국어 요약 오류: {sha[:12].decode()} {message}')
    return warnings


def file_warnings(root, changed):
    warnings = set()
    for kind, name in changed:
        path = root / name
        if 'node_modules' in Path(name).parts and kind != '삭제':
            warnings.add(f'새로 추가된 node_modules: {name}')
        if kind != '삭제' and path.is_file() and not path.is_symlink() and path.stat().st_size > LARGE_BYTES:
            warnings.add(f'큰 파일(5 MiB 초과): {name}')

    for current, dirs, files in os.walk(root):
        dirs[:] = [name for name in dirs if name not in {'.git', '.agents', 'node_modules', '.venv'}]
        base = Path(current)
        if base.name == '__pycache__':
            warnings.add(f'생성물: {base.relative_to(root)}/')
        for name in files:
            rel = (base / name).relative_to(root)
            low = name.lower()
            if low.endswith('.pyc'):
                warnings.add(f'생성물: {rel}')
            if (low == '.env' or low.startswith('.env.') and low not in {'.env.example', '.env.sample', '.env.template'}
                    or low in {'auth.json', 'id_rsa', 'id_ed25519'} or low.endswith(('.pem', '.key', '.p12', '.pfx'))):
                warnings.add(f'민감 파일 가능성: {rel}')
            if low == '.ds_store' or low.endswith(('.log', '.tmp', '.temp', '.swp', '.bak')) or low.endswith('~'):
                warnings.add(f'로그·임시 파일: {rel}')
    return warnings


def document_warnings(root, changed, document):
    if document is None:
        document = (root / 'DECISIONS.md').resolve()
        if not document.exists():
            return set(), None
    else:
        document = (root / document).resolve()
    if not document.is_relative_to(root):
        return {'결정 문서는 작업 폴더 안에 있어야 합니다.'}, None
    if not document.is_file():
        return {f'결정 문서를 찾을 수 없습니다: {document.relative_to(root)}'}, None
    try:
        content = document.read_text(encoding='utf-8')
    except (OSError, UnicodeError):
        return {f'결정 문서를 읽을 수 없습니다: {document.relative_to(root)}'}, None
    code_files = [name for _, name in changed if Path(name).suffix.lower() in CODE_EXTENSIONS]
    return ({f'결정 문서에 언급되지 않은 코드: {name}' for name in code_files
             if Path(name).name not in content}, len(code_files))


def run_test(root, command):
    env = dict(os.environ, PYTHONDONTWRITEBYTECODE='1')
    print(f'테스트: {command}')
    result = subprocess.run(command, shell=True, cwd=root, env=env, stdout=subprocess.PIPE,
                            stderr=subprocess.STDOUT)
    output = result.stdout.decode('utf-8', errors='replace')
    tail = '\n'.join(output.splitlines()[-20:])[-2000:]
    if tail:
        print(tail)
    print(f'test exit {result.returncode}')
    return result.returncode != 0


def main():
    parser = argparse.ArgumentParser(description='제출 전 Git 변경·생성물·결정 문서를 읽기 전용으로 확인합니다.')
    parser.add_argument('--test', help='실행할 검사 명령. 검사 자체의 파일 변경은 막지 않습니다.')
    parser.add_argument('--decisions', type=Path, help='결정 문서 경로. 기본값은 존재하는 DECISIONS.md입니다.')
    parser.add_argument('--base', help='비교 기준 커밋. 기본값은 현재 이력의 최초 커밋입니다.')
    parser.add_argument('--protect', action='append', default=[], metavar='FILE', help='수정 금지 파일(반복 지정 가능). README.md는 기본 보호합니다.')
    args = parser.parse_args()
    current = Path.cwd()
    result = git(current, 'rev-parse', '--show-toplevel')
    if result.returncode:
        print('Git 작업 폴더가 아닙니다.')
        return 1
    root = Path(os.fsdecode(result.stdout.strip())).resolve()
    try:
        base = base_commit(root, args.base)
        test_failed = run_test(root, args.test) if args.test else False
        changed = changes(root, base)
        protected_issues = protection_warnings(root, base, changed, args.protect)
        commit_issues = commit_warnings(root, base)
    except ValueError as error:
        print(error)
        return 1

    print(f'기준: {base[:12]} ({"최초 커밋" if args.base is None else "--base"})')
    counts = {kind: sum(item[0] == kind for item in changed) for kind in ('수정', '신규', '삭제')}
    print(f"변경: 수정 {counts['수정']} · 신규 {counts['신규']} · 삭제 {counts['삭제']}")
    for kind, name in changed:
        print(f'  {kind} {name}')

    document_issues, checked = document_warnings(root, changed, args.decisions)
    if checked is not None:
        print(f'결정 문서 대조: 코드 {checked}개')
    warnings = file_warnings(root, changed) | document_issues | protected_issues | commit_issues
    for warning in sorted(warnings):
        print(f'주의: {warning}')
    print('결과: 점검 필요' if warnings or test_failed else '결과: 추가 경고 없음')
    return 1 if warnings or test_failed else 0


if __name__ == '__main__':
    raise SystemExit(main())
