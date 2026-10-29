# claim-auditor

Инструмент для аудита утверждений: сравнение формулировок в разных источниках и выявление расхождений.

## Проблема
Современные LLM (ChatGPT, Gemini) уверенно выдают ложные утверждения. Пользователь не может проверить, где ИИ врёт, а где говорит правду. Существующие фактчекеры либо слишком сложны, либо не показывают **расхождения между источниками**.

## Подход
Вместо того чтобы искать «единственно верный ответ», инструмент:
1. Принимает утверждение (например, «Dubai Duty Free — крупнейший в мире»).
2. Ищет его в нескольких источниках (Wikipedia RU, Wikipedia EN).
3. Сравнивает формулировки: если один источник говорит «крупнейший», а другой — «один из крупнейших», выводит оба варианта и помечает расхождение.
4. Даёт пользователю не ответ, а **прозрачность**: «вот что говорит источник А, вот что говорит источник Б».

## Что уже работает
- Поиск статей через Wikipedia API (русская и английская версии).
- Извлечение краткого содержания.
- Обработка ошибок (429 Too Many Requests) через паузы и корректный User-Agent.

## Что не получилось (и почему это важно)
- Wikipedia API ищет по ключевым словам, а не по смыслу. Запрос «Dubai Duty Free» выдаёт теннисный турнир, а не магазин. Это ограничение источника, а не кода.
- Для полноценного аудита нужно добавить новостные API и официальные сайты. Это следующий шаг.

## Как запустить
```bash
pip install requests
python fact_checker.py

## Первый эксперимент: оценка релевантности поиска (ручная разметка)

**Цель:** Проверить, находит ли текущая реализация (Wikipedia API) релевантные статьи для запросов с контекстом и без.

**Метод:** Для трёх запросов был взят Top-1 результат поиска. Человек (автор проекта) вручную присвоил вердикт: `yes` (соответствует), `no` (не соответствует), `unclear` (неоднозначно).

| Запрос | Top-1 статья | Вердикт | Обоснование |
|--------|--------------|---------|-------------|
| Mercury planet | Mercury (planet) | yes | Статья точно соответствует запросу (планета). |
| Pilot HR platform | Honda HR-V (third generation) | no | Это автомобиль, а не HR-платформа. Поиск не понял контекст. |
| Notion app | Notion (productivity software) | yes | Статья точно соответствует приложению. |

**Вывод:** Из трёх запросов два дали правильный Top-1 результат. Провал на `Pilot HR platform` связан с тем, что в Википедии, вероятно, отсутствует статья про HR-платформу Pilot, а поисковый алгоритм цепляется за слова «Pilot» и «HR» в автомобильных статьях. Это **Corpus Gap** (пробел в корпусе данных), а не ошибка ранжирования.

**Ограничение:** Автоматическая оценка с помощью LLM-судьи была исследована (код в репозитории), но не включена в основной процесс из-за проблем с доступом к API (гео-блокировки). Ручная разметка — первый шаг; в будущем планируется вернуться к автоматизации.

## Benchmark v0.1: Manual Evaluation of Search Relevance

**Goal:** Establish a baseline for how the current implementation (Wikipedia API) handles complex user queries.

**Method:** 14 queries across 8 categories were run through the current script (v0.9, without LLM judge). For each query, the Top-1 article was manually evaluated:
- `top1_relevant`: `yes` / `no` / `unclear`
- `error_code`: L0–L7 (see below)

**Error Code Legend:**
- **L0** — Top-1 is topically relevant and directly answers the query.
- **L1** — Negation ignored (e.g., "planets except Mars" → Mars).
- **L2** — Comparison ignored (e.g., "who is faster cheetah or lion" → cartoon).
- **L3** — Typo not corrected (e.g., "Efeleva tower" → unrelated article).
- **L4** — Actual/temporal data ignored (e.g., "dollar rate yesterday" → USSR).
- **L5** — Empty result (0 articles).
- **L6** — Possible corpus gap (article likely absent; not conclusively proven).
- **L7** — Topically relevant but does not answer the specific query (incomplete, wrong synthesis, or partial coverage).

**Results:**

| case_id | category | query | top1 | top1_relevant | error_code | notes |
|---------|----------|-------|------|---------------|------------|-------|
| CTRL-01 | Control | столица Франции | Париж | yes | L0 | Simple query works correctly. |
| NEG-01 | Negation | планеты кроме Марса | Марс | no | L1 | Negation ignored; returned Mars. |
| CMP-01 | Comparison | кто быстрее гепард или лев | Хранитель Лев | no | L2 | Comparison ignored; returned cartoon. |
| CMP-02 | Comparison | кто больше, слон или бегемот | Обыкновенный бегемот | unclear | L7 | Both animals in Top-5, but no direct comparison. |
| TMP-01 | Temporal | президент США 2010 | Список президентов США | unclear | L7 | Year 2010 not reflected in result; not proven ignored by search. |
| NUM-01 | Numeric | население Москвы 2024 | Население Москвы | unclear | L7 | Year 2024 not confirmed in the article. |
| MUL-01 | Multi-step | столица страны с самым большим населением | Токио | no | L7 | Wrong synthesis: India's capital is New Delhi, not Tokyo. |
| TYP-01 | Typo | Эфелева башня | Необычайные приключения Адель Блан-Сек | no | L3 | Typo not corrected; unrelated article. |
| LNG-01 | Mixed language | machine learning по-русски | Journal of Machine Learning Research | unclear | L7 | Relevant topic but not the Russian term. |
| PRE-01 | Superlative | самая высокая гора | Список высочайших вершин Земли | unclear | L7 | Relevant list, but no direct answer (Everest). |
| ACT-01 | Actual data | курс доллара вчера | Союз Советских Социалистических Республик | no | L4 | Actual/temporal data ignored. |
| ABR-01 | Abbreviations | ЕС, ООН, API | Миротворческие силы ООН | unclear | L7 | Partial coverage (UN only); EU and API missing. |
| CTX-01 | Implicit context | что такое квантовый комп | Компьютер | unclear | L7 | Relevant but not about quantum computer. |
| NUM-02 | Counting | первая десятка простых чисел | *0 results* | no | L5 | Empty result. |

**Key Findings:**

1. **Complex queries expose relevance failures.** In this exploratory sample, the Top-1 result was sometimes inconsistent with the user's intent, particularly for negation, comparison, and misspelled queries.
2. **Relevance is not the same as answer completeness.** A result can be topically relevant without answering the specific question. For example, an article about US presidents may be relevant to a query about the president in 2010 without identifying the expected person directly.
3. **The control query succeeded.** The query `столица Франции` returned `Париж` as Top-1, showing that the basic search pipeline works for this simple case.
4. **The results identify areas for further evaluation, not universal performance claims.** The benchmark is small, manually annotated, and based on one search source and one language setting. It does not establish the general capabilities or limitations of Wikipedia search or AI systems.

**Limitations:**
- LLM judge was not used due to API access issues. Evaluation is manual.
- This is an exploratory benchmark, not a representative sample.
- A possible corpus gap was observed earlier (Pilot HR platform) but not included in this set.

**Next Steps:**
- Add an LLM layer to synthesize answers from retrieved articles (future).
- Expand the benchmark with more categories and control queries.
- Document the methodology for reproducibility.
