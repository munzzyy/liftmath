# liftmath i18n glossary

Core lifting-term glossary for the 6 Stage 1 proof locales (es, de, ru, ja,
zh-Hans, ar), plus the exact checklist for adding one of the ~26 remaining
Stage 2 locales.

## Do-not-translate list (byte-identical in every locale file)

These tokens stay exactly as written, in every language, in every locale
file (`web/js/i18n/*.js`). They are how lifters worldwide actually write
them - translating them would make the app *harder* to read for a native
speaker, not easier.

- **Abbreviations**: `1RM`, `RIR`, `RPE`, `AMRAP`, `MV`, `MEV`, `MAV`, `MRV`,
  `TDEE`, `FFMI`, `BMR`
- **Proper nouns**: `Wilks`, `DOTS`, `IPF GL`, `McCulloch`, `Mifflin`,
  `Cunningham`, `Garthe`, `Foster`, `Ebben`
- **Program names**: `5/3/1`, `GZCLP`, `nSuns`
- **Unit symbols**: `kg`, `lb`, `kcal`

Note: `RPE` is listed here as a general lifting-terminology abbreviation for
completeness (a future Stage 2 feature might use it), but liftmath's actual
UI copy today only ever uses `RIR`, never `RPE` - don't be surprised if you
don't find it in any locale file's values.

A locale file that translates any of these has a bug - see
`tests/web/i18n-keys.test.mjs`'s heuristic check.

## Core term glossary (25 terms x 6 locales)

Legend: a term marked **(EN-in-context)** means that language's lifting
community commonly borrows the English word/abbreviation in casual use even
though a native translation exists - both are valid; the table gives the
term this app actually uses in the UI (the one a lifter in that language
would expect to read, not necessarily the most literal option).

| # | English | Spanish (es) | German (de) | Russian (ru) | Japanese (ja) | Simplified Chinese (zh-Hans) | Arabic (ar) |
|---|---|---|---|---|---|---|---|
| 1 | deadlift | peso muerto | Kreuzheben | становая тяга (stanovaya tyaga) | デッドリフト (deddorifuto) **(EN-in-context)** | 硬拉 (yìnglā) | الرفعة الميتة (ar-rafʻa al-mayyita) |
| 2 | squat | sentadilla | Kniebeuge | присед (присед / приседания, prised) | スクワット (sukuwatto) **(EN-in-context)** | 深蹲 (shēndūn) | القرفصاء (al-qurfusāʼ) |
| 3 | bench press | press de banca | Bankdrücken | жим лёжа (zhim lyozha) | ベンチプレス (benchipuresu) **(EN-in-context)** | 卧推 (wòtuī) | ضغط البنش (ḍaghṭ al-banish) **(EN-in-context)** |
| 4 | overhead press | press militar | Schulterdrücken / Overhead Press **(EN-in-context)** | жим стоя (zhim stoya) | オーバーヘッドプレス (ōbāheddo puresu) **(EN-in-context)** | 推举 (tuījǔ) | الضغط العلوي (aḍ-ḍaghṭ al-ʻulwī) |
| 5 | rep | repetición | Wiederholung | повторение (povtoreniye) | レップ (reppu) **(EN-in-context)** | 次 / 个 (cì / gè) | تكرار (takrār) |
| 6 | set | serie | Satz | подход (podkhod) | セット (setto) **(EN-in-context)** | 组 (zǔ) | مجموعة (majmūʻa) |
| 7 | hard set | serie efectiva/al fallo | harter Satz / Arbeitssatz | рабочий подход (rabochiy podkhod) | ハードセット (hādosetto) **(EN-in-context)** | 有效组 (yǒuxiào zǔ) | مجموعة فعّالة (majmūʻa faʻʻāla) |
| 8 | bodyweight | peso corporal | Körpergewicht | собственный вес (sobstvennyy ves) | 体重 (taijū) | 体重 (tǐzhòng) | وزن الجسم (wazn al-jism) |
| 9 | training max (TM) | máximo de entrenamiento | Trainingsmaximum | тренировочный максимум | トレーニングマックス (TM) | 训练最大重量 (TM) | الحد الأقصى التدريبي (TM) |
| 10 | plate | disco | Gewichtsscheibe | блин (blin) | プレート (purēto) **(EN-in-context)** | 杠铃片 (gànglíng piàn) | قرص وزن (qurṣ wazn) |
| 11 | barbell | barra | Langhantel | штанга (shtanga) | バーベル (bāberu) | 杠铃 (gànglíng) | البار / بار الأوزان (al-bār) **(EN-in-context)** |
| 12 | deload | descarga | Deload **(EN-in-context)** / Entlastungswoche | разгрузка (razgruzka) | ディロード (dirōdo) **(EN-in-context)** | 减载 (jiǎnzài) | تخفيف الحمل (takhfīf al-ḥiml) |
| 13 | mesocycle | mesociclo | Mesozyklus | мезоцикл (mezotsikl) | メゾサイクル (mezosaikuru) | 中周期 (zhōng zhōuqī) | الدورة المتوسطة (ad-dawra al-mutawassiṭa) |
| 14 | cut (goal) | definición | Diät / Cut **(EN-in-context)** | сушка (sushka) | 減量 (genryō) | 减脂 (jiǎnzhī) | تنشيف (tanshīf) |
| 15 | bulk (goal) | volumen | Aufbau / Bulk **(EN-in-context)** | набор массы (nabor massy) | 増量 (zōryō) | 增肌 (zēngjī) | تضخيم (taḍkhīm) |
| 16 | maintain (goal) | mantenimiento | Erhaltung | поддержание (podderzhaniye) | 維持 (iji) | 维持 (wéichí) | الحفاظ على الوزن (al-ḥifāẓ ʻalā al-wazn) |
| 17 | recomp (goal) | recomposición | Rekomposition | рекомпозиция (rekompozitsiya) | リコンプ (rikonpu) **(EN-in-context)** | 体重重组 (tǐzhòng chóngzǔ) | إعادة التشكيل (iʻādat at-tashkīl) |
| 18 | added weight | peso añadido | Zusatzgewicht | дополнительный вес | 追加重量 (tsuika jūryō) | 附加重量 (fùjiā zhòngliàng) | الوزن الإضافي (al-wazn al-iḍāfī) |
| 19 | pull-up | dominada (pronada) | Klimmzug | подтягивание (podtyagivaniye) | 懸垂 (kensui) | 引体向上 (yǐntǐ xiàngshàng) | العقلة (al-ʻuqla) |
| 20 | dip | fondos | Dip **(EN-in-context)** / Stützstemmen | отжимания на брусьях | ディップス (dippusu) **(EN-in-context)** | 双杠臂屈伸 (shuānggàng bìqūshēn) | متوازي (mutawāzī) |
| 21 | chin-up | dominada (supinada) | Klimmzug (Untergriff) | подтягивание обратным хватом | チンニング (chinningu) **(EN-in-context)** | 反握引体向上 (fǎnwò yǐntǐ xiàngshàng) | العقلة بقبضة معكوسة |
| 22 | sex (formula input) | sexo | Geschlecht | пол (pol) | 性別 (seibetsu) | 性别 (xìngbié) | الجنس (al-jins) |
| 23 | muscle group | grupo muscular | Muskelgruppe | группа мышц (gruppa myshts) | 筋肉群 (kinniku-gun) | 肌肉群 (jīròu qún) | مجموعة عضلية (majmūʻa ʻaḍaliyya) |
| 24 | achievable | alcanzable | erreichbar | достижимо (dostizhimo) | 達成可能 (tassei kanō) | 可达到 (kě dádào) | قابل للتحقيق (qābil lit-taḥqīq) |
| 25 | remainder / shortfall | restante / faltante | Rest / Fehlbetrag | остаток / нехватка | 残り / 不足 (nokori / fusoku) | 剩余 / 差额 (shèngyú / chā'é) | المتبقي / النقص (al-mutabaqqī / an-naqṣ) |

Notes on choices that aren't the most literal option:

- **German "cut"/"bulk"/"deload"**: German lifting forums (Fitness-Board,
  r/Fitness_de) use the English loanwords as often as the native terms in
  casual speech; this app uses the native term as the primary UI string
  (`Diät`, `Aufbau`, `Entlastungswoche`) since it reads as intentional
  writing rather than code-switching, but the loanword is a fully acceptable
  alternate if a future locale update prefers it.
- **Japanese lifting vocabulary** leans heavily on English loanwords
  (katakana) for gym-specific terms (スクワット, ベンチプレス, セット) - this
  mirrors how Japanese lifters actually talk, not a translation shortcut.
  Native kanji/wago terms exist for bodyweight/percentage/muscle-group
  vocabulary and are used there instead.
- **Arabic** has real regional variation in gym vocabulary (Gulf vs. Levant
  vs. Egypt often differ, and English loanwords are extremely common in gym
  contexts across all of them). This app uses Modern Standard Arabic (MSA)
  spellings with the widely-understood loanword where one dominates
  (`بنش` for bench, `بار` for barbell) since a single MSA UI needs to read
  naturally across dialects, not target one region's slang.
- **Russian "сушка"/"набор массы"**: these are the actual terms Russian
  lifting communities use for cut/bulk (literally "drying"/"gaining mass"),
  not calques of the English words - a literal "резка" (cutting) would read
  as machine-translated.

## Stage 2 handoff: adding one new locale file

1. **Copy the template.** Copy `web/js/i18n/en.js` to
   `web/js/i18n/<code>.js` (use the exact BCP-47-ish code from the canonical
   list below - it must match the key you'll add to `REGISTRY`/`AUTONYMS` in
   step 3).
2. **Translate every value, key-for-key.** Keep every key name and every
   `{placeholder}` token exactly as in `en.js` - only the string *values*
   change. Do NOT add, remove, or rename any key.
   - Apply the do-not-translate list above (abbreviations, proper nouns,
     program names, unit symbols) - leave those substrings untouched inside
     otherwise-translated sentences.
   - Use this GLOSSARY's per-term choices for the 6 locales already done as
     a style reference for tone/register even if translating a 7th
     language - idiomatic and native-quality, not stiff or calqued.
   - If translating a language not yet in this glossary, add a new column
     (or a short prose note) here with your term choices, so the *next*
     locale after yours has the same reference.
3. **Register the locale** in `web/js/i18n/index.js`:
   - Add `<code>: () => import("./<code>.js"),` to `REGISTRY`.
   - Add `<code>: "<Autonym>",` to `AUTONYMS` (the language's own name for
     itself, e.g. `"Deutsch"`, `"日本語"` - not the English name).
   - If the locale is RTL (Hebrew `he`, Persian `fa` are in the canonical
     Stage 2 list), add it to the `RTL_LOCALES` set too.
4. **Precache it**: add `"./js/i18n/<code>.js"` to `PRECACHE_URLS` in
   `web/sw.js` and bump `CACHE_NAME` (e.g. `liftmath-v3` -> `liftmath-v4`) -
   see that file's own header comment for why the bump is manual.
5. **Verify key parity**: run
   `node --test "tests/web/i18n-keys.test.mjs"` - it asserts every locale
   file (including your new one) exports EXACTLY the same key set as
   `en.js`, and flags values that look untranslated. This must stay green;
   it's what makes a locale-only PR safe to merge without a JS reviewer
   re-checking every key by hand.
6. **Full gate**: `node --test "tests/web/*.test.mjs"` (must stay green -
   adding a locale never touches math, so this is really just confirming
   you didn't break the registry wiring) and a manual spot-check in a
   browser with `?lang=<code>` (or the language switcher) to confirm the
   layout doesn't break - RTL locales in particular need a visual check
   (numbers/units still read LTR embedded in RTL text is expected and
   correct, not a bug).

### Canonical Stage 2 locale list (still to fill)

`pt-BR`, `fr`, `it`, `nl`, `pl`, `sv`, `nb`, `da`, `fi`, `cs`, `ro`, `hu`,
`tr`, `tl`, `id`, `vi`, `uk`, `el`, `zh-Hant`, `ko`, `hi`, `bn`, `th`, `he`,
`fa`

Of these, **`he` (Hebrew) and `fa` (Persian) are RTL** - add them to
`RTL_LOCALES` in `web/js/i18n/index.js` per step 3 above. Every other locale
in this list is LTR.
