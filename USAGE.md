# CoT Agent System - 사용법

CoT Agent System은 Chain of Thought 추론을 기반으로 복잡한 작업을 관리 가능한 todo로 분해하고 실행하는 에이전트 시스템입니다.

## 🚀 빠른 시작

### 1. 환경 설정

```bash
# 저장소 클론 후 이동
cd cot-agent-system

# 자동 설정 스크립트 실행
./setup.sh
```

### 2. API 키 설정 (선택사항)

LLM 기능을 사용하려면 `.env` 파일에 API 키를 설정하세요:

```bash
# .env 파일 편집
nano .env

# OpenAI API 키 추가
OPENAI_API_KEY=your_openai_api_key_here
```

### 3. 예제 실행

```bash
# 가상환경 활성화
source .venv/bin/activate

# API 키 없이 실행 가능한 예제
cot-agent example

# 또는 직접 실행
python run.py example
```

## 📋 CLI 사용법

### 기본 명령어

```bash
# 도움말 보기
cot-agent --help

# 버전 확인
cot-agent --version
```

### 쿼리 처리

```bash
# 단일 쿼리 처리 (API 키 필요)
cot-agent process "오늘 하루 일정을 효율적으로 계획해줘"

# 대화형 모드
cot-agent process --interactive

# 설정 파일 사용
cot-agent process --config-file config.json "내 질문"

# 결과를 파일로 저장
cot-agent process --save-result result.json "내 질문"
```

### 고급 옵션

```bash
# 모델 및 매개변수 커스터마이징
cot-agent process \
  --model gpt-4 \
  --temperature 0.8 \
  --max-tokens 1500 \
  --max-iterations 10 \
  --thinking-depth 5 \
  "복잡한 프로젝트 계획을 세워줘"
```

### 설정 파일 생성

```bash
# 기본 설정 파일 생성
cot-agent init-config

# 커스텀 위치에 생성
cot-agent init-config --output my-config.json
```

## 🐍 Python에서 사용

### 기본 사용법

```python
import asyncio
from cot_agent_system import CoTAgent, AgentConfig

async def main():
    # 에이전트 설정
    config = AgentConfig(
        model_name="gpt-3.5-turbo",
        temperature=0.7,
        max_iterations=5
    )
    
    # 에이전트 초기화
    agent = CoTAgent(config=config)
    
    # 쿼리 처리
    result = await agent.process_query("주말 여행 계획을 세워줘")
    
    # 결과 확인
    print(f"처리 완료: {result['process'].process_id}")
    print(f"생성된 Todo 수: {len(result['process'].todos)}")
    
    # Todo 요약 보기
    summary = agent.get_todos_summary()
    for todo in summary['completed_todos']:
        print(f"✅ {todo['content']}")

if __name__ == "__main__":
    asyncio.run(main())
```

### 수동 피드백 추가

```python
# 특정 todo에 피드백 추가
feedback_result = await agent.add_manual_feedback(
    todo_id="todo-id-here",
    feedback="이 작업은 잘 완료되었지만 더 자세한 설명이 필요합니다."
)
```

## 🔧 개발 환경

### 테스트 실행

```bash
# 모든 테스트 실행
python -m pytest

# 상세 출력과 함께 실행
python -m pytest -v

# 특정 테스트 파일 실행
python -m pytest tests/test_models.py
```

### 코드 포맷팅

```bash
# 코드 포맷팅
black src/ tests/ examples/

# import 정렬
isort src/ tests/ examples/

# 타입 검사
mypy src/
```

## 📁 프로젝트 구조

```
cot-agent-system/
├── src/cot_agent_system/          # 메인 패키지
│   ├── __init__.py               # 패키지 초기화
│   ├── agent.py                  # CoTAgent 클래스
│   ├── todo_manager.py           # TodoManager 클래스
│   ├── cot_engine.py            # CoTEngine 클래스
│   ├── models.py                # 데이터 모델
│   └── cli.py                   # CLI 인터페이스
├── tests/                       # 테스트 파일
├── examples/                    # 사용 예제
├── setup.sh                     # 환경 설정 스크립트
├── run.py                       # 직접 실행 스크립트
├── requirements.txt             # 의존성 목록
├── pyproject.toml              # 프로젝트 설정
└── .env                        # 환경 변수 (생성됨)
```

## 🎯 주요 기능

- **Chain of Thought 추론**: 복잡한 쿼리를 단계별로 분석
- **자동 Todo 생성**: CoT 단계를 기반으로 실행 가능한 todo 생성
- **의존성 관리**: Todo 간 의존성 자동 추적
- **피드백 루프**: 실행 결과를 통한 지속적 개선
- **CLI 및 Python API**: 명령줄과 Python 코드 양방향 지원
- **설정 가능**: 모델, 매개변수 등 다양한 옵션 제공

## 🔍 문제 해결

### 일반적인 문제들

1. **Import 오류**
   ```bash
   # 가상환경 활성화 확인
   source .venv/bin/activate
   
   # 패키지 재설치
   pip install -e .
   ```

2. **API 키 오류**
   ```bash
   # .env 파일 확인
   cat .env
   
   # 환경변수 확인
   echo $OPENAI_API_KEY
   ```

3. **Python 버전 오류**
   ```bash
   # Python 버전 확인 (3.13+ 필요)
   python --version
   ```

## 📞 지원

- 이슈나 버그는 GitHub Issues에 보고해주세요
- 예제는 `examples/` 디렉토리를 참고하세요
- 추가 문서는 README.md를 확인하세요