from __future__ import annotations

import shutil
from datetime import UTC, datetime
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.dates as mdates
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle

from app.schemas.analysis import AnalysisLevel, ChartBar, ChartResponse
from app.schemas.signal import SignalTicket

_KIND_COLORS = {
    "entry": "#d4a017",
    "stop": "#ef5350",
    "target": "#26a69a",
    "invalidation": "#c778d0",
}

_ARTIFACT_ROOTS = (
    Path("/opt/cursor/artifacts"),
    Path("/cursor/stores/self/artifacts"),
)


def artifact_filename(ticket: SignalTicket) -> str:
    stamp = ticket.analyzed_at.astimezone(UTC).strftime("%Y%m%dT%H%M")
    return (
        f"{ticket.symbol.lower()}_{ticket.style}_{ticket.timeframe.lower()}_"
        f"{ticket.action}_{stamp}.png"
    )


def publish_chart_artifact(source: Path, filename: str) -> Path | None:
    """Copy a chart into the cloud artifact folder so Cursor can upload it."""
    for root in _ARTIFACT_ROOTS:
        try:
            if not root.parent.exists() and not root.exists():
                continue
            root.mkdir(parents=True, exist_ok=True)
            dest = root / filename
            shutil.copy2(source, dest)
            return dest
        except OSError:
            continue
    return None


def render_analysis_chart(
    chart: ChartResponse,
    ticket: SignalTicket,
    levels: list[AnalysisLevel],
    last_price: float | None,
    decimals: int,
    output_path: Path,
    yahoo_symbol: str,
    label: str,
) -> Path:
    if not chart.bars:
        raise ValueError("No OHLC bars to plot")

    output_path.parent.mkdir(parents=True, exist_ok=True)
    times = [datetime.fromtimestamp(bar.time, tz=UTC) for bar in chart.bars]
    last = last_price if last_price is not None else chart.bars[-1].close
    width = _bar_width_days(times)

    bg, panel, grid, muted, text = "#12161c", "#181d24", "#1c222b", "#7d8491", "#e8edf4"
    fig, ax = plt.subplots(figsize=(14.5, 8.2), dpi=140)
    fig.patch.set_facecolor(bg)
    ax.set_facecolor(panel)

    _draw_candles(ax, times, chart.bars, width)
    _draw_ema(ax, times, chart.ema20, "#d4a017", "EMA20")
    _draw_ema(ax, times, chart.ema50, "#5b8def", "EMA50")

    xmin = mdates.date2num(times[0])
    xmax = mdates.date2num(times[-1])
    pad = max((xmax - xmin) * 0.02, 0.001)
    ax.set_xlim(xmin - pad, xmax + pad * 8)

    overlay = _overlay_lines(ticket, levels, last, chart, decimals)
    for price, color, caption in overlay:
        style = "-" if caption.lower().startswith("last") else "--"
        ax.axhline(price, color=color, linewidth=1.15, linestyle=style, zorder=1)
        ax.text(
            xmax + pad * 0.4,
            price,
            caption,
            color=color,
            fontsize=8.5,
            va="center",
            ha="left",
        )

    ax.scatter([times[-1]], [last], color=text, s=28, zorder=5, edgecolors=bg, linewidths=0.6)
    action = ticket.action.replace("_", " ").upper()
    ax.set_title(
        f"{label}  {ticket.timeframe}  —  {action}   |   {yahoo_symbol}   |   "
        f"{ticket.analyzed_at.astimezone(UTC).strftime('%d %b %Y')}",
        color=text,
        loc="left",
        fontsize=14,
        pad=12,
    )
    ax.xaxis.set_major_formatter(mdates.DateFormatter("%b %d\n%H:%M"))
    ax.yaxis.set_major_formatter(plt.FuncFormatter(lambda y, _: f"{y:.{decimals}f}"))
    ax.tick_params(colors=muted, labelsize=8)
    for spine in ax.spines.values():
        spine.set_color("#222831")
    ax.grid(True, color=grid, linewidth=0.6)
    legend = ax.legend(loc="upper left", frameon=True, fontsize=8)
    if legend is not None:
        legend.get_frame().set_facecolor("#1a2028")
        legend.get_frame().set_edgecolor("#222831")
        for item in legend.get_texts():
            item.set_color(text)
    badge = "#26a69a" if ticket.action == "long" else "#ef5350"
    ax.text(
        0.99,
        0.04,
        f"{ticket.style.upper()}  ·  {action}",
        transform=ax.transAxes,
        ha="right",
        va="bottom",
        fontsize=11,
        color=badge,
        fontweight="bold",
        bbox={
            "boxstyle": "round,pad=0.35",
            "facecolor": "#152018" if ticket.action == "long" else "#2a1518",
            "edgecolor": badge,
            "linewidth": 1,
        },
    )
    fig.tight_layout()
    fig.savefig(output_path, facecolor=fig.get_facecolor(), bbox_inches="tight")
    plt.close(fig)
    return output_path


def _bar_width_days(times: list[datetime]) -> float:
    if len(times) < 2:
        return 0.02
    seconds = sorted((times[index + 1] - times[index]).total_seconds() for index in range(len(times) - 1))
    median = seconds[len(seconds) // 2]
    return max(median / 86400 * 0.7, 0.0004)


def _draw_candles(ax, times: list[datetime], bars: list[ChartBar], width: float) -> None:
    for stamp, bar in zip(times, bars, strict=True):
        x = mdates.date2num(stamp)
        up = bar.close >= bar.open
        color = "#26a69a" if up else "#ef5350"
        ax.vlines(x, bar.low, bar.high, color=color, linewidth=1.0, zorder=2)
        body_low = min(bar.open, bar.close)
        body_h = max(abs(bar.close - bar.open), (bar.high - bar.low) * 0.04, 1e-8)
        ax.add_patch(
            Rectangle(
                (x - width / 2, body_low),
                width,
                body_h,
                facecolor=color,
                edgecolor=color,
                linewidth=0,
                zorder=3,
            )
        )


def _draw_ema(ax, times: list[datetime], values: list[float | None], color: str, label: str) -> None:
    xs: list[datetime] = []
    ys: list[float] = []
    for stamp, value in zip(times, values, strict=False):
        if value is None:
            continue
        xs.append(stamp)
        ys.append(value)
    if xs:
        ax.plot(xs, ys, color=color, linewidth=1.8, label=label, zorder=4)


def _overlay_lines(
    ticket: SignalTicket,
    levels: list[AnalysisLevel],
    last: float,
    chart: ChartResponse,
    decimals: int,
) -> list[tuple[float, str, str]]:
    lines: list[tuple[float, str, str]] = []
    seen: set[float] = set()

    def fmt(price: float) -> str:
        return f"{price:.{decimals}f}"

    def add(price: float, color: str, caption: str) -> None:
        key = round(price, 8)
        if key in seen:
            return
        seen.add(key)
        lines.append((price, color, caption))

    add(last, "#e8edf4", f"Last {fmt(last)}")
    for level in levels:
        add(level.price, _KIND_COLORS.get(level.kind, "#7d8491"), f"{level.label} {fmt(level.price)}")
    if ticket.action == "no_trade":
        if chart.swing_highs:
            add(chart.swing_highs[-1], "#ef5350", f"Swing high {fmt(chart.swing_highs[-1])}")
        if chart.swing_lows:
            add(chart.swing_lows[-1], "#26a69a", f"Swing low {fmt(chart.swing_lows[-1])}")
    return lines
