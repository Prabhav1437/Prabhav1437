import os
import urllib.request
import json
from datetime import datetime, timedelta
from xml.sax.saxutils import escape

USERNAME = os.environ.get("GITHUB_USERNAME", "Prabhav1437")
TOKEN = os.environ["GITHUB_TOKEN"]

API_URL = "https://api.github.com/graphql"

query = """
query($username: String!) {
  user(login: $username) {
    contributionsCollection {
      contributionCalendar {
        totalContributions
        weeks {
          contributionDays {
            contributionCount
            date
            weekday
          }
        }
      }
    }
  }
}
"""

payload = json.dumps({
    "query": query,
    "variables": {
        "username": USERNAME
    }
}).encode()

request = urllib.request.Request(
    API_URL,
    data=payload,
    headers={
        "Authorization": f"Bearer {TOKEN}",
        "Content-Type": "application/json",
        "User-Agent": "github-activity-graph"
    }
)

with urllib.request.urlopen(request) as response:
    data = json.loads(response.read())

if "errors" in data:
    raise RuntimeError(json.dumps(data["errors"], indent=2))

calendar = data["data"]["user"]["contributionsCollection"]["contributionCalendar"]

weeks = calendar["weeks"]
total = calendar["totalContributions"]

days = []

for week in weeks:
    for day in week["contributionDays"]:
        days.append(day)

# --------------------------------------------------
# SVG configuration
# --------------------------------------------------

CELL = 11
GAP = 3

LEFT = 38
TOP = 38

WEEKS = len(weeks)
ROWS = 7

WIDTH = LEFT + WEEKS * (CELL + GAP) + 20
HEIGHT = TOP + ROWS * (CELL + GAP) + 38

BG = "#0d1117"
TEXT = "#8b949e"
TEXT_BRIGHT = "#c9d1d9"

LEVELS = [
    "#161b22",
    "#0e4429",
    "#006d32",
    "#26a641",
    "#39d353",
]

max_count = max(
    (day["contributionCount"] for day in days),
    default=1
)

def get_level(count):
    if count == 0:
        return 0

    ratio = count / max_count

    if ratio <= 0.25:
        return 1
    elif ratio <= 0.50:
        return 2
    elif ratio <= 0.75:
        return 3
    else:
        return 4


svg = []

svg.append(
    f'<svg xmlns="http://www.w3.org/2000/svg" '
    f'width="{WIDTH}" height="{HEIGHT}" '
    f'viewBox="0 0 {WIDTH} {HEIGHT}">'
)

svg.append(
    f'<rect width="100%" height="100%" rx="8" fill="{BG}"/>'
)

# --------------------------------------------------
# Title
# --------------------------------------------------

svg.append(
    f'<text x="{LEFT}" y="20" '
    f'font-family="Arial, sans-serif" '
    f'font-size="12" font-weight="600" '
    f'fill="{TEXT_BRIGHT}">'
    f'{escape(USERNAME)} — {total} contributions'
    f'</text>'
)

# --------------------------------------------------
# Weekday labels
# --------------------------------------------------

labels = [
    (1, "Mon"),
    (3, "Wed"),
    (5, "Fri"),
]

for row, label in labels:
    y = TOP + row * (CELL + GAP) + 9

    svg.append(
        f'<text x="4" y="{y}" '
        f'font-family="Arial, sans-serif" '
        f'font-size="9" fill="{TEXT}">'
        f'{label}'
        f'</text>'
    )

# --------------------------------------------------
# Contribution cells
# --------------------------------------------------

for week_index, week in enumerate(weeks):

    for day in week["contributionDays"]:

        weekday = day["weekday"]
        count = day["contributionCount"]

        x = LEFT + week_index * (CELL + GAP)
        y = TOP + weekday * (CELL + GAP)

        level = get_level(count)

        date = escape(day["date"])

        svg.append(
            f'<rect '
            f'x="{x}" y="{y}" '
            f'width="{CELL}" height="{CELL}" '
            f'rx="2" '
            f'fill="{LEVELS[level]}">'
            f'<title>{date}: {count} contributions</title>'
            f'</rect>'
        )

# --------------------------------------------------
# Legend
# --------------------------------------------------

legend_y = HEIGHT - 18
legend_x = WIDTH - 145

svg.append(
    f'<text x="{legend_x - 30}" y="{legend_y + 9}" '
    f'font-family="Arial, sans-serif" '
    f'font-size="9" fill="{TEXT}">Less</text>'
)

for i, color in enumerate(LEVELS):

    x = legend_x + i * 15

    svg.append(
        f'<rect x="{x}" y="{legend_y}" '
        f'width="10" height="10" rx="2" '
        f'fill="{color}"/>'
    )

svg.append(
    f'<text x="{legend_x + 85}" y="{legend_y + 9}" '
    f'font-family="Arial, sans-serif" '
    f'font-size="9" fill="{TEXT}">More</text>'
)

svg.append("</svg>")

os.makedirs("assets", exist_ok=True)

with open("assets/activity-graph.svg", "w", encoding="utf-8") as f:
    f.write("\n".join(svg))

print(f"Generated activity graph for {USERNAME}")
print(f"Total contributions: {total}")