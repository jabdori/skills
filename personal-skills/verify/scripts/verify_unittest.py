"""기존 unittest를 실행하고 수집 누락·전체 생략을 성공과 구분합니다."""

import argparse
import json
from pathlib import Path
import sys
import unittest


class EvidenceResult(unittest.TextTestResult):
    successes = 0

    def addSuccess(self, test):
        super().addSuccess(test)
        self.successes += 1


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('-s', '--start-directory', default='.')
    parser.add_argument('-p', '--pattern', default='test*.py')
    parser.add_argument('-t', '--top-level-directory')
    args = parser.parse_args()
    # 프로젝트 모듈 탐색은 프로젝트 루트에서 실행하는 unittest와 맞춥니다.
    sys.path.insert(0, str(Path.cwd()))
    evidence = {
        'cwd': str(Path.cwd()),
        'start_directory': str(Path(args.start_directory).resolve()),
        'pattern': args.pattern,
        'top_level_directory': args.top_level_directory,
    }
    try:
        suite = unittest.TestLoader().discover(
            args.start_directory, args.pattern, args.top_level_directory
        )
    except (ImportError, OSError) as error:
        evidence.update(status='unverified', reason='discovery_error', detail=str(error))
        print(json.dumps(evidence, ensure_ascii=False))
        return 2

    evidence['collected'] = suite.countTestCases()
    result = unittest.TextTestRunner(
        verbosity=2, buffer=True, resultclass=EvidenceResult
    ).run(suite)
    evidence.update(
        run=result.testsRun,
        successes=result.successes,
        failures=len(result.failures),
        errors=len(result.errors),
        skipped=len(result.skipped),
        expected_failures=len(result.expectedFailures),
        unexpected_successes=len(result.unexpectedSuccesses),
    )
    # 실패 판정이 먼저입니다. 일부 오류가 있어도 생략으로 덮지 않습니다.
    if not result.wasSuccessful():
        evidence['status'], code = 'failed', 1
    elif (result.successes == 0 or result.shouldStop
          or result.testsRun < evidence['collected']):
        evidence['status'], code = 'unverified', 2
    else:
        evidence['status'] = (
            'passed_with_exceptions'
            if result.skipped or result.expectedFailures else 'passed'
        )
        code = 0
    print(json.dumps(evidence, ensure_ascii=False))
    return code


if __name__ == '__main__':
    raise SystemExit(main())
