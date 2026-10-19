"""Immutable byte catalogs for supported ForgeFlow governance bundles."""

from hashlib import sha256
from pathlib import Path
from typing import Dict

from .catalog_oracles import load_oracle
from .scaffold import TemplateScaffolder

VERSION_LINE = "\n- ForgeFlow bundle version: `0.22.0`\n"
V060_VERSION_LINE = "\n- ForgeFlow bundle version: `0.6.0`\n"
V050_VERSION_LINE = "\n- ForgeFlow bundle version: `0.5.0`\n"
V047_VERSION_LINE = "\n- ForgeFlow bundle version: `0.4.7`\n"
V046_VERSION_LINE = "\n- ForgeFlow bundle version: `0.4.6`\n"
V045_VERSION_LINE = "\n- ForgeFlow bundle version: `0.4.5`\n"
V048_CHANGELOG_SECTION = """## [v0.4.8] - 2026-10-03

### User-facing Release Notes artifact
- 새 release scaffold에 `RELEASE_NOTES.md`를 추가하고 사용자·운영자 문서의 역할을 정의했다.
- Evidence v1 core artifact와 strict lifecycle audit은 기존 exact four artifact만 검사하도록 경계를 명확히 했다.

"""
V047_CHANGELOG_SECTION = """## [v0.4.7] - 2026-10-01

### Autonomous guidance consolidation
- autonomous continuation의 상세 정책과 Tier 분류 규칙을 `GATES_AND_LOOPS.md` 단일 원본으로 통합했다.

"""
V047_TIERING_RULE = "- `autonomous` 선택·활성화·운영 자체는 Tier를 올리거나 내리는 risk signal이 아니다. Tier와 Gate 강도는 요청의 실제 변경과 기존 risk signal만으로 분류한다.\n"
V048_FLOW_TREE = "│           └── RELEASE_NOTES.md     # 사용자용 변경·운영 안내 (선택적, evidence 제외)\n"
V048_FLOW_BOUNDARY = "- **Release Notes boundary**: `RELEASE_NOTES.md`는 기능 변화, 사용자 영향, 운영·업그레이드 유의사항, 알려진 제약, 근거 문서를 담는 사용자용 문서다. 새 release scaffold에는 기본 포함되지만 기존 release에서는 선택적이다. Evidence v1 core artifact와 digest는 정확히 `PRD.md`, `DESIGN.md`, `QA_SIGNOFF.md`, `COMPLETION_REPORT.md` 네 파일만 대상으로 하며 Release Notes의 생성·수정·삭제·부재는 stale candidate나 strict audit 결과를 바꾸지 않는다.\n"
V048_GATES_BOUNDARY = "- `RELEASE_NOTES.md`는 사용자용 release communication artifact다. 새 scaffold에는 생성하지만 기존 release에서 optional이며 Gate evidence로 해석하지 않는다. Evidence v1 artifact set과 digest는 `PRD.md`, `DESIGN.md`, `QA_SIGNOFF.md`, `COMPLETION_REPORT.md` exact four로 고정한다. Release Notes만 추가·수정·삭제되어도 candidate, Gate 2, QA evidence, strict lifecycle audit은 stale 처리하지 않는다.\n"
V047_FLOW_CONTINUATION = "프로젝트는 기본 `interactive` 또는 opt-in `autonomous` continuation policy를 선택할 수 있다. 상세 activation, delegation, lifecycle-owner, authority boundary, evidence, 그리고 tiering 규칙은 [GATES_AND_LOOPS.md](GATES_AND_LOOPS.md)를 따른다.\n"
V046_FLOW_CONTINUATION = "프로젝트는 기본 `interactive` 또는 opt-in `autonomous` continuation policy를 선택할 수 있다. `interactive`는 기존 사람과 lifecycle owner의 판단 교환을 유지한다. `autonomous`, “autonomous mode”, “자동 모드”는 host가 해석하는 동등한 명시적 완료 위임의 예시이며, parser나 runtime attestation이 아니다. `autonomous`에서는 host의 Autonomous Main AI가 사용자 대리 lifecycle owner로서 stage-owner와 implementer/reviewer 역할을 논리적으로 배치할 수 있다. `Go`와 `계속`은 이미 활성화된 autonomous lifecycle만 재개하며, dormant lifecycle을 활성화하거나 이전 authority boundary의 위험 작업을 포괄 승인하지 않는다. 활성 lifecycle owner는 내부 작업을 기다리고, 반환 결과를 평가하며, self-resolvable failure를 remediation으로 전환한 뒤에만 다음 action 또는 final response를 낸다. 내부 작업이 남아 있으면 final response를 내지 않는다. 정상 종료는 evidence completion 또는 기존 authority boundary에서만 가능하다. 이 선택은 Tier, Stage, Gate, 독립 심사, candidate binding, 기존 evidence 또는 외부 side effect 승인 경계를 완화하지 않는다. host가 dispatch, wait, retry, 위임 해석과 runtime result를 소유하며, ForgeFlow는 이를 기록하거나 검사하지 않는다. 기존 canonical release artifact가 유일한 Gate evidence다.\n"
V047_GOVERNANCE_CONTINUATION = "`.forgeflow.json`의 `governance.continuation_policy`는 기본 `interactive`와 opt-in `autonomous`를 구분합니다. 상세 activation, authority boundary, evidence, tiering 규칙은 [Gate와 loop 기준](./spec/GATES_AND_LOOPS.md)을 따릅니다.\n"
V046_GOVERNANCE_CONTINUATION = "`.forgeflow.json`의 `governance.continuation_policy`는 기본 `interactive`와 opt-in `autonomous`를 구분합니다. `interactive`에서는 사람과 lifecycle owner가 다음 판단을 주고받습니다. `autonomous`, “autonomous mode”, “자동 모드”는 동등한 명시적 완료 위임의 예시이며, host가 해석합니다. `Go`와 `계속`은 이미 활성화된 autonomous lifecycle만 재개하고 dormant lifecycle을 활성화하거나 이전 authority boundary의 위험 작업을 포괄 승인하지 않습니다. autonomous lifecycle owner는 internal work를 기다리고 결과를 평가하며 self-resolvable failure를 remediation으로 전환합니다. internal work가 남아 있으면 final response를 내지 않으며, evidence completion 또는 기존 authority boundary에서만 정상 종료합니다. Autonomous Main AI는 사용자 대리 lifecycle owner로서 stage-owner와 worker/reviewer 역할을 논리적으로 배치합니다. 이 정책은 Stage, Tier, Gate, evidence, reviewer independence, 또는 외부 side effect 승인 경계를 완화하지 않습니다. 모호한 위임, scope/risk/design 변경, credential, destructive action, remote Git, publish, deploy, product/design decision, exact-five no-progress는 사용자 판단으로 에스컬레이션합니다.\n"
V045_UPDATE_SECTION = """### Local governance bundle update

`forgeflow update` previews a supported local governance-bundle transition without writing. `--apply` may replace only an exact catalog-recognized bundle through the existing transaction/recovery controls; edited, unknown, or unsafe targets fail closed.

"""
CURRENT_UPDATE_SECTION = """### Local governance bundle update

`forgeflow update` previews a supported local governance-bundle transition without writing. `--apply` may replace only an exact catalog-recognized bundle through the existing transaction/recovery controls; edited, unknown, or unsafe targets fail closed. A valid unversioned legacy configuration is eligible only when every governed file exactly matches a supported immutable legacy bundle. `forgeflow init --force` is the explicit complete local reinstall path: it replaces only `.forgeflow.json`, `docs/forgeflow/GOVERNANCE.md`, and the governed spec/template bundle through the same transaction controls; it never replaces root guides, project source, release artifacts, or other user files.

"""


def current_bundle() -> Dict[Path, str]:
    bundle = {TemplateScaffolder.GOVERNANCE_PATH: TemplateScaffolder.get_template_content("GOVERNANCE.md")}
    bundle.update({path: TemplateScaffolder.get_template_content(resource) for path, resource in TemplateScaffolder.BUNDLE_FILES.items()})
    return bundle


def bundle_for(version: str) -> Dict[Path, str]:
    if version in {"0.1.0", "0.30.0", "0.22.1", "0.22.0", "0.21.0", "0.20.0", "0.19.0", "0.18.0", "0.17.0", "0.16.1", "0.16.0", "0.15.0", "0.14.0", "0.13.0", "0.12.0", "0.11.0", "0.10.1", "0.10.0", "0.9.0", "0.8.2", "0.8.1", "0.8.0", "0.7.1", "0.7.0"}:
        return current_bundle()
    if version == "0.6.0":
        return load_oracle(version)
    if version == "0.5.0":
        return load_oracle(version)
    if version == "0.4.8":
        return load_oracle(version)
    bundle = bundle_for("0.4.8")
    if version == "0.4.7":
        bundle[TemplateScaffolder.GOVERNANCE_PATH] = bundle[TemplateScaffolder.GOVERNANCE_PATH].replace(VERSION_LINE, V047_VERSION_LINE)
        bundle[Path("docs/forgeflow/spec/CHANGELOG.md")] = bundle[Path("docs/forgeflow/spec/CHANGELOG.md")].replace(V048_CHANGELOG_SECTION, "")
        flow = Path("docs/forgeflow/spec/FLOW_SPEC.md")
        bundle[flow] = bundle[flow].replace(V048_FLOW_TREE, "").replace(V048_FLOW_BOUNDARY, "")
        gates = Path("docs/forgeflow/spec/GATES_AND_LOOPS.md")
        bundle[gates] = bundle[gates].replace(V048_GATES_BOUNDARY, "")
        return bundle
    if version == "0.4.6":
        bundle[TemplateScaffolder.GOVERNANCE_PATH] = bundle[TemplateScaffolder.GOVERNANCE_PATH].replace(VERSION_LINE, V046_VERSION_LINE).replace(V047_GOVERNANCE_CONTINUATION, V046_GOVERNANCE_CONTINUATION)
        bundle[Path("docs/forgeflow/spec/CHANGELOG.md")] = bundle[Path("docs/forgeflow/spec/CHANGELOG.md")].replace(V047_CHANGELOG_SECTION, "")
        bundle[Path("docs/forgeflow/spec/FLOW_SPEC.md")] = bundle[Path("docs/forgeflow/spec/FLOW_SPEC.md")].replace(V047_FLOW_CONTINUATION, V046_FLOW_CONTINUATION)
        bundle[Path("docs/forgeflow/spec/GATES_AND_LOOPS.md")] = bundle[Path("docs/forgeflow/spec/GATES_AND_LOOPS.md")].replace(V047_TIERING_RULE, "")
        return bundle
    if version == "0.4.5":
        bundle = bundle_for("0.4.6")
        bundle[TemplateScaffolder.GOVERNANCE_PATH] = bundle[TemplateScaffolder.GOVERNANCE_PATH].replace(V046_VERSION_LINE, V045_VERSION_LINE)
        flow_spec = Path("docs/forgeflow/spec/FLOW_SPEC.md")
        bundle[flow_spec] = bundle[flow_spec].replace(CURRENT_UPDATE_SECTION, V045_UPDATE_SECTION)
        return bundle
    if version == "0.4.4":
        bundle = bundle_for("0.4.5")
        bundle[TemplateScaffolder.GOVERNANCE_PATH] = bundle[TemplateScaffolder.GOVERNANCE_PATH].replace(V045_VERSION_LINE, "")
        flow_spec = Path("docs/forgeflow/spec/FLOW_SPEC.md")
        bundle[flow_spec] = bundle[flow_spec].replace(V045_UPDATE_SECTION, "")
        return bundle
    raise KeyError(version)


def digests_for(version: str) -> Dict[Path, str]:
    return {path: sha256(content.encode()).hexdigest() for path, content in bundle_for(version).items()}
