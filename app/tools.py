"""第3回: エージェントに持たせるツール。

ここに書いた関数の docstring と型ヒントが、そのままモデルへの「ツールの説明文」になる。
説明文を書き換えると、モデルがツールを使うかどうか・どんな引数で呼ぶかが変わる。
"""

import json
import random
from functools import cache
from pathlib import Path

DATA_DIR = Path(__file__).resolve().parent.parent / "data"
MAX_RESULTS = 3


@cache
def load_glossary() -> list[dict]:
    with open(DATA_DIR / "glossary.json", encoding="utf-8") as f:
        return json.load(f)["terms"]


def _normalize(text: str) -> str:
    return text.casefold().replace(" ", "").replace("　", "")


def _names(entry: dict) -> list[str]:
    return [_normalize(entry["term"]), _normalize(entry["id"])] + [
        _normalize(a) for a in entry["aliases"]
    ]


def search_glossary(query: str) -> str:
    """講座の用語集から、指定した用語の定義と関連する講義回を検索する。

ユーザーが専門用語の意味や特徴を質問した場合に使用する。
queryには検索する用語を1つ指定する。

復習問題を作成する目的では、原則としてmake_quizを優先する。
    """
    q = _normalize(query)
    if not q:
        return "検索語が空です。調べたい用語を1つ指定してください。"
    glossary = load_glossary()

    exact = [e for e in glossary if q in _names(e)]
    # 「r」のような短い別名が何にでも当たらないよう、名前側が短いものは除く
    partial = [
        e for e in glossary
        if e not in exact and any(q in n or (len(n) >= 3 and n in q) for n in _names(e))
    ]
    in_definition = [
        e for e in glossary
        if e not in exact and e not in partial and q in _normalize(e["definition"])
    ]
    hits = (exact + partial + in_definition)[:MAX_RESULTS]

    if not hits:
        return f"用語集に「{query}」は見つかりませんでした。"
    return json.dumps(
        [
            {
                "term": e["term"],
                "lecture": e["lecture"],
                "definition": e["definition"],
                "related": e["related"],
            }
            for e in hits
        ],
        ensure_ascii=False,
    )


def get_lecture_summary(lecture: int) -> str:
    """指定された講義回の概要と主要な学習内容を取得する。

「第2回では何を学ぶのか」など、講義全体の内容や要点を
質問された場合に使用する。
lectureには講義回を1始まりの整数で指定する。
    """
    path = DATA_DIR / "lectures" / f"{lecture:02d}.md"
    if not path.exists():
        available = sorted(p.stem for p in (DATA_DIR / "lectures").glob("*.md"))
        return f"第{lecture}回の要点はまだありません。用意されている回: {', '.join(available)}"
    return path.read_text(encoding="utf-8")

def make_quiz(lecture: int) -> str:
    """指定した講義回の用語集から復習問題を1問生成する。

ユーザーが「第2回の復習問題を出して」など、
復習問題や理解度確認のクイズを求めた際に必ず使用する。

lectureには対象の講義回を1始まりの整数で指定する。

用語集からランダムに用語を1つ選び、問題(question)と
解答(answer)をJSON形式で返す。

このツールの結果を利用する際は、最初はquestionだけを
表示し、answerはユーザーが解答するまで表示しない。
    """
    # 1. 用語集を読み込む
    glossary = load_glossary()

    # 2. 指定された講義回の用語を抽出する
    terms = [
        entry for entry in glossary
        if entry["lecture"] == lecture
    ]

    # 3. 該当する用語が存在しない場合
    if not terms:
        return f"第{lecture}回の用語は見つかりませんでした。"

    # 4. 用語をランダムに1つ選択する
    selected = random.choice(terms)

    # 5. 問題と解答を作成する
    quiz = {
        "question": f"{selected['term']}とは何ですか？",
        "answer": selected["definition"],
    }

    # 6. JSON形式の文字列として返す
    return json.dumps(quiz, ensure_ascii=False)
