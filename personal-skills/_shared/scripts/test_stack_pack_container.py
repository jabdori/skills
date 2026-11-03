"""일회용 연습 컨테이너에서 설치 시간·파일 배치·오프라인 동작을 측정합니다."""
import argparse
import json
from pathlib import Path
import subprocess
import time
import uuid

SHARED = Path(__file__).resolve().parents[1]
GO_FAILURE = 'Go 설치 실패 — 이미 설치된 Node.js 22나 Python 3.11 스택을 고려'
EXPECTED = {
    'common': ['find-skills'],
    'go': ['find-skills', 'use-modern-go'],
    'react': ['find-skills', 'shadcn', 'vercel-composition-patterns',
              'vercel-react-best-practices', 'web-design-guidelines'],
    'python': ['find-skills'],
    'node': ['find-skills'],
}
INSPECT = r'''
import json,os,re,subprocess
from pathlib import Path
home=Path('/home/user');root=home/'.agents/skills';names=[]
for folder in sorted(root.iterdir()) if root.exists() else []:
    skill=folder/'SKILL.md';assert skill.is_file(),str(skill)
    text=skill.read_text();front=text.split('---',2)[1]
    assert re.search(r'^name:\s*'+re.escape(folder.name)+r'\s*$',front,re.M),str(skill)
    assert re.search(r'^description:\s*\S',front,re.M),str(skill)
    assert skill.stat().st_uid==1001,str(skill)
    names.append(folder.name)
assert not (home/'.codex/config.toml').exists(),'Codex 설정이 만들어졌습니다'
assert os.getuid()==1001
print(json.dumps({'skills':names,'codex':subprocess.check_output(['codex','--version'],text=True).strip(),'uid':os.getuid(),'config_untouched':True}))
'''


def command(args, **kwargs):
    return subprocess.run(args, text=True, capture_output=True, timeout=240, **kwargs)


def create(image, network):
    name = 'stack-pack-test-'+uuid.uuid4().hex[:12]
    args = ['docker', 'run', '--detach', '--rm', '--name', name, '--network', network,
            '--user', '1001:1001', '--workdir', '/home/user', '--env', 'HOME=/home/user',
            '--mount', 'type=bind,source='+str(SHARED)+',target=/pack,readonly',
            '--entrypoint', '/bin/sh', image, '-c', 'exec sleep infinity']
    result = command(args)
    if result.returncode:
        raise RuntimeError(result.stderr)
    return name


def inspect(name):
    result = command(['docker', 'exec', name, 'python3', '-B', '-c', INSPECT])
    if result.returncode:
        raise RuntimeError(result.stderr)
    return json.loads(result.stdout)


def install(name, pack, offline=False):
    args = ['docker', 'exec', name, 'bash', '/pack/scripts/install-stack-pack.sh', pack]
    if offline:
        args.append('--offline')
    started = time.monotonic()
    result = command(args)
    elapsed = time.monotonic()-started
    return dict(seconds=round(elapsed, 3), exit_code=result.returncode,
                stdout=result.stdout, stderr=result.stderr)


def cold(image, pack, mode, offline, expected_success):
    network = 'bridge' if mode == 'online' else 'none'
    name = create(image, network)
    try:
        before = inspect(name)
        assert not before['skills'], before
        result = install(name, pack, offline)
        after = inspect(name)
        if pack == 'go' and mode == 'online' and result['exit_code'] != 0:
            expected_success = False
            result['expected_fallback'] = True
        assert (result['exit_code'] == 0) == expected_success, result
        assert after['skills'] == (sorted(EXPECTED[pack]) if expected_success else []), after
        if pack == 'go' and not expected_success:
            assert result['stdout'] == '' and result['stderr'] == GO_FAILURE+'\n', result
        if pack == 'go' and expected_success:
            smoke = command(['docker', 'exec', name, '/bin/sh', '-c',
                'set -eu; export PATH="$HOME/.local/go/bin:$PATH"; export GOTOOLCHAIN=local; '
                'go version; go tool compile -V=full; '
                'sh "$HOME/.agents/skills/use-modern-go/scripts/run-tool.sh" --version; '
                'sh "$HOME/.agents/skills/use-modern-go/scripts/run-tool.sh" list --go-version 1.27'])
            assert smoke.returncode == 0 and 'go1.27.3' in smoke.stdout and 'v0.1.1' in smoke.stdout, smoke.stderr
            result['go_runtime_and_guidelines_ok'] = True
        return {'pack': pack, 'mode': 'cold-'+mode+('-explicit' if offline else '-auto'),
                **result, 'placement': after}
    finally:
        command(['docker', 'rm', '--force', name])


def warm_react(image):
    name = create(image, 'bridge')
    try:
        initial = install(name, 'react')
        assert initial['exit_code'] == 0, initial
        assert inspect(name)['skills'] == sorted(EXPECTED['react'])
        detached = command(['docker', 'network', 'disconnect', 'bridge', name])
        assert detached.returncode == 0, detached.stderr
        removed = command(['docker', 'exec', name, 'python3', '-B', '-c',
                           "import shutil;shutil.rmtree('/home/user/.agents/skills')"])
        assert removed.returncode == 0, removed.stderr
        result = install(name, 'react', True)
        after = inspect(name)
        assert result['exit_code'] == 0 and after['skills'] == sorted(EXPECTED['react']), result
        return {'pack': 'react', 'mode': 'warm-offline-reinstall', **result, 'placement': after}
    finally:
        command(['docker', 'rm', '--force', name])


def warm_go(image):
    name = create(image, 'bridge')
    try:
        initial = install(name, 'go')
        if initial['exit_code'] != 0:
            assert initial['stdout'] == '' and initial['stderr'] == GO_FAILURE+'\n', initial
            return {'pack': 'go', 'mode': 'warm-offline-prerequisite-failed', **initial,
                    'expected_fallback': True, 'placement': inspect(name)}
        detached = command(['docker', 'network', 'disconnect', 'bridge', name])
        assert detached.returncode == 0, detached.stderr
        removed = command(['docker', 'exec', name, 'python3', '-B', '-c',
                           "import shutil;shutil.rmtree('/home/user/.agents/skills');shutil.rmtree('/home/user/.local/go')"])
        assert removed.returncode == 0, removed.stderr
        result = install(name, 'go', True)
        after = inspect(name)
        assert result['exit_code'] == 0 and after['skills'] == sorted(EXPECTED['go']), result
        smoke = command(['docker', 'exec', name, '/bin/sh', '-c',
                         'set -eu; "$HOME/.local/go/bin/go" version; '
                         'sh "$HOME/.agents/skills/use-modern-go/scripts/run-tool.sh" --version'])
        assert smoke.returncode == 0, smoke.stderr
        return {'pack': 'go', 'mode': 'warm-offline-reinstall', **result, 'placement': after}
    finally:
        command(['docker', 'rm', '--force', name])


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--image', default='cofa-practice:local')
    parser.add_argument('--output', type=Path)
    args = parser.parse_args()
    image = command(['docker', 'image', 'inspect', args.image, '--format', '{{.Id}} {{.Architecture}}'])
    if image.returncode:
        raise SystemExit(image.stderr)
    report = {'image': args.image, 'image_id_and_arch': image.stdout.strip(),
              'recognition_check': '공식 사용자 발견 경로의 SKILL.md와 앞부분 이름·설명·소유자만 확인; 모델 호출 없음',
              'results': []}
    for pack in EXPECTED:
        for mode in ('online', 'offline'):
            result = cold(args.image, pack, mode, mode == 'offline', not (pack in ('go', 'react') and mode == 'offline'))
            report['results'].append(result)
            print(json.dumps({k:result[k] for k in ('pack','mode','seconds','exit_code')}, ensure_ascii=False), flush=True)
    for pack in ('go', 'react'):
        result = cold(args.image, pack, 'offline', False, False)
        report['results'].append(result)
        print(json.dumps({k:result[k] for k in ('pack','mode','seconds','exit_code')}, ensure_ascii=False), flush=True)
    for probe in (warm_go, warm_react):
        result = probe(args.image)
        report['results'].append(result)
        print(json.dumps({k:result[k] for k in ('pack','mode','seconds','exit_code')}, ensure_ascii=False), flush=True)
    if args.output:
        args.output.write_text(json.dumps(report, ensure_ascii=False, indent=2)+'\n')
    else:
        print(json.dumps(report, ensure_ascii=False, indent=2))


if __name__ == '__main__':
    main()
