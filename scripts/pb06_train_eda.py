"""Reproducible train-only EDA; run from the repository root (see README).

Outputs are descriptive reports, never inputs to feature extraction. No model,
imputation, outlier deletion, or feature selection is performed here.
"""

from __future__ import annotations

import argparse
import base64
from html import escape
import json
from pathlib import Path
import platform
import subprocess

import matplotlib

matplotlib.use("Agg")
import matplotlib.dates as mdates
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns

from metropt3.config import load_config
from metropt3.ingest import ANALOG_COLUMNS, DIGITAL_COLUMNS, SENSOR_COLUMNS


ROOT = Path(__file__).resolve().parents[1]
UNITS = {c: "bar" for c in ANALOG_COLUMNS}
UNITS.update(Oil_temperature="°C", Motor_current="A")
STATE_COLUMNS = ("COMP", "DV_eletric", "Towers")
QUALITY_FLAGS = ("invalid_timestamp", "missing_cell", "invalid_numeric", "infinity", "invalid_digital")
UCI_URL = "https://archive.ics.uci.edu/dataset/791/metropt%2B3%2Bdataset"


def analyze(cleaned: pd.DataFrame, config: dict, per_day: int = 300) -> dict:
    """Select train BEFORE computing statistics or choosing any plot samples."""
    if per_day < 1:
        raise ValueError("per_day must be positive")
    boundary = pd.Timestamp(config["split"]["train_end_exclusive"])
    calendar_train = cleaned.timestamp.lt(boundary)
    if not calendar_train.equals(cleaned.split.eq("train")):
        raise ValueError("cleaned.split disagrees with configured train boundary; rerun audit")
    raw = cleaned.loc[calendar_train].sort_values(["timestamp", "raw_row_id"]).copy()
    raw.attrs = {}
    if raw.empty or raw.raw_row_id.duplicated().any() or raw.timestamp.duplicated().any():
        raise ValueError("Expected nonempty audited train with unique row IDs/timestamps")
    train = raw.loc[raw.valid.fillna(False)].copy()
    if train.empty or not np.isfinite(train[list(SENSOR_COLUMNS)].to_numpy()).all():
        raise ValueError("No valid train, or valid train contains nonfinite sensors")
    if not train[list(DIGITAL_COLUMNS)].isin([0, 1]).all().all():
        raise ValueError("Valid train contains nonbinary digital values")

    # Each day gets the same cap; the RNG sees only sorted train observations.
    # This sample is used ONLY in scatter plots. All tables use full valid train.
    rng = np.random.default_rng(config["reproducibility"]["seed"])
    pieces = []
    sampling = []
    for day, group in train.groupby(train.timestamp.dt.normalize(), sort=True):
        count = min(per_day, len(group))
        positions = np.sort(rng.choice(len(group), size=count, replace=False))
        pieces.append(group.iloc[positions])
        sampling.append({"day": day, "available_rows": len(group), "sample_rows": count})
    sample = pd.concat(pieces).sort_values(["timestamp", "raw_row_id"])
    stats = train[list(ANALOG_COLUMNS)].describe(percentiles=[.01, .1, .25, .5, .75, .9, .99]).T
    stats.insert(0, "unit", [UNITS[c] for c in stats.index])
    frequencies = []
    for column in DIGITAL_COLUMNS:
        for value in [0, 1]:
            count = int(train[column].eq(value).sum())
            frequencies.append({"sensor": column, "value": value, "count": count,
                                "percent": count / len(train) * 100})
    frequencies = pd.DataFrame(frequencies)
    days = pd.date_range(raw.timestamp.min().normalize(), boundary.normalize() - pd.Timedelta(days=1), freq="D")
    daily_count = train.groupby(train.timestamp.dt.normalize()).size().reindex(days, fill_value=0)
    daily = pd.DataFrame({"valid_rows": daily_count})
    daily.index.name = "day"
    for column in ANALOG_COLUMNS:
        grouped = train.groupby(train.timestamp.dt.normalize())[column]
        for name, quantile in [("p10", .1), ("median", .5), ("p90", .9)]:
            daily[f"{column}_{name}"] = grouped.quantile(quantile).reindex(days)
    state_stats = []
    for state in STATE_COLUMNS:
        for value, group in train.groupby(state, sort=True):
            row = {"signal": state, "value": int(value), "count": len(group),
                   "percent": len(group) / len(train) * 100}
            row.update({f"{c}_median": group[c].median() for c in ANALOG_COLUMNS})
            state_stats.append(row)
    combinations = train.groupby(list(STATE_COLUMNS)).size().rename("count").reset_index()
    combinations["percent"] = combinations["count"] / len(train) * 100
    deltas = raw.timestamp.diff().dt.total_seconds()
    # Cadence is recomputed exclusively on train, matching PB03's mode tie rule.
    positive = deltas[deltas.gt(0)]
    if positive.empty:
        raise ValueError("At least two distinct train timestamps are required")
    cadence = float(positive.mode().min())
    gap_break = cadence * config["quality"]["gap_multiplier"]
    gaps = pd.DataFrame({"start": raw.timestamp.shift(), "end": raw.timestamp,
                         "seconds": deltas}).loc[deltas.gt(gap_break)].reset_index(drop=True)
    return {"train": train, "sample": sample, "sampling": pd.DataFrame(sampling),
            "stats": stats, "frequencies": frequencies, "daily": daily,
            "pearson": train[list(SENSOR_COLUMNS)].corr(method="pearson"),
            "spearman": train[list(SENSOR_COLUMNS)].corr(method="spearman"),
            "state_stats": pd.DataFrame(state_stats), "combinations": combinations,
            "quality": {c: int(raw[c].fillna(False).sum()) for c in QUALITY_FLAGS},
            "train_rows_before_quality": len(raw), "quality_excluded": len(raw) - len(train),
            "cadence_seconds": cadence, "gap_break_seconds": gap_break, "gaps": gaps,
            "boundary": str(boundary), "seed": config["reproducibility"]["seed"], "per_day": per_day}


def plot_figures(a: dict, output: Path) -> dict[str, Path]:
    sns.set_theme(style="whitegrid", font="DejaVu Sans", font_scale=.9)
    plt.rcParams.update({"savefig.dpi": 125, "axes.spines.top": False, "axes.spines.right": False})
    figures = {}
    train, sample, daily = a["train"], a["sample"], a["daily"]
    period = f"Train: {train.timestamp.min():%Y-%m-%d} → {train.timestamp.max():%Y-%m-%d}"

    def save(fig, name):
        fig.tight_layout(rect=(0, 0, 1, .975))
        path = output / "figures" / f"{name}.png"
        path.parent.mkdir(parents=True, exist_ok=True)
        fig.savefig(path, bbox_inches="tight", metadata={"Software": "MetroPT-3 PB06"})
        plt.close(fig)
        figures[name] = path

    fig, axes = plt.subplots(4, 2, figsize=(13, 13))
    for ax, column in zip(axes.flat, ANALOG_COLUMNS):
        ax.hist(train[column], bins=80, color="#247a96")
        ax.set(xlabel=f"{column} ({UNITS[column]})", ylabel="Số quan sát")
    axes.flat[-1].axis("off")
    fig.suptitle(f"Phân phối 7 analog — toàn bộ train hợp lệ\n{period}")
    save(fig, "analog_histograms")

    fig, axes = plt.subplots(4, 2, figsize=(13, 11))
    for ax, column in zip(axes.flat, ANALOG_COLUMNS):
        ax.boxplot(train[column].to_numpy(), orientation="horizontal", whis=1.5,
                   flierprops={"markersize": 1.5, "alpha": .15})
        ax.set(xlabel=f"{column} ({UNITS[column]})", yticks=[])
    axes.flat[-1].axis("off")
    fig.suptitle(f"Boxplot — toàn bộ train, giữ cả điểm ngoài râu\n{period}")
    save(fig, "analog_boxplots")

    freq = a["frequencies"].pivot(index="sensor", columns="value", values="percent").reindex(DIGITAL_COLUMNS)
    fig, ax = plt.subplots(figsize=(12, 6))
    freq.plot.barh(stacked=True, color=["#247a96", "#e6a348"], ax=ax)
    ax.set(xlabel="Tỷ lệ quan sát hợp lệ (%)", ylabel="Digital (giá trị nhị phân 0/1)", xlim=(0, 100))
    ax.legend(title="Giá trị", loc="lower right")
    ax.set_title(f"Tần suất digital — không quy đổi sang thời lượng\n{period}")
    save(fig, "digital_frequency")

    fig, axes = plt.subplots(8, 1, figsize=(14, 19), sharex=True)
    for ax, column in zip(axes, ANALOG_COLUMNS):
        ax.fill_between(daily.index, daily[f"{column}_p10"], daily[f"{column}_p90"], alpha=.22, color="#247a96", label="P10–P90")
        ax.plot(daily.index, daily[f"{column}_median"], color="#247a96", marker=".", label="Median")
        ax.set_ylabel(f"{column}\n({UNITS[column]})")
    axes[0].legend(loc="upper left", ncols=2)
    axes[-1].bar(daily.index, daily.valid_rows, color="#596c78")
    axes[-1].set(ylabel="Số quan sát\nhợp lệ/ngày", xlabel="Ngày (đồng hồ gốc, không múi giờ)")
    axes[-1].xaxis.set_major_formatter(mdates.DateFormatter("%d/%m"))
    axes[-1].set_xlim(daily.index.min() - pd.Timedelta(hours=12), daily.index.max() + pd.Timedelta(hours=12))
    fig.suptitle(f"Timeline ngày — median và P10–P90, ngày thiếu để trống\n{period}")
    save(fig, "daily_timeline")

    fig, axes = plt.subplots(2, 1, figsize=(13, 23))
    for ax, method in zip(axes, ["pearson", "spearman"]):
        corr = a[method]
        sns.heatmap(corr, mask=corr.isna(), vmin=-1, vmax=1, center=0, cmap="vlag", ax=ax,
                    annot=True, fmt=".2f", annot_kws={"fontsize": 8}, square=True,
                    cbar_kws={"label": "Hệ số tương quan (không đơn vị)", "shrink": .65})
        ax.set_title(method.title() + " — ô trống: cột hằng / không xác định")
        ax.tick_params(axis="both", labelsize=8)
    fig.suptitle(f"Tương quan trên toàn bộ 15 sensor train hợp lệ\n{period}")
    save(fig, "correlations")

    fig, axes = plt.subplots(1, 2, figsize=(13, 5))
    for ax, (left, right) in zip(axes, [("TP3", "Reservoirs"), ("TP2", "H1")]):
        ax.scatter(sample[left], sample[right], s=4, alpha=.2, color="#247a96", rasterized=True)
        ax.set(xlabel=f"{left} ({UNITS[left]})", ylabel=f"{right} ({UNITS[right]})")
    fig.suptitle(f"Scatter lấy mẫu theo ngày: n={len(sample):,}, seed={a['seed']}\n{period}")
    save(fig, "sampled_scatter")

    fig, axes = plt.subplots(3, 4, figsize=(16, 10))
    for row, state in enumerate(STATE_COLUMNS):
        for col, sensor in enumerate(["Motor_current", "TP2", "TP3", "H1"]):
            ax = axes[row, col]
            groups = [(v, g) for v, g in train.groupby(state, sort=True)]
            ax.boxplot([g[sensor].to_numpy() for _, g in groups], tick_labels=[str(int(v)) for v, _ in groups],
                       flierprops={"markersize": 1, "alpha": .1})
            ax.set(xlabel=f"{state} (0/1)", ylabel=f"{sensor} ({UNITS[sensor]})")
    fig.suptitle(f"Analog theo từng digital — toàn bộ train, có số lượng trong bảng báo cáo\n{period}")
    save(fig, "analog_by_state")

    # Two train-only windows chosen by explicit rules, never by looking at test.
    transition = train.COMP.ne(train.COMP.shift()) & train.segment_id.eq(train.segment_id.shift())
    centers = [("detail_transition", "Chuyển COMP đầu tiên trong cùng segment",
                train.loc[transition, "timestamp"].iloc[0] if transition.any() else train.timestamp.iloc[0])]
    rare = a["frequencies"].query("count > 0").sort_values(["count", "sensor", "value"]).iloc[0]
    rare_time = train.loc[train[rare.sensor].eq(rare.value), "timestamp"].iloc[0]
    centers.append(("detail_rare", f"Trạng thái hiếm nhất: {rare.sensor}={int(rare.value)}", rare_time))
    for name, label, center in centers:
        part = train.loc[train.timestamp.between(center - pd.Timedelta(minutes=10), center + pd.Timedelta(minutes=10))]
        detail_states = list(STATE_COLUMNS)
        if name == "detail_rare" and rare.sensor not in detail_states:
            detail_states.append(rare.sensor)
        fig, axes = plt.subplots(2 + len(detail_states), 1, figsize=(14, 2.2 * (2 + len(detail_states))), sharex=True)
        for _, group in part.groupby("segment_id", sort=False):
            axes[0].plot(group.timestamp, group.Motor_current, ".-", markersize=2, color="#247a96")
            for column in ["TP2", "TP3", "H1"]:
                axes[1].plot(group.timestamp, group[column], label=column)
            for ax, state in zip(axes[2:], detail_states):
                ax.step(group.timestamp, group[state], where="post", label=state)
                ax.set(ylabel=f"{state}\n(0/1)", yticks=[0, 1], ylim=(-.1, 1.1))
        axes[0].set_ylabel("Motor_current (A)")
        axes[1].set_ylabel("Áp suất (bar)")
        handles, labels = axes[1].get_legend_handles_labels()
        unique = dict(zip(labels, handles))
        axes[1].legend(unique.values(), unique.keys(), loc="upper left", ncols=3)
        for ax in axes:
            ax.axvline(center, color="#b14f39", linestyle="--", alpha=.7)
        axes[-1].set_xlabel("Ngày giờ gốc (không múi giờ); điểm analog là quan sát thật")
        axes[-1].set_xlim(center - pd.Timedelta(minutes=10), center + pd.Timedelta(minutes=10))
        axes[-1].xaxis.set_major_formatter(mdates.DateFormatter("%d/%m %H:%M"))
        fig.suptitle(f"{label} — {center}\nCửa sổ ±10 phút, không aggregate/fill; không nối qua segment")
        save(fig, name)
    return figures


class Report:
    """Write identical content to Markdown and a portable, self-contained HTML."""

    def __init__(self):
        self.md = []
        self.html = []

    def heading(self, title, level=2):
        self.md.append(f"{'#' * level} {title}\n")
        self.html.append(f"<h{level}>{escape(title)}</h{level}>")

    def paragraph(self, text):
        self.md.append(text.replace(UCI_URL, f"[UCI MetroPT-3 — bảng biến]({UCI_URL})") + "\n")
        linked = escape(text).replace(escape(UCI_URL), f'<a href="{UCI_URL}">UCI MetroPT-3 — bảng biến</a>')
        self.html.append(f"<p>{linked}</p>")

    def table(self, frame, index=False):
        frame = frame.reset_index() if index else frame.copy()
        def fmt(value):
            if isinstance(value, (float, np.floating)):
                return "—" if pd.isna(value) else f"{value:,.6f}".rstrip("0").rstrip(".")
            return str(value)
        rows = [[fmt(v) for v in row] for row in frame.itertuples(index=False, name=None)]
        self.md.append("\n".join(["| " + " | ".join(map(str, frame.columns)) + " |",
                                  "| " + " | ".join(["---"] * len(frame.columns)) + " |"] +
                                 ["| " + " | ".join(row) + " |" for row in rows]) + "\n")
        self.html.append('<div class="table-wrap"><table><thead><tr>' +
                         "".join(f"<th>{escape(str(c))}</th>" for c in frame.columns) +
                         "</tr></thead><tbody>" + "".join("<tr>" + "".join(f"<td>{escape(v)}</td>" for v in row) + "</tr>" for row in rows) + "</tbody></table></div>")

    def figure(self, path, caption):
        self.md.append(f"![{caption}](figures/{path.name})\n\n{caption}\n")
        data = base64.b64encode(path.read_bytes()).decode("ascii")
        self.html.append(f'<figure><img src="data:image/png;base64,{data}" alt="{escape(caption)}"><figcaption>{escape(caption)}</figcaption></figure>')

    def write(self, output):
        (output / "report.md").write_text("\n".join(self.md), encoding="utf-8")
        css = """body{margin:0;background:#f3f6f8;color:#18313d;font:16px/1.65 'Segoe UI',Arial,sans-serif}main{max-width:1200px;margin:auto;padding:40px;background:white}h1{font-size:32px;line-height:1.2}h2{margin-top:48px;border-bottom:2px solid #d9e7eb;padding-bottom:8px}p{max-width:100ch}img{width:100%;height:auto}figure{margin:28px 0}figcaption{color:#526773;font-size:14px}table{border-collapse:collapse;font-size:14px;white-space:nowrap;width:100%}td,th{padding:8px 12px;border-bottom:1px solid #dae4e8;text-align:left}th{background:#eaf2f5}tr:nth-child(even){background:#f7fafb}.table-wrap{overflow:auto;margin:20px 0}a{color:#176c8c}@media print{main{padding:0}figure, tr{break-inside:avoid}}"""
        (output / "report.html").write_text('<!doctype html><html lang="vi"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>PB06 — EDA train MetroPT-3</title><style>' + css + '</style><main>' + "\n".join(self.html) + '</main></html>', encoding="utf-8")


def build_report(a: dict, figures: dict, source: Path, provenance: dict) -> Report:
    r = Report()
    t, f = a["train"], a["frequencies"]
    p, s, stats = a["pearson"], a["spearman"], a["stats"]
    r.heading("PB06 — Khám phá dữ liệu train MetroPT-3", 1)
    r.paragraph("Mục tiêu: hiểu phân phối, biến động theo thời gian và quan hệ giữa các tín hiệu trước khi xây detector. Mọi số liệu và lựa chọn đoạn minh họa dưới đây chỉ dùng train; chưa có kết quả huấn luyện hay chấm điểm bất thường.")
    r.heading("1. Những điểm đáng chú ý")
    r.paragraph(f"TP3 và Reservoirs gần trùng nhau: Pearson={p.loc['TP3', 'Reservoirs']:.6f}, Spearman={s.loc['TP3', 'Reservoirs']:.6f}. Đây là bằng chứng về mức độ trùng thông tin trên train, chưa phải quyết định bỏ cột.")
    r.paragraph(f"TP2 và H1 có Pearson={p.loc['TP2', 'H1']:.6f}, nhưng Spearman={s.loc['TP2', 'H1']:.6f}. Hai chỉ số khác nhau mạnh; cần đọc cùng scatter và trạng thái digital, thay vì mô tả chúng bằng một quan hệ đơn điệu duy nhất.")
    def state_median(signal, value, sensor):
        frame = a["state_stats"]
        found = frame.loc[frame.signal.eq(signal) & frame.value.eq(value), f"{sensor}_median"]
        return f"{found.iloc[0]:.4f}" if len(found) else "không có quan sát"
    r.paragraph(f"Motor_current khác rõ theo COMP: median khi COMP=0 là {state_median('COMP', 0, 'Motor_current')} A; khi COMP=1 là {state_median('COMP', 1, 'Motor_current')} A. Một ngưỡng duy nhất trên dữ liệu trộn trạng thái có thể phản ánh khác biệt chế độ; đây là giả thuyết cần kiểm tra sau này.")
    constants = [c for c in DIGITAL_COLUMNS if t[c].nunique() == 1]
    r.paragraph("Digital hằng trên train: " + (", ".join(f"{c}={int(t[c].iloc[0])}" for c in constants) or "không có") + ". Chưa có bằng chứng từ train về hành vi ở giá trị còn lại; báo cáo không sửa schema hay feature.")
    rare = f.loc[f['count'].gt(0)].sort_values(["count", "sensor", "value"]).iloc[0]
    r.paragraph(f"Trạng thái ít quan sát nhất là {rare.sensor}={int(rare.value)}: {int(rare['count']):,} dòng ({rare.percent:.6f}%). Tần suất hiếm không tự chứng minh lỗi; xem đoạn chi tiết và giới hạn nhãn ở cuối báo cáo.")

    r.heading("2. Phạm vi dữ liệu và chất lượng")
    r.table(pd.DataFrame([
        ("Đầu vào", source.as_posix()), ("Dataset version", provenance.get("dataset_version", "không có")),
        ("CSV SHA-256", provenance.get("csv_sha256", "không có")),
        ("Config hash", provenance["config_hash"]), ("Train kết thúc trước", a["boundary"]),
        ("Khoảng quan sát hợp lệ", f"{t.timestamp.min()} → {t.timestamp.max()}"),
        ("Dòng train trước quality mask", a["train_rows_before_quality"]),
        ("Dòng bị loại do valid=false/null", a["quality_excluded"]),
        ("Dòng train dùng phân tích", len(t)), ("Số segment có quan sát hợp lệ", t.segment_id.nunique()),
        ("Nhịp mode từ train (giây)", a["cadence_seconds"]),
        ("Ngưỡng gap: delta > (giây)", a["gap_break_seconds"]),
        ("Số gap trong train trước quality mask", len(a["gaps"])),
    ], columns=["Thông tin", "Giá trị"]))
    r.table(pd.DataFrame(a["quality"].items(), columns=["Quality flag trong cleaned train", "Số dòng (có thể chồng lấp)"]))
    r.paragraph("Quality mask dùng cột valid của PB03; không fill và không xóa analog âm hoặc cực trị hợp lệ. Những dòng đã bị audit loại vì timestamp lỗi/trùng/xung đột không có trong cleaned: xem data card PB03/PB05 cho sổ audit toàn nguồn. Báo cáo này chỉ đếm quality flags còn trong cleaned train.")
    r.paragraph("Đơn vị analog: áp suất bar, nhiệt độ °C, dòng điện A; digital là giá trị nhị phân không đơn vị. Nguồn đơn vị: " + UCI_URL + ". Đồng hồ timestamp gốc không có múi giờ. Tần suất là tỷ lệ theo quan sát, không phải phần trăm thời gian do nhịp không hoàn toàn đều và có gap.")
    r.paragraph("EDA mô tả các quan sát cảm biến hợp lệ, nên không áp warm-up/purge của lưới cửa sổ PB05 lên raw. temporal_valid trong minute_grid là điều kiện thời gian cho mốc chấm điểm, không phải quality mask của dòng raw; validity cuối cùng của feature thuộc PB07.")

    r.heading("3. Phân phối 7 analog")
    r.table(stats[["unit", "count", "mean", "std", "min", "1%", "25%", "50%", "75%", "99%", "max"]].rename_axis("sensor"), index=True)
    r.paragraph("std trong bảng dùng ddof=1 theo describe của pandas và chỉ phục vụ EDA; công thức feature PB07 vẫn theo config. Histogram dùng 80 bin trên toàn bộ train hợp lệ, không cắt miền; các đuôi rất ít quan sát có thể khó nhìn ở thang đếm tuyến tính. Boxplot dùng râu 1,5×IQR; điểm ngoài râu chỉ là mô tả thống kê.")
    r.figure(figures["analog_histograms"], "Histogram của toàn bộ 7 analog trên train hợp lệ.")
    r.figure(figures["analog_boxplots"], "Boxplot cùng miền giá trị đầy đủ, giữ điểm cực trị.")
    r.paragraph(f"Motor_current có median={stats.loc['Motor_current', '50%']:.4f} A, Q3={stats.loc['Motor_current', '75%']:.4f} A và P99={stats.loc['Motor_current', '99%']:.4f} A: phần lớn quan sát ở mức thấp nhưng có một nhóm mức cao. TP2 có median={stats.loc['TP2', '50%']:.4f} bar và P99={stats.loc['TP2', '99%']:.4f} bar. Các phân phối trộn mức này cần được đối chiếu với digital.")
    r.paragraph(f"DV_pressure có P99={stats.loc['DV_pressure', '99%']:.4f} bar nhưng max={stats.loc['DV_pressure', 'max']:.4f} bar: tồn tại đuôi dương ít quan sát. Chưa có căn cứ để loại các giá trị đó hoặc gọi là lỗi cảm biến.")

    r.heading("4. Tín hiệu digital và trạng thái hiếm")
    r.table(f)
    r.figure(figures["digital_frequency"], "Tỷ lệ từng giá trị 0/1 của 8 digital; bảng phía trên giữ số đếm chính xác cho trạng thái rất hiếm.")
    r.paragraph(f"COMP và MPG bằng nhau ở {t.COMP.eq(t.MPG).mean() * 100:.6f}% quan sát train; COMP và DV_eletric khác nhau ở {t.COMP.ne(t.DV_eletric).mean() * 100:.6f}%. Các tỷ lệ này là quan sát trên train, không phải quy luật chắc chắn cho dữ liệu mới.")
    rare_rows = f.loc[f['count'].between(1, max(1, int(len(t) * .001)))]
    for row in rare_rows.itertuples(index=False):
        hits = t.loc[t[row.sensor].eq(row.value)]
        r.paragraph(f"{row.sensor}={row.value}: {row.count:,} dòng, từ {hits.timestamp.min()} đến {hits.timestamp.max()}. Hai mốc chỉ là đầu/cuối quan sát, không khẳng định trạng thái kéo dài liên tục.")

    r.heading("5. Xu hướng và độ phủ theo ngày")
    r.figure(figures["daily_timeline"], "Mỗi ngày: median và dải P10–P90, tính từ tất cả quan sát hợp lệ; không nội suy ngày thiếu.")
    d = a["daily"]
    temp = d.Oil_temperature_median.dropna()
    r.paragraph(f"Median Oil_temperature theo ngày nằm trong {temp.min():.3f}–{temp.max():.3f} °C; thấp nhất ngày {temp.idxmin():%d/%m/%Y}, cao nhất ngày {temp.idxmax():%d/%m/%Y}. Các median tăng/giảm theo từng đoạn; biểu đồ mô tả biến động, chưa đủ để kết luận có xu hướng suy giảm thiết bị hay chu kỳ ổn định.")
    missing = d.index[d.valid_rows.eq(0)]
    r.paragraph("Ngày không có dòng hợp lệ trong lịch train: " + (", ".join(day.strftime("%d/%m/%Y") for day in missing) or "không có") + ". Ngày ít quan sát có thể có phân phối khác do thiếu một phần trạng thái; không so median mà bỏ qua số dòng.")
    r.table(d[["valid_rows", "Oil_temperature_median", "Motor_current_median", "TP3_median"]].reset_index())
    r.paragraph(f"Train có {len(a['gaps'])} gap dài hơn {a['gap_break_seconds']:g} giây; gap dài nhất là {a['gaps'].seconds.max():,.0f} giây. Tổng số mẫu không chứng minh độ phủ liên tục. Danh sách gap được lưu ở tables/train_gaps.csv.")

    r.heading("6. Tương quan và giới hạn diễn giải")
    r.figure(figures["correlations"], "Pearson và Spearman của toàn bộ 15 sensor; cột hằng có tương quan không xác định, để trống.")
    pairs = [("TP3", "Reservoirs"), ("TP2", "H1"), ("TP3", "H1"),
             ("TP2", "Motor_current"), ("Oil_temperature", "DV_pressure"), ("COMP", "MPG")]
    r.table(pd.DataFrame([{"sensor_1": l, "sensor_2": rr, "Pearson": p.loc[l, rr], "Spearman": s.loc[l, rr]} for l, rr in pairs]))
    r.figure(figures["sampled_scatter"], "Scatter minh họa hai cặp áp suất; lấy mẫu riêng từng ngày, không dùng sample để tính tương quan.")
    r.paragraph("Pearson nhạy với biên độ và các nhóm mức cách xa nhau; Spearman dùng thứ hạng và xử lý ties bằng thứ hạng trung bình. Với TP2/H1, nhóm trạng thái khác nhau có thể chi phối Pearson trong khi thứ hạng bên trong các nhóm có hành vi khác. Đây là giả thuyết từ scatter, cần phân tích theo trạng thái nếu mở rộng.")
    r.paragraph("Chuỗi thời gian có phụ thuộc giữa các dòng; đây không phải kiểm định với các quan sát độc lập. Tương quan không xác nhận nhân quả hay cảm biến dư thừa trong mọi chế độ. Không tính p-value, không tự loại cột và không diễn giải ô trống của cột hằng thành tương quan bằng 0.")

    r.heading("7. Đối chiếu analog với COMP / DV_eletric / Towers")
    r.table(a["state_stats"][["signal", "value", "count", "percent", "Motor_current_median", "TP2_median", "TP3_median", "H1_median", "DV_pressure_median"]])
    r.figure(figures["analog_by_state"], "Boxplot analog theo từng giá trị digital; dữ liệu đầy đủ, không cân bằng lại tỷ lệ nhóm.")
    r.table(a["combinations"])
    r.paragraph("Ba digital này phụ thuộc mạnh vào nhau trên train, nên khác biệt khi nhóm riêng theo Towers không chứng minh Towers gây thay đổi dòng điện. Báo cáo dùng COMP=0/1, DV_eletric=0/1, Towers=0/1 làm tên trạng thái; không gán tên cơ học chỉ từ giá trị.")
    r.figure(figures["detail_transition"], "Đoạn ±10 phút quanh chuyển COMP đầu tiên có hai quan sát liên tiếp cùng segment. Digital vẽ step để minh họa, không dùng làm dữ liệu fill.")
    r.figure(figures["detail_rare"], "Đoạn ±10 phút quanh quan sát đầu tiên của trạng thái digital có số đếm dương nhỏ nhất; hòa chọn theo tên cột rồi giá trị.")

    r.heading("8. Cách chạy lại và giới hạn kết luận")
    r.paragraph(f"Seed={a['seed']}; mỗi ngày lấy tối đa {a['per_day']} quan sát hợp lệ không hoàn lại bằng numpy.default_rng, duyệt ngày tăng dần và dữ liệu sắp theo timestamp/raw_row_id. Sample có {len(a['sample']):,} dòng trên {len(a['sampling'])} ngày có quan sát. Bảng sampling_by_day.csv lưu số lượng từng ngày; code đủ để dựng lại cùng sample, không cần manifest ID.")
    r.paragraph("Thống kê, histogram, boxplot, tương quan và bảng trạng thái dùng toàn bộ train hợp lệ. Chỉ scatter dùng sample. Timeline ngày aggregate để vẽ; chi tiết dùng raw. Không đưa bảng aggregate/sample của báo cáo vào pipeline feature.")
    r.paragraph('Chạy từ root repo: .\\.venv\\Scripts\\python.exe scripts/pb06_train_eda.py --config configs/base.yaml --cleaned data/interim/pb05-verified-20261025/cleaned.parquet --output docs/examples/pb06')
    r.paragraph("Script: scripts/pb06_train_eda.py. Bảng máy đọc: tables/*.csv. provenance.json ghi dữ liệu, config và phiên bản thư viện. Báo cáo HTML nhúng toàn bộ ảnh nên có thể mở độc lập; Markdown tham chiếu thư mục figures/.")
    r.paragraph("Train chỉ bao phủ tháng đầu và không có sự cố được báo cáo trong giai đoạn này theo events.csv của PB04; ngoài khoảng sự cố không đồng nghĩa được xác nhận hoàn toàn khỏe. EDA chưa chứng minh khả năng phát hiện sự cố. Không dùng validation/test để chọn nhận xét, sample, cửa sổ minh họa hoặc sửa feature. PCA/K-Means, fit preprocessing và mô hình được thực hiện ở các PB tiếp theo.")
    return r


def generate(cleaned: pd.DataFrame, config, source: Path, output: Path, per_day=300):
    a = analyze(cleaned, config.as_dict(), per_day)
    output.mkdir(parents=True, exist_ok=True)
    tables = output / "tables"
    tables.mkdir(exist_ok=True)
    for name, key, index in [
        ("analog_statistics", "stats", True), ("digital_frequency", "frequencies", False),
        ("daily_summary", "daily", True), ("pearson", "pearson", True),
        ("spearman", "spearman", True), ("analog_by_state", "state_stats", False),
        ("state_combinations", "combinations", False), ("sampling_by_day", "sampling", False),
        ("train_gaps", "gaps", False),
    ]:
        a[key].to_csv(tables / f"{name}.csv", index=index, encoding="utf-8", float_format="%.12g")
    audit = cleaned.attrs.get("audit", {})
    provenance = {k: audit.get(k) for k in ["dataset_version", "csv_sha256"]}
    provenance.update(config_hash=config.config_hash, config=config.as_dict(), source=source.as_posix(),
                      seed=a["seed"], train_rows=len(a["train"]), sample_rows=len(a["sample"]),
                      quality_excluded=a["quality_excluded"],
                      versions={"python": platform.python_version(), "pandas": pd.__version__,
                                "numpy": np.__version__, "matplotlib": matplotlib.__version__, "seaborn": sns.__version__})
    provenance["code"] = {
        "git_commit": subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip(),
        "dirty": bool(subprocess.check_output(["git", "status", "--porcelain"], cwd=ROOT, text=True).strip()),
    }
    (output / "provenance.json").write_text(json.dumps(provenance, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    figures = plot_figures(a, output)
    build_report(a, figures, source, provenance).write(output)
    return a


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", type=Path, default=ROOT / "configs/base.yaml")
    parser.add_argument("--cleaned", type=Path, default=ROOT / "data/interim/pb05-verified-20261025/cleaned.parquet")
    parser.add_argument("--output", type=Path, default=ROOT / "docs/examples/pb06")
    parser.add_argument("--sample-per-day", type=int, default=300)
    args = parser.parse_args()
    config = load_config(args.config)
    try:
        source = args.cleaned.resolve().relative_to(config.project_root)
    except ValueError:
        source = args.cleaned.resolve()
    result = generate(pd.read_parquet(args.cleaned), config, source, args.output, args.sample_per_day)
    print(json.dumps({"report": str(args.output / "report.html"), "train_rows": len(result["train"]),
                      "sample_rows": len(result["sample"])}, ensure_ascii=False))


if __name__ == "__main__":
    main()
