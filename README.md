# Fitting AI

무신사 AX 인재전쟁 2026 — 온라인 쇼핑몰 **가상 피팅** Codex 플러그인.

## 문제

온라인 쇼핑몰(무신사 등)에서는 옷을 직접 입어볼 수 없어 구매 결정이 어렵습니다.

## 해결

사용자 사진과 옷 사진을 [Replicate](https://replicate.com/cuuupid/idm-vton) `cuuupid/idm-vton` API로 합성해 가상 피팅 결과를 보여줍니다. 모델은 로컬에서 실행하지 않고 Replicate API만 호출합니다.

## 프로젝트 구조

```
AX-Hackerton-AI Fitting Plugin/
├── .agents/plugins/marketplace.json
├── README.md
├── logs/
│   ├── save_log.py
│   └── cursor/ …
└── src/                         # Codex 플러그인 루트
    ├── .codex-plugin/plugin.json
    ├── .env                     # REPLICATE_API_TOKEN (git 제외)
    ├── .env.example
    ├── run.ps1
    ├── skills/fitting-ai/SKILL.md
    ├── scripts/
    └── app/
```



## Codex에서 실행



### 1. 사전 준비

- Python 3.10+ 설치

### 2. 플러그인 설치

1. 플러그인 디렉터리를 연다.
  - Codex 앱: **Plugins**
  - Codex CLI: `codex /plugins`
2. 마켓플레이스 **Fitting AI** (`fitting-ai-local`)를 선택한다.
3. **fitting-ai** 플러그인을 **Install**한다.

### 3. 플러그인 사용

새 스레드를 연 뒤 아래처럼 요청한다.

```
@fitting-ai 내 사진에 옷 입혀보기
```

또는

```
Fitting AI로 가상 피팅 해줘
```

Codex가 `fitting-ai` 스킬을 읽고 Replicate API로 합성을 진행한다.

### 4. 웹 UI로 결과 확인 (선택)

Codex가 안내하거나, 플러그인 루트에서 웹 서버를 실행한다.

```powershell
cd src
.\run.ps1
```

브라우저에서 [http://127.0.0.1:8765](http://127.0.0.1:8765) 를 연다.

- 사용자 사진 / 옷 사진 업로드
- **입어보기** → 합성 결과 미리보기
- **저장** → 사용자가 클릭할 때만 다운로드

> Codex 캐시에 설치된 경우(`~/.codex/plugins/cache/.../local/`)에도 해당 폴더에 `.env`를 두거나, 환경변수 `REPLICATE_API_TOKEN`을 설정해야 한다.



## 제출 구조

```
submission.zip
├── src/
├── README.md
└── logs/
```



## 출처 (공개 자료)

- [AX 인재전쟁 2026](https://hackathon.jocodingax.ai/)
- [OpenAI Codex Plugins](https://developers.openai.com/codex/plugins)
- [OpenAI Codex Skills](https://developers.openai.com/codex/skills)
- [Replicate cuuupid/idm-vton](https://replicate.com/cuuupid/idm-vton)
- [IDM-VTON 논문 (arXiv:2403.05139)](https://arxiv.org/abs/2403.05139)
- [IDM-VTON GitHub](https://github.com/yisol/IDM-VTON)



## 라이선스 주의

IDM-VTON 모델은 [CC BY-NC-SA 4.0](https://creativecommons.org/licenses/by-nc-sa/4.0/) (비상업적 사용)입니다. 해커톤·데모 목적에 맞게 사용하세요.

## 로그 주의

`logs/` 폴더의 파일은 **사후 가공·편집·삭제 없이** 원본 그대로 제출해야 합니다. `logs/save_log.py`와 `.cursor/hooks/`가 대화를 자동 저장합니다.
