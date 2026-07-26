import matplotlib.pyplot as plt
import matplotlib
import csv
import os
from typing import Dict, Any, List

# 设置中文字体（macOS: PingFang SC / STHeiti; Linux: SimHei; Windows: Microsoft YaHei）
matplotlib.rcParams['font.sans-serif'] = ['Noto Sans SC', 'PingFang SC', 'STHeiti', 'SimHei', 'Microsoft YaHei', 'Source Han Sans SC', 'DejaVu Sans']
matplotlib.rcParams['axes.unicode_minus'] = False

class ChartGenerator:
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.vi = config["vi_spec"]
        self.output_dir = "output/charts"
        os.makedirs(self.output_dir, exist_ok=True)

    def generate_charts(self, page_content: Dict[str, Any]) -> Dict[str, str]:
        """
        为每页生成配套图表
        HarnessConfig chart_code规则：同步输出CSV数据源+Python生成源码，确保可编辑可复现
        """
        charts = {}
        for page_id, content in page_content.items():
            if content.get("chart_data"):
                chart_spec = content["chart_data"]
                chart_path = self._create_chart(chart_spec, page_id)
                if chart_path:
                    # 2.9 同步输出CSV数据源
                    self._export_csv(chart_spec, page_id)
                    # 2.9 同步输出Python生成源码
                    self._export_source_code(chart_spec, page_id)
                    charts[page_id] = chart_path
        return charts

    def _create_chart(self, chart_spec: Dict[str, Any], page_id: str) -> str:
        """根据数据类型创建图表"""
        chart_type = chart_spec["type"]
        data = chart_spec["data"]
        title = chart_spec.get("title", "")

        fig, ax = plt.subplots(figsize=(6, 4), dpi=150)

        # 设置配色
        colors = [self.vi["primary_color"], self.vi["secondary_color"]] + self.vi["neutral_colors"][2:4]

        if chart_type == "bar":
            self._plot_bar(ax, data, colors, title)
        elif chart_type == "line":
            self._plot_line(ax, data, colors, title)
        elif chart_type == "pie":
            self._plot_pie(ax, data, colors, title)
        else:
            print(f"不支持的图表类型：{chart_type}")
            return None

        # 保存图表（PNG格式，python-pptx可嵌入；同时保留SVG供编辑）
        chart_path = os.path.join(self.output_dir, f"{page_id}_chart.png")
        plt.tight_layout()
        plt.savefig(chart_path, format="png", dpi=150, bbox_inches="tight", transparent=True)
        # 同时导出SVG供矢量编辑
        svg_path = os.path.join(self.output_dir, f"{page_id}_chart.svg")
        plt.savefig(svg_path, format="svg", bbox_inches="tight", transparent=True)
        plt.close()
        print(f"生成图表：{chart_path}")
        return chart_path

    # ================ CSV数据源输出 ================
    def _export_csv(self, chart_spec: Dict[str, Any], page_id: str):
        """
        HarnessConfig chart_code: 同步输出CSV数据源
        """
        chart_type = chart_spec["type"]
        data = chart_spec["data"]
        title = chart_spec.get("title", "")
        csv_path = os.path.join(self.output_dir, f"{page_id}_data.csv")

        try:
            with open(csv_path, "w", newline="", encoding="utf-8-sig") as f:
                writer = csv.writer(f)
                writer.writerow(["chart_type", chart_type])
                writer.writerow(["title", title])

                if chart_type in ("bar", "line"):
                    writer.writerow(["x", "y"])
                    for x_val, y_val in zip(data.get("x", []), data.get("y", [])):
                        writer.writerow([x_val, y_val])
                    if "x_label" in data:
                        writer.writerow(["x_label", data["x_label"]])
                    if "y_label" in data:
                        writer.writerow(["y_label", data["y_label"]])
                elif chart_type == "pie":
                    writer.writerow(["label", "size"])
                    for label, size in zip(data.get("labels", []), data.get("sizes", [])):
                        writer.writerow([label, size])

            print(f"  📊 CSV数据源已导出：{csv_path}")
        except Exception as e:
            print(f"  ⚠️ CSV导出失败：{e}")

    # ================ Python源码输出 ================
    def _export_source_code(self, chart_spec: Dict[str, Any], page_id: str):
        """
        HarnessConfig chart_code: 同步输出可执行Python生成源码
        """
        chart_type = chart_spec["type"]
        data = chart_spec["data"]
        title = chart_spec.get("title", "")
        py_path = os.path.join(self.output_dir, f"{page_id}_chart.py")

        # 构建可独立执行的Python脚本
        code_lines = [
            '"""自动生成的图表脚本 - 可独立执行，可编辑可复现"""',
            'import matplotlib.pyplot as plt',
            'import matplotlib',
            '',
            "matplotlib.rcParams['font.sans-serif'] = ['SimHei', 'Source Han Sans SC']",
            "matplotlib.rcParams['axes.unicode_minus'] = False",
            '',
            f'# 图表配置',
            f'chart_type = "{chart_type}"',
            f'title = "{title}"',
            '',
            f'# 数据源',
            f'data = {repr(data)}',
            '',
            f'# VI配色',
            f'primary_color = "{self.vi.get("primary_color", "#165DFF")}"',
            f'secondary_color = "{self.vi.get("secondary_color", "#36CFC9")}"',
            f'colors = [primary_color, secondary_color]',
            '',
            'fig, ax = plt.subplots(figsize=(6, 4), dpi=150)',
            '',
        ]

        if chart_type == "bar":
            code_lines.extend([
                'bars = ax.bar(data["x"], data["y"], color=primary_color, edgecolor=secondary_color, linewidth=1.5)',
                'ax.set_title(title, fontsize=12)',
                'if "y_label" in data: ax.set_ylabel(data["y_label"], fontsize=10)',
                'for bar in bars:',
                '    height = bar.get_height()',
                '    ax.text(bar.get_x() + bar.get_width()/2., height, f\'{height}\', ha=\'center\', va=\'bottom\', fontsize=9)',
            ])
        elif chart_type == "line":
            code_lines.extend([
                'ax.plot(data["x"], data["y"], color=primary_color, linewidth=2, marker="o", markersize=6)',
                'ax.set_title(title, fontsize=12)',
                'if "x_label" in data: ax.set_xlabel(data["x_label"], fontsize=10)',
                'if "y_label" in data: ax.set_ylabel(data["y_label"], fontsize=10)',
                'ax.grid(True, linestyle="--", alpha=0.3)',
            ])
        elif chart_type == "pie":
            code_lines.extend([
                'ax.pie(data["sizes"], labels=data["labels"], colors=colors[:len(data["sizes"])], autopct="%1.1f%%",',
                '       startangle=90, wedgeprops=dict(width=0.3, edgecolor="white"))',
                'ax.set_title(title, fontsize=12)',
                'ax.axis("equal")',
            ])

        code_lines.extend([
            '',
            'plt.tight_layout()',
            f'plt.savefig("{page_id}_chart.png", format="png", dpi=150, bbox_inches="tight", transparent=True)',
            f'plt.savefig("{page_id}_chart.svg", format="svg", bbox_inches="tight", transparent=True)',
            'plt.show()',
        ])

        try:
            with open(py_path, "w", encoding="utf-8") as f:
                f.write("\n".join(code_lines))
            print(f"  🐍 Python源码已导出：{py_path}")
        except Exception as e:
            print(f"  ⚠️ 源码导出失败：{e}")

    # ================ 图表绘制方法 ================
    def _plot_bar(self, ax, data: Dict[str, List], colors: List[str], title: str):
        """绘制柱状图"""
        x = data["x"]
        y = data["y"]
        bars = ax.bar(x, y, color=colors[0], edgecolor=colors[1], linewidth=1.5)
        ax.set_title(title, fontsize=12, color=self.vi["neutral_colors"][0])
        ax.set_ylabel(data.get("y_label", ""), fontsize=10)
        ax.tick_params(axis='both', labelsize=9)
        # 添加数据标签
        for bar in bars:
            height = bar.get_height()
            ax.text(bar.get_x() + bar.get_width()/2., height,
                    f'{height}', ha='center', va='bottom', fontsize=9)

    def _plot_line(self, ax, data: Dict[str, List], colors: List[str], title: str):
        """绘制折线图"""
        x = data["x"]
        y = data["y"]
        ax.plot(x, y, color=colors[0], linewidth=2, marker='o', markersize=6)
        ax.set_title(title, fontsize=12, color=self.vi["neutral_colors"][0])
        ax.set_xlabel(data.get("x_label", ""), fontsize=10)
        ax.set_ylabel(data.get("y_label", ""), fontsize=10)
        ax.tick_params(axis='both', labelsize=9)
        ax.grid(True, linestyle='--', alpha=0.3)

    def _plot_pie(self, ax, data: Dict[str, List], colors: List[str], title: str):
        """绘制环形图"""
        labels = data["labels"]
        sizes = data["sizes"]
        ax.pie(sizes, labels=labels, colors=colors[:len(sizes)], autopct='%1.1f%%',
               startangle=90, wedgeprops=dict(width=0.3, edgecolor='white'))
        ax.set_title(title, fontsize=12, color=self.vi["neutral_colors"][0])
        ax.axis('equal')
