"""Matplotlib charts rendered server-side to base64 PNG (no pyplot global state)."""
import base64
import io

from matplotlib.figure import Figure

COLORS = {'Critical': '#B42318', 'High': '#D9730D', 'Medium': '#C9A227', 'Low': '#3B7A57'}
INK = '#1B2B30'
GRID = '#D7DEE1'
ORDER = ['Critical', 'High', 'Medium', 'Low']


def _encode(fig):
    buf = io.BytesIO()
    fig.savefig(buf, format='png', dpi=110, bbox_inches='tight', facecolor='white')
    return base64.b64encode(buf.getvalue()).decode('ascii')


def _style(ax):
    for side in ('top', 'right'):
        ax.spines[side].set_visible(False)
    for side in ('left', 'bottom'):
        ax.spines[side].set_color(GRID)
    ax.tick_params(colors=INK, labelsize=9)
    ax.set_axisbelow(True)


def _empty(ax, msg='No data yet'):
    ax.text(0.5, 0.5, msg, ha='center', va='center', color=INK, transform=ax.transAxes)
    ax.axis('off')


def findings_by_pillar(names, matrix):
    """Stacked horizontal bars: matrix[severity] = list of counts per pillar."""
    fig = Figure(figsize=(6.4, 3.2))
    ax = fig.subplots()
    if not any(sum(v) for v in matrix.values()):
        _empty(ax)
        return _encode(fig)
    left = [0] * len(names)
    for sev in ORDER:
        vals = matrix.get(sev, [0] * len(names))
        ax.barh(names, vals, left=left, color=COLORS[sev], label=sev, height=0.6)
        left = [a + b for a, b in zip(left, vals)]
    ax.invert_yaxis()
    ax.set_xlabel('Open findings', color=INK, fontsize=9)
    ax.legend(frameon=False, fontsize=8, ncol=4, loc='lower center',
              bbox_to_anchor=(0.5, 1.0))
    ax.xaxis.grid(True, color=GRID, linewidth=0.6)
    _style(ax)
    return _encode(fig)


def severity_donut(counts):
    fig = Figure(figsize=(3.4, 3.2))
    ax = fig.subplots()
    vals = [counts.get(s, 0) for s in ORDER]
    if not sum(vals):
        _empty(ax)
        return _encode(fig)
    ax.pie(vals, colors=[COLORS[s] for s in ORDER], startangle=90, counterclock=False,
           wedgeprops={'width': 0.38, 'edgecolor': 'white'})
    ax.text(0, 0, str(sum(vals)), ha='center', va='center', fontsize=18,
            fontweight='bold', color=INK)
    ax.legend([f'{s} ({counts.get(s, 0)})' for s in ORDER], frameon=False, fontsize=8,
              loc='upper center', bbox_to_anchor=(0.5, 0.02), ncol=2)
    return _encode(fig)


def weekly_trend(labels, values):
    fig = Figure(figsize=(5.4, 2.6))
    ax = fig.subplots()
    if not labels:
        _empty(ax)
        return _encode(fig)
    ax.plot(labels, values, color='#12545F', linewidth=2, marker='o', markersize=4)
    ax.fill_between(labels, values, color='#12545F', alpha=0.08)
    ax.set_ylabel('New findings', color=INK, fontsize=9)
    ax.set_ylim(bottom=0)
    ax.yaxis.grid(True, color=GRID, linewidth=0.6)
    fig.autofmt_xdate(rotation=0, ha='center')
    _style(ax)
    return _encode(fig)


def top_techniques(names, counts):
    fig = Figure(figsize=(5.4, 3.0))
    ax = fig.subplots()
    if not names:
        _empty(ax)
        return _encode(fig)
    ax.barh(names, counts, color='#12545F', height=0.6)
    ax.invert_yaxis()
    ax.set_xlabel('Findings', color=INK, fontsize=9)
    ax.xaxis.grid(True, color=GRID, linewidth=0.6)
    _style(ax)
    return _encode(fig)
