#!/bin/bash
set -euo pipefail
shopt -s nullglob

BASE="$(pwd)/output"
TOOL="$(dirname "$0")/v3-typst"
PY="${VIRTUAL_ENV:-$(dirname "$0")/v3-typst/.venv}/bin/python3"

compile_book() {
    local N=$1 DIR=$2 TITLE=$3 SUBTITLE=$4 COLOR=$5
    local MD_FILE PDF_OUT SIZE
    local -a MD_FILES
    local rc=0

    MD_FILES=("$BASE/$DIR/"*.md)
    if [ "${#MD_FILES[@]}" -eq 0 ]; then
        echo "❌ Book$N: no MD file in $DIR"
        return 1
    fi
    MD_FILE=${MD_FILES[0]}

    PDF_OUT="$BASE/$DIR/ZTurns_Book${N}_${DIR#Book${N}_}.pdf"

    echo "📖 [$N/70] $TITLE — compiling..."
    "$PY" "$TOOL/generate.py" textbook \
        --md "$MD_FILE" \
        --number "$N" \
        --title "$TITLE" \
        --subtitle "$SUBTITLE" \
        --color "$COLOR" \
        --out "$PDF_OUT" 2>&1 | tail -4 || rc=$?

    # pipefail makes rc the compiler's status; a stale PDF must not count as success.
    if [ "$rc" -ne 0 ]; then
        echo "❌ Book$N FAILED (exit $rc)"
        return "$rc"
    fi
    if [ -f "$PDF_OUT" ]; then
        SIZE=$(du -h "$PDF_OUT" | cut -f1)
        echo "✅ Book$N done ($SIZE)"
    else
        echo "❌ Book$N FAILED"
        return 1
    fi
}

failed=0
compile_book 51 "Book51_JobHunter"         "Job Hunter's Chinese"          "求职面试中文实战手册"    "#E53935" || failed=$((failed + 1))
compile_book 52 "Book52_Startup"           "Startup Chinese"               "创业创新中文实战词汇"    "#1565C0" || failed=$((failed + 1))
compile_book 53 "Book53_Negotiation"       "Negotiation Chinese"           "商务谈判中文实战手册"    "#6A1B9A" || failed=$((failed + 1))
compile_book 54 "Book54_Resume"            "Business Chinese Mastery"      "职业发展中文全面提升"    "#2E7D32" || failed=$((failed + 1))
compile_book 55 "Book55_WorkplacePolitics" "Workplace Politics Chinese"    "职场人际关系中文指南"    "#E65100" || failed=$((failed + 1))
compile_book 56 "Book56_Gaming"            "Gaming in Chinese"             "电竞游戏中文词汇大全"    "#1A237E" || failed=$((failed + 1))
compile_book 57 "Book57_Music"             "Music in Chinese"              "音乐娱乐中文词汇全集"    "#880E4F" || failed=$((failed + 1))
compile_book 58 "Book58_Comedy"            "Comedy in Chinese"             "脱口秀喜剧中文词汇"      "#F57F17" || failed=$((failed + 1))
compile_book 59 "Book59_WebNovels"         "Web Novel Chinese"             "网络小说文学中文词汇"    "#4E342E" || failed=$((failed + 1))
compile_book 60 "Book60_VarietyShows"      "Variety Show Chinese"          "综艺节目中文词汇全集"    "#00838F" || failed=$((failed + 1))
compile_book 62 "Book62_Finance"           "Finance in Chinese"            "理财投资中文实战"        "#1565C0" || failed=$((failed + 1))
compile_book 63 "Book63_Fitness"           "Fitness in Chinese"            "健身运动中文词汇"        "#2E7D32" || failed=$((failed + 1))
compile_book 64 "Book64_TravelPhoto"       "Travel Photography Chinese"    "旅行摄影中文实战"        "#6A1B9A" || failed=$((failed + 1))
compile_book 65 "Book65_HomeReno"          "Home Renovation Chinese"       "装修家居中文全攻略"      "#4E342E" || failed=$((failed + 1))
compile_book 66 "Book66_EV"               "Electric Vehicle Chinese"       "新能源汽车中文词汇"      "#00695C" || failed=$((failed + 1))
compile_book 67 "Book67_CleanEnergy"       "Clean Energy Chinese"          "清洁能源中文实战"        "#F57F17" || failed=$((failed + 1))
compile_book 68 "Book68_Robotics"          "Robotics in Chinese"           "机器人AI中文词汇"        "#283593" || failed=$((failed + 1))
compile_book 69 "Book69_Quantum"           "Quantum Tech Chinese"          "量子半导体中文实战"      "#4A148C" || failed=$((failed + 1))
compile_book 70 "Book70_Space"             "Space Exploration Chinese"     "航天探索中文词汇"        "#01579B" || failed=$((failed + 1))
echo ""
if [ "$failed" -gt 0 ]; then
    echo "❌ $failed book(s) failed"
    exit 1
fi
echo "🎉 All done!"
