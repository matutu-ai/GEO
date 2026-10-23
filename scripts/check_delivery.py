"""Validate a final Markdown delivery against the single bundled template."""

import argparse
import re
from pathlib import Path


TEMPLATE = Path(__file__).resolve().parents[1] / "templates" / "delivery.md"
OUTPUT_MODES = ("完整模式", "仅词模式", "仅画像模式")
DELIVERY_MODES = ("简约版", "完整版")


def delivery_template(output_mode="仅词模式"):
    if output_mode not in OUTPUT_MODES:
        raise ValueError("DELIVERY-001: 未知输出模式")
    template = TEMPLATE.read_text(encoding="utf-8")
    if output_mode == "仅词模式":
        template = re.sub(r"^## 九大画像\n.*?(?=^## 待补资料)", "", template, flags=re.M | re.S)
    if output_mode == "仅画像模式":
        template = re.sub(r"^## 四类关键词\n.*?(?=^## 九大画像)", "", template, flags=re.M | re.S)
    return template


def _cells(row):
    return [cell.strip() for cell in re.split(r"(?<!\\)\|", row.strip())[1:-1]]


def validate_delivery(text, output_mode="仅词模式", delivery_mode="完整版"):
    template = delivery_template(output_mode)
    if delivery_mode not in DELIVERY_MODES:
        raise ValueError("DELIVERY-002: 未知画像详略")
    expected = re.findall(r"^#{2,6} .+$", template, re.M)
    actual = re.findall(r"^#{2,6} .+$", text, re.M)
    if actual != expected or len(re.findall(r"^# .+$", text, re.M)) != 1:
        raise ValueError("DELIVERY-003: 章节缺失、增加或顺序与固定模板不一致")
    if re.search(r"\{\{\w+\}\}|^```", text, re.M):
        raise ValueError("DELIVERY-004: 未替换占位符或结果被代码块包裹")
    if output_mode != "仅画像模式":
        section = text.split("## 四类关键词\n", 1)[1].split("\n## ", 1)[0]
        blocks = re.split(r"^### .+\n", section, flags=re.M)[1:]
        header = _cells(next(line for line in template.splitlines() if line.startswith("|")))
        for block in blocks:
            rows = [line for line in block.splitlines() if line.startswith("|")]
            if len(rows) < 3 or _cells(rows[0]) != header:
                raise ValueError("DELIVERY-005: 每类词须使用固定两列表头并有内容或待补行")
            if any(len(_cells(row)) != 2 for row in rows):
                raise ValueError("DELIVERY-006: 词表只能有推荐词、短词根两列")
            if not all(re.fullmatch(r":?-{3,}:?", cell) for cell in _cells(rows[1])):
                raise ValueError("DELIVERY-007: 表格分隔行无效")
            for row in rows[2:]:
                keyword, root = _cells(row)
                if not keyword or not root:
                    raise ValueError("DELIVERY-008: 推荐词或短词根缺失")
    if output_mode != "仅词模式":
        section = text.split("## 九大画像\n", 1)[1].split("\n## 待补资料", 1)[0]
        selected = re.search(r"^本轮已选词：(.+)。$", section, re.M)
        if not selected or selected.group(1).strip() in ("待补", "—", "无", "未选择"):
            raise ValueError("DELIVERY-011: 生成画像前须记录用户已选词")
        bodies = re.split(r"^### .+\n", section, flags=re.M)[1:]
        for body in bodies:
            if not body.strip():
                raise ValueError("DELIVERY-009: 画像板块为空，简约版缺项应写待补")
            length = len("".join(body.replace("\\|", "|").split()))
            if delivery_mode == "完整版" and not 800 <= length <= 1000:
                raise ValueError(f"DELIVERY-010: 完整版每项必须800–1000字，当前{length}字")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("file", type=Path)
    parser.add_argument("--output-mode", choices=OUTPUT_MODES, default="仅词模式")
    parser.add_argument("--delivery-mode", choices=DELIVERY_MODES, default="完整版")
    args = parser.parse_args()
    try:
        validate_delivery(args.file.read_text(encoding="utf-8"), args.output_mode, args.delivery_mode)
    except (OSError, ValueError) as exc:
        parser.exit(1, f"{exc}\n")
    print("PASS: 交付结构与所选模式一致")


if __name__ == "__main__":
    main()
