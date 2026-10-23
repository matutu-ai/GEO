"""Build and synchronize a self-contained Skill from the repository source."""

import argparse
import shutil
import tempfile
import zipfile
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
PACKAGE_FILES = (
    "SKILL.md", "agents/openai.yaml", "templates/delivery.md",
    "references/keyword-rules.md", "references/template-guide.md",
    "references/article-training.md", "prompts/standard/00_quick_start.md",
    "scripts/check_delivery.py",
)


def package_skill(install_to=None, archive=None):
    for name in PACKAGE_FILES:
        if not (ROOT / name).is_file():
            raise ValueError(f"Skill 资源缺失：{name}")
    if install_to is not None:
        target = Path(install_to).resolve()
        if target == ROOT or target.name != "geo-keyword-persona":
            raise ValueError("安装目标必须是独立的 geo-keyword-persona 目录")
        changed = [name for name in PACKAGE_FILES if (target / name).exists()
                   and (target / name).read_bytes() != (ROOT / name).read_bytes()]
        if changed:
            backup = Path(tempfile.mkdtemp(prefix="geo-skill-backup-"))
            for name in changed:
                (backup / name).parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(target / name, backup / name)
            print(f"原安装文件备份：{backup}")
        for name in PACKAGE_FILES:
            (target / name).parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(ROOT / name, target / name)
            if (target / name).read_bytes() != (ROOT / name).read_bytes():
                raise ValueError(f"同步后内容不一致：{name}")
        print(f"PASS: 已同步并逐文件核对 {len(PACKAGE_FILES)} 个 Skill 文件")
    if archive is not None:
        archive = Path(archive)
        archive.parent.mkdir(parents=True, exist_ok=True)
        with zipfile.ZipFile(archive, "w", zipfile.ZIP_DEFLATED) as bundle:
            for name in PACKAGE_FILES:
                bundle.write(ROOT / name, f"geo-keyword-persona/{name}")
        with zipfile.ZipFile(archive) as bundle:
            for name in PACKAGE_FILES:
                if bundle.read(f"geo-keyword-persona/{name}") != (ROOT / name).read_bytes():
                    raise ValueError(f"压缩包内容不一致：{name}")
        print(f"PASS: 完整 Skill 包 {archive}")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--install-to", type=Path)
    parser.add_argument("--archive", type=Path)
    args = parser.parse_args()
    if not args.install_to and not args.archive:
        parser.error("至少指定 --install-to 或 --archive")
    package_skill(args.install_to, args.archive)


if __name__ == "__main__":
    main()
