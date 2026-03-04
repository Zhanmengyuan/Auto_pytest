"""
Auto Pytest - 功能用例 → 自动化接口测试用例 转换系统

用法:
    python main.py generate -i testcases/sample_cases.yaml -o output/
    python main.py generate -d testcases/ -o output/
    python main.py init
    python main.py sample
"""

from __future__ import annotations

import sys
from pathlib import Path

import click

# 确保项目根目录在 sys.path 中
PROJECT_ROOT = Path(__file__).resolve().parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.utils.helpers import setup_logging


@click.group()
@click.version_option(version="2.0.0", prog_name="auto_pytest")
def cli():
    """
    🚀 Auto Pytest — 功能用例自动转换为接口自动化测试用例

    将 YAML 格式的功能用例自动生成为 pytest + httpx 的测试代码。
    """
    pass


@cli.command()
@click.option(
    "-i", "--input", "input_file",
    default=None,
    type=click.Path(exists=True),
    help="功能用例文件路径 (.yaml / .yml)",
)
@click.option(
    "-d", "--dir", "input_dir",
    default=None,
    type=click.Path(exists=True),
    help="功能用例目录（解析目录下所有 .yaml 文件）",
)
@click.option(
    "-o", "--output", "output_dir",
    default="output",
    type=click.Path(),
    help="测试代码输出目录 (默认: output/)",
)
@click.option(
    "--log-level",
    default="INFO",
    type=click.Choice(["DEBUG", "INFO", "WARNING", "ERROR"]),
    help="日志级别",
)
@click.option(
    "--with-conftest/--no-conftest",
    default=True,
    help="是否同时生成 conftest.py (默认: 是)",
)
def generate(input_file, input_dir, output_dir, log_level, with_conftest):
    """
    📝 从 YAML 功能用例文件生成测试代码

    示例:
        python main.py generate -i testcases/sample_cases.yaml
        python main.py generate -d testcases/ -o tests/
    """
    setup_logging(log_level)

    from src.parser.yaml_parser import parse_file, parse_dir
    from src.generator.test_generator import TestGenerator

    if not input_file and not input_dir:
        click.echo("❌ 请指定 -i (文件) 或 -d (目录) 参数")
        sys.exit(1)

    click.echo(f"\n{'='*60}")
    click.echo(f"  Auto Pytest - 自动化接口测试用例生成器")
    click.echo(f"{'='*60}\n")

    # 1. 解析用例文件
    if input_file:
        click.echo(f"📂 读取用例文件: {input_file}")
        cases = parse_file(input_file)
    else:
        click.echo(f"📂 扫描用例目录: {input_dir}")
        cases = parse_dir(input_dir)

    if not cases:
        click.echo("⚠️  未解析到任何用例，请检查 YAML 文件格式和内容")
        sys.exit(1)

    click.echo(f"✅ 成功解析 {len(cases)} 条用例\n")

    # 显示用例概览
    click.echo("📋 用例概览:")
    click.echo(f"{'─'*60}")
    for case in cases:
        tags_str = f" [{', '.join(case.tags)}]" if case.tags else ""
        data_driven = " 📊数据驱动" if case.is_data_driven else ""
        skip_mark = " ⏭跳过" if case.skip else ""
        click.echo(
            f"  {case.case_id:10s} | {case.priority} | {case.method:6s} {case.path:30s} "
            f"| {case.title}{tags_str}{data_driven}{skip_mark}"
        )
    click.echo(f"{'─'*60}\n")

    # 2. 生成测试代码
    click.echo(f"🔧 生成测试代码到: {output_dir}/")
    generator = TestGenerator(output_dir=output_dir)

    generated = generator.generate(cases)

    if with_conftest:
        conftest_path = generator.generate_conftest()
        click.echo(f"  ✅ {conftest_path}")

    for f in generated:
        click.echo(f"  ✅ {f}")

    click.echo(f"\n🎉 生成完成! 共 {len(generated)} 个测试文件")
    click.echo(f"\n💡 运行测试:")
    click.echo(f"   cd {output_dir}")
    click.echo(f"   pytest -v --env=dev")
    click.echo(f"   pytest -v --env=test")
    click.echo(f"   pytest -v --env=dev -m p0  # 仅运行 P0 用例")


@cli.command()
@click.option(
    "-o", "--output", "output_path",
    default="testcases/sample_cases.yaml",
    help="示例文件输出路径 (默认: testcases/sample_cases.yaml)",
)
def sample(output_path):
    """
    📄 生成示例 YAML 用例文件

    生成一个包含示例数据的 YAML 文件，方便参考格式填写。
    """
    setup_logging("INFO")
    from src.utils.helpers import generate_sample_yaml

    click.echo(f"\n📄 生成示例用例文件...")
    path = generate_sample_yaml(output_path)
    click.echo(f"✅ 示例文件已生成: {path}")
    click.echo(f"\n💡 接下来，在此文件中填写你的功能用例，然后运行:")
    click.echo(f"   python main.py generate -i {output_path}")


@cli.command()
def init():
    """
    🏗️  初始化项目结构

    创建必要的目录和默认配置文件。
    """
    setup_logging("INFO")

    dirs = ["testcases", "output", "reports", "config"]
    for d in dirs:
        Path(d).mkdir(parents=True, exist_ok=True)
        click.echo(f"  📁 {d}/")

    # 检查配置文件
    config_path = Path("config/env_config.yaml")
    if not config_path.exists():
        click.echo(f"  📄 请创建 {config_path}，可参考项目中的示例配置")
    else:
        click.echo(f"  ✅ {config_path} 已存在")

    click.echo(f"\n🎉 初始化完成!")
    click.echo(f"\n💡 下一步:")
    click.echo(f"   1. python main.py sample        # 生成示例 YAML 用例模板")
    click.echo(f"   2. 编辑 YAML 填写功能用例")
    click.echo(f"   3. python main.py generate -i testcases/sample_cases.yaml")


if __name__ == "__main__":
    cli()
