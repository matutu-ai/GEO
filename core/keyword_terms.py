"""Small deterministic helpers for GEO keyword and root normalization."""

import re


_GENERIC_REGION_TERMS = ("全国", "全球", "中国", "国内", "海外", "境外", "本地", "当地")
_ADMIN_AREA = re.compile(r"[\u4e00-\u9fff]{2,6}?(?:特别行政区|自治区|自治州|地区|省|市|州|盟|县|区)")
_ADMIN_SUFFIX = re.compile(r"(?:特别行政区|自治区|自治州|地区|省|市|州|盟|县|区)$")
_ROOT_BREAKS = re.compile(
    r"承接|增加|用于|帮助|解决|询问|缺少|目前|针对|通过|考察|寻找|希望|需要|优化|提升|改造|运营|开展|拓展|面向|决策者|较多|项目|现有|谨慎|为|在|做|的|与|和|或|但|[\s，。；、（）()/+]+"
)
_GENERIC_ROOTS = {"谨慎", "客户", "用户", "企业", "服务", "需求", "项目", "产品", "内容", "当前"}


def confirmed_region_terms(value):
    """Return confirmed region names and common aliases for conservative removal."""
    terms = set(_GENERIC_REGION_TERMS)
    values = value if isinstance(value, list) else [value]
    for item in values:
        if not isinstance(item, str):
            continue
        for part in re.split(r"[，,、;/；\s]+", item.strip()):
            if not part or any(marker in part for marker in ("待确认", "待核实", "待企业")):
                continue
            terms.add(part)
            for match in _ADMIN_AREA.findall(part):
                terms.add(match)
                alias = _ADMIN_SUFFIX.sub("", match)
                if len(alias) >= 2:
                    terms.add(alias)
            alias = _ADMIN_SUFFIX.sub("", part)
            if len(alias) >= 2:
                terms.add(alias)
    return tuple(sorted((term for term in terms if len(term) >= 2), key=len, reverse=True))


def without_regions(value, terms):
    """Remove known geographic modifiers without truncating the remaining phrase."""
    text = str(value or "")
    for term in terms:
        text = text.replace(term, "")
    return re.sub(r"[\s，,、；;｜|（）()]+", " ", text).strip()


def compact_keyword_root(value, terms=()):
    """Extract a concise, source-derived cue without manufacturing a new claim."""
    text = without_regions(value, terms)
    if 2 <= len(text) <= 8:
        return text
    parts = [part.strip(" ，、；。:：") for part in _ROOT_BREAKS.split(text)]
    candidates = [part for part in parts if 2 <= len(part) <= 8 and part not in _GENERIC_ROOTS]
    if not candidates:
        return ""
    selected = max(enumerate(candidates), key=lambda pair: (len(pair[1]), pair[0]))[1]
    if selected.endswith("需求") and len(selected) > 4:
        selected = selected[:-2]
    return selected
