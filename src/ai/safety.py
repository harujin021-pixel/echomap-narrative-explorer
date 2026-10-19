"""AI 生成内容 / 用户编辑文案的本地敏感信息检测与脱敏（src.ai.safety）。

设计原则（与项目硬约束一致）：
    - 纯本地规则检测：不联网、不把完整文案发送给任何第三方（含 AI 服务）；
    - 复用既有敏感词表（src/analysis/sensitive_words.txt），与预处理过滤口径同源；
    - 个人信息（PII）用正则识别：手机号、身份证号、邮箱；
    - 命中即脱敏（替换为占位标记），并给出"通过 / 未通过 / 无法确定"三种结论：
        仅"通过"允许界面导出；未通过或无法确定一律不得标记为通过、不得导出。

本模块只做检测与脱敏，不做"改写润色"，保持 AI 调用、文案生成、内容安全三层分离。
"""

from __future__ import annotations

import re
from dataclasses import dataclass

from src.analysis.preprocessing import load_sensitive_words

STATUS_PASS = "pass"
STATUS_FAIL = "fail"
STATUS_UNCERTAIN = "uncertain"

# 检出类别（界面标签由 i18n 层的 safety_cat_<code> 提供）
CAT_PHONE = "phone"
CAT_ID_CARD = "id_card"
CAT_EMAIL = "email"
CAT_SENSITIVE_WORD = "sensitive_word"

CATEGORIES: tuple[str, ...] = (
    CAT_PHONE,
    CAT_ID_CARD,
    CAT_EMAIL,
    CAT_SENSITIVE_WORD,
)

# 各类别的脱敏占位文本（替换命中片段）
_PLACEHOLDER: dict[str, str] = {
    CAT_PHONE: "[手机号已脱敏]",
    CAT_ID_CARD: "[证件号已脱敏]",
    CAT_EMAIL: "[邮箱已脱敏]",
    CAT_SENSITIVE_WORD: "***",
}

# PII 正则：用零宽断言避免把 18 位证件号中的片段误判为手机号
_PII_PATTERNS: tuple[tuple[str, re.Pattern[str]], ...] = (
    (CAT_ID_CARD, re.compile(r"(?<!\d)\d{17}[\dXx](?!\d)")),
    (CAT_PHONE, re.compile(r"(?<!\d)1[3-9]\d{9}(?!\d)")),
    (CAT_EMAIL, re.compile(r"[A-Za-z0-9._%+\-]+@[A-Za-z0-9.\-]+\.[A-Za-z]{2,}")),
)


@dataclass(frozen=True)
class Finding:
    """一处命中：类别、原始片段与位置（原始片段仅用于生成脱敏文本）。"""

    category: str
    term: str
    start: int
    end: int


@dataclass(frozen=True)
class SafetyReport:
    """一次检测结论；findings 为空且 status 为 pass 时才允许导出。"""

    status: str
    findings: tuple[Finding, ...]
    masked_text: str
    reason: str = ""  # "empty"（空内容）| "error"（检测异常）| ""

    @property
    def passed(self) -> bool:
        return self.status == STATUS_PASS


def analyze_text(text: object) -> SafetyReport:
    """检测并脱敏一段文案，返回 SafetyReport（纯函数，不联网）。

    - 空 / 非字符串内容：判定为 uncertain（无内容可判定，不得标记通过）；
    - 检测过程异常：判定为 uncertain（不猜测，不标记通过）；
    - 有命中：fail；无命中：pass。
    masked_text 始终给出（无命中时即原文）。
    """
    if not isinstance(text, str) or not text.strip():
        return SafetyReport(STATUS_UNCERTAIN, (), "", reason="empty")

    try:
        findings = _scan(text, load_sensitive_words())
    except Exception:
        return SafetyReport(STATUS_UNCERTAIN, (), text, reason="error")

    masked = _mask(text, findings)
    status = STATUS_FAIL if findings else STATUS_PASS
    return SafetyReport(status, tuple(findings), masked)


def category_counts(report: SafetyReport) -> list[tuple[str, int]]:
    """按类别汇总命中数量，返回按 CATEGORIES 顺序的 (类别, 数量) 列表。"""
    counts: dict[str, int] = {}
    for finding in report.findings:
        counts[finding.category] = counts.get(finding.category, 0) + 1
    return [(cat, counts[cat]) for cat in CATEGORIES if counts.get(cat)]


def _scan(text: str, sensitive_words: set[str]) -> list[Finding]:
    findings: list[Finding] = []
    for category, pattern in _PII_PATTERNS:
        for match in pattern.finditer(text):
            findings.append(Finding(category, match.group(0), match.start(), match.end()))

    lowered = text.lower()
    for word in sorted(sensitive_words):
        if not word:
            continue
        start = lowered.find(word)
        while start != -1:
            findings.append(
                Finding(CAT_SENSITIVE_WORD, text[start : start + len(word)], start, start + len(word))
            )
            start = lowered.find(word, start + len(word))

    findings.sort(key=lambda f: (f.start, f.end))
    return findings


def _mask(text: str, findings: list[Finding]) -> str:
    """把命中片段替换为占位文本；重叠片段按先出现者处理，不重复覆盖。"""
    if not findings:
        return text
    parts: list[str] = []
    cursor = 0
    for finding in sorted(findings, key=lambda f: f.start):
        if finding.start < cursor:  # 与已处理片段重叠，跳过
            continue
        parts.append(text[cursor : finding.start])
        parts.append(_PLACEHOLDER[finding.category])
        cursor = finding.end
    parts.append(text[cursor:])
    return "".join(parts)
