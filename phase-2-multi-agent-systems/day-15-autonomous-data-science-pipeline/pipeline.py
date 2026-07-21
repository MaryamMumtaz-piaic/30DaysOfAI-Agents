"""Autonomous Data Science Pipeline — six agents on any tabular dataset.

Given a CSV and a target column, the pipeline runs end to end:

  1. Data Profiler    — shape, dtypes, missingness, cardinality, target profile.
  2. Data Cleaner     — drop junk columns, impute nulls, cap outliers.
  3. Feature Engineer — encode categoricals, scale, engineer date parts, select.
  4. Model Selector   — train and cross-validate 5 models on a common split.
  5. Hyperparameter Tuner — grid-search the leaderboard winner.
  6. Report Generator — an LLM narrative + a model card over the real metrics.

Task type (classification vs regression) is inferred from the target. All model
work is deterministic scikit-learn; only the closing narrative uses the LLM, so
the numbers in the report are real. The heavy fit/predict work is dispatched to
a thread so the asyncio event loop stays responsive, and progress is streamed to
the browser over a WebSocket through an async callback.
"""

from __future__ import annotations

import asyncio
import io
import json
import os
import warnings
from typing import Awaitable, Callable

import numpy as np
import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.ensemble import (
    GradientBoostingClassifier,
    GradientBoostingRegressor,
    RandomForestClassifier,
    RandomForestRegressor,
)
from sklearn.impute import SimpleImputer
from sklearn.linear_model import LinearRegression, LogisticRegression, Ridge
from sklearn.model_selection import GridSearchCV, cross_val_score, train_test_split
from sklearn.neighbors import KNeighborsClassifier, KNeighborsRegressor
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler
from sklearn.svm import SVC, SVR
from sklearn.tree import DecisionTreeClassifier, DecisionTreeRegressor

from openai import AsyncOpenAI

warnings.filterwarnings("ignore")

MODEL = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
MAX_ROWS = 20_000           # cap for responsiveness on large uploads
HIGH_CARD_RATIO = 0.95       # drop object columns whose cardinality exceeds 95% (likely IDs)
CLASS_MAX_UNIQUE = 20       # numeric target with <= this many uniques => classification

ProgressFn = Callable[[str, str], Awaitable[None]]


async def _noop(stage: str, message: str) -> None:
    return None


class DataSciencePipeline:
    def __init__(self) -> None:
        key = os.getenv("OPENAI_API_KEY")
        self.openai = AsyncOpenAI(api_key=key) if key else None

    async def run(
        self,
        csv_bytes: bytes,
        target: str = "",
        progress: ProgressFn = _noop,
    ) -> dict:
        df = self._read_csv(csv_bytes)
        if df.shape[0] < 10 or df.shape[1] < 2:
            raise ValueError("Need a dataset with at least 10 rows and 2 columns")

        target = (target or "").strip()
        if not target:
            target = df.columns[-1]
        if target not in df.columns:
            raise ValueError(f"Target column '{target}' not found in the dataset")

        await progress("start", f"Loaded {df.shape[0]} rows × {df.shape[1]} columns")

        # 1. Profile
        await progress("profile", "Data Profiler running exploratory analysis")
        profile = await asyncio.to_thread(self._profile, df, target)

        task_type = profile["task_type"]
        await progress("profile", f"Target '{target}' → {task_type} task")

        # 2. Clean
        await progress("clean", "Data Cleaner handling nulls, outliers, and junk columns")
        df_clean, clean_log = await asyncio.to_thread(self._clean, df, target)

        # 3. Feature engineering
        await progress("features", "Feature Engineer encoding and selecting features")
        X, y, feat_info, preprocessor = await asyncio.to_thread(
            self._features, df_clean, target, task_type
        )

        # 4. Model selection
        await progress("models", "Model Selector training and comparing 5 models")
        leaderboard, split = await asyncio.to_thread(
            self._select_models, X, y, task_type, preprocessor
        )
        best = leaderboard[0]
        await progress(
            "models",
            f"Best: {best['name']} ({best['primary_metric']} = {best['primary_score']})",
        )

        # 5. Tune
        await progress("tune", f"Hyperparameter Tuner optimizing {best['name']}")
        model_card = await asyncio.to_thread(
            self._tune, best["name"], X, y, task_type, preprocessor, split
        )

        result = {
            "target": target,
            "task_type": task_type,
            "profile": profile,
            "cleaning": clean_log,
            "features": feat_info,
            "leaderboard": leaderboard,
            "model_card": model_card,
        }

        # 6. Report narrative (LLM, optional)
        await progress("report", "Report Generator writing insights")
        result["insights"] = await self._insights(result)

        result["stats"] = {
            "rows": profile["rows"],
            "cols": profile["cols"],
            "task_type": task_type,
            "best_model": best["name"],
            "best_metric": best["primary_metric"],
            "best_score": model_card["test_score"],
            "features_used": feat_info["n_features_out"],
        }
        await progress(
            "done",
            f"{best['name']} tuned · test {best['primary_metric']} = {model_card['test_score']}",
        )
        return result

    # ----- 0. IO --------------------------------------------------------------

    def _read_csv(self, csv_bytes: bytes) -> pd.DataFrame:
        try:
            df = pd.read_csv(io.BytesIO(csv_bytes))
        except Exception as exc:
            raise ValueError(f"Could not parse CSV: {exc}")
        if len(df) > MAX_ROWS:
            df = df.sample(MAX_ROWS, random_state=42).reset_index(drop=True)
        # Normalize obviously-empty column names.
        df.columns = [str(c).strip() for c in df.columns]
        return df

    # ----- 1. Profiler --------------------------------------------------------

    def _infer_task(self, s: pd.Series) -> str:
        s = s.dropna()
        if s.empty:
            return "classification"
        # Any non-numeric target (object, string, category, bool) is classification.
        if not pd.api.types.is_numeric_dtype(s) or s.dtype == bool:
            return "classification"
        nunique = s.nunique()
        # Integer-like with few uniques -> classification.
        if nunique <= CLASS_MAX_UNIQUE and float(s.astype(float).apply(float.is_integer).mean()) > 0.99:
            return "classification"
        if nunique <= max(2, int(0.05 * len(s))) and nunique <= CLASS_MAX_UNIQUE:
            return "classification"
        return "regression"

    def _profile(self, df: pd.DataFrame, target: str) -> dict:
        rows, cols = df.shape
        columns = []
        for c in df.columns:
            s = df[c]
            miss = int(s.isna().sum())
            col = {
                "name": c,
                "dtype": str(s.dtype),
                "missing": miss,
                "missing_pct": round(miss / rows * 100, 1) if rows else 0,
                "unique": int(s.nunique(dropna=True)),
            }
            if pd.api.types.is_numeric_dtype(s) and s.notna().any():
                desc = s.describe()
                col.update({
                    "kind": "numeric",
                    "mean": _round(desc.get("mean")),
                    "std": _round(desc.get("std")),
                    "min": _round(desc.get("min")),
                    "max": _round(desc.get("max")),
                })
            else:
                top = s.value_counts(dropna=True).head(3)
                col["kind"] = "categorical"
                col["top_values"] = [{"value": str(k), "count": int(v)} for k, v in top.items()]
            columns.append(col)

        task_type = self._infer_task(df[target])
        target_profile = {"name": target, "task_type": task_type}
        ts = df[target].dropna()
        if task_type == "classification":
            vc = ts.value_counts().head(10)
            target_profile["classes"] = [
                {"label": str(k), "count": int(v), "pct": round(v / len(ts) * 100, 1)}
                for k, v in vc.items()
            ]
            target_profile["n_classes"] = int(ts.nunique())
        else:
            d = ts.astype(float).describe()
            target_profile.update({
                "mean": _round(d.get("mean")), "std": _round(d.get("std")),
                "min": _round(d.get("min")), "max": _round(d.get("max")),
            })

        # Correlations with a numeric target (top drivers).
        correlations = []
        if task_type == "regression":
            num = df.select_dtypes(include=np.number)
            if target in num.columns and num.shape[1] > 1:
                corr = num.corr(numeric_only=True)[target].drop(target).dropna()
                corr = corr.reindex(corr.abs().sort_values(ascending=False).index).head(8)
                correlations = [{"feature": k, "corr": _round(v)} for k, v in corr.items()]

        return {
            "rows": rows, "cols": cols, "task_type": task_type,
            "columns": columns, "target_profile": target_profile,
            "correlations": correlations,
            "duplicate_rows": int(df.duplicated().sum()),
            "total_missing": int(df.isna().sum().sum()),
        }

    # ----- 2. Cleaner ---------------------------------------------------------

    def _clean(self, df: pd.DataFrame, target: str) -> tuple[pd.DataFrame, dict]:
        log: list[str] = []
        df = df.copy()

        before = len(df)
        df = df.drop_duplicates()
        if len(df) < before:
            log.append(f"Removed {before - len(df)} duplicate row(s).")

        # Drop rows missing the target.
        before = len(df)
        df = df.dropna(subset=[target])
        if len(df) < before:
            log.append(f"Dropped {before - len(df)} row(s) with a missing target.")

        dropped_cols = []
        for c in list(df.columns):
            if c == target:
                continue
            # Ensure we do not drop ALL feature columns
            feature_cols_left = [col for col in df.columns if col != target]
            if len(feature_cols_left) <= 1:
                break

            s = df[c]
            # Drop all-null columns.
            if s.isna().all():
                df = df.drop(columns=[c]); dropped_cols.append(f"{c} (all null)"); continue
            # Drop constant columns.
            if s.nunique(dropna=True) <= 1:
                df = df.drop(columns=[c]); dropped_cols.append(f"{c} (constant)"); continue
            # Drop very high-cardinality text columns (likely IDs / free text),
            # but keep date-like columns so the feature engineer can extract parts.
            if not pd.api.types.is_numeric_dtype(s) and s.nunique(dropna=True) > HIGH_CARD_RATIO * len(df):
                if pd.to_datetime(s, errors="coerce").notna().mean() > 0.8:
                    continue
                df = df.drop(columns=[c]); dropped_cols.append(f"{c} (high-cardinality text)"); continue
        if dropped_cols:
            log.append("Dropped columns: " + ", ".join(dropped_cols) + ".")

        # Check if any feature column remains
        feature_cols = [c for c in df.columns if c != target]
        if not feature_cols:
            raise ValueError("No valid feature columns left after data cleaning. Please provide a dataset with at least one non-constant feature column besides target.")

        # Impute + cap outliers on numeric feature columns.
        n_imputed = 0
        n_capped = 0
        for c in df.columns:
            if c == target:
                continue
            s = df[c]
            if pd.api.types.is_numeric_dtype(s):
                if s.isna().any():
                    n_imputed += int(s.isna().sum())
                    df[c] = s.fillna(s.median())
                q1, q3 = df[c].quantile(0.25), df[c].quantile(0.75)
                iqr = q3 - q1
                if iqr > 0:
                    lo, hi = q1 - 1.5 * iqr, q3 + 1.5 * iqr
                    mask = (df[c] < lo) | (df[c] > hi)
                    if mask.any():
                        n_capped += int(mask.sum())
                        df[c] = df[c].clip(lo, hi)
            else:
                if s.isna().any():
                    n_imputed += int(s.isna().sum())
                    mode = s.mode()
                    df[c] = s.fillna(mode.iloc[0] if not mode.empty else "unknown")
        if n_imputed:
            log.append(f"Imputed {n_imputed} missing value(s) (median / mode).")
        if n_capped:
            log.append(f"Capped {n_capped} outlier value(s) to the 1.5×IQR fence.")

        if not log:
            log.append("Dataset was already clean — no changes needed.")

        return df, {
            "log": log,
            "rows_after": len(df),
            "cols_after": df.shape[1],
            "dropped_columns": dropped_cols,
        }

    # ----- 3. Feature Engineer ------------------------------------------------

    def _features(self, df: pd.DataFrame, target: str, task_type: str):
        df = df.copy()
        engineered = []

        # Expand any parseable datetime columns into year/month/dow parts.
        for c in list(df.columns):
            if c == target or pd.api.types.is_numeric_dtype(df[c]):
                continue
            parsed = pd.to_datetime(df[c], errors="coerce")
            if parsed.notna().mean() > 0.8:
                df[f"{c}_year"] = parsed.dt.year
                df[f"{c}_month"] = parsed.dt.month
                df[f"{c}_dow"] = parsed.dt.dayofweek
                df = df.drop(columns=[c])
                engineered.append(f"{c} → {c}_year/_month/_dow")

        y = df[target]
        X = df.drop(columns=[target])
        if X.shape[1] == 0:
            raise ValueError("No feature columns available for model training. Please check your dataset.")

        if task_type == "classification":
            y = y.astype(str)

        num_cols = X.select_dtypes(include=np.number).columns.tolist()
        cat_cols = [c for c in X.columns if c not in num_cols]

        transformers = []
        if num_cols:
            transformers.append(("num", Pipeline([
                ("impute", SimpleImputer(strategy="median")),
                ("scale", StandardScaler()),
            ]), num_cols))
        if cat_cols:
            transformers.append(("cat", Pipeline([
                ("impute", SimpleImputer(strategy="most_frequent")),
                ("ohe", OneHotEncoder(handle_unknown="ignore", max_categories=15, sparse_output=False)),
            ]), cat_cols))
        if not transformers:
            raise ValueError("No numeric or categorical features available after processing.")
        preprocessor = ColumnTransformer(transformers, remainder="drop")

        # Fit once to count output features for the report.
        n_out = 0
        try:
            n_out = preprocessor.fit_transform(X.head(min(len(X), 2000))).shape[1]
        except Exception:
            n_out = len(num_cols) + len(cat_cols)

        feat_info = {
            "numeric": num_cols,
            "categorical": cat_cols,
            "engineered": engineered,
            "n_features_in": X.shape[1],
            "n_features_out": int(n_out),
        }
        return X, y, feat_info, preprocessor

    # ----- 4. Model Selector --------------------------------------------------

    def _models(self, task_type: str, n_samples: int = 100) -> dict:
        k_neighbors = min(5, max(1, n_samples))
        if task_type == "classification":
            return {
                "Logistic Regression": LogisticRegression(max_iter=1000),
                "Decision Tree": DecisionTreeClassifier(random_state=42),
                "Random Forest": RandomForestClassifier(n_estimators=200, random_state=42),
                "Gradient Boosting": GradientBoostingClassifier(random_state=42),
                "KNN": KNeighborsClassifier(n_neighbors=k_neighbors),
            }
        return {
            "Linear Regression": LinearRegression(),
            "Ridge": Ridge(),
            "Decision Tree": DecisionTreeRegressor(random_state=42),
            "Random Forest": RandomForestRegressor(n_estimators=200, random_state=42),
            "Gradient Boosting": GradientBoostingRegressor(random_state=42),
        }

    def _select_models(self, X, y, task_type: str, preprocessor):
        stratify = y if (task_type == "classification" and y.value_counts().min() >= 2) else None
        try:
            X_tr, X_te, y_tr, y_te = train_test_split(
                X, y, test_size=0.2, random_state=42, stratify=stratify
            )
        except Exception:
            X_tr, X_te, y_tr, y_te = train_test_split(
                X, y, test_size=0.2, random_state=42, stratify=None
            )
        scoring = "accuracy" if task_type == "classification" else "r2"
        metric_name = "accuracy" if task_type == "classification" else "R²"

        n_splits = 5
        if task_type == "classification":
            n_splits = int(max(2, min(5, y_tr.value_counts().min())))

        leaderboard = []
        for name, est in self._models(task_type, n_samples=len(X_tr)).items():
            pipe = Pipeline([("prep", preprocessor), ("model", est)])
            try:
                cv = cross_val_score(pipe, X_tr, y_tr, cv=n_splits, scoring=scoring)
                cv_mean, cv_std = float(cv.mean()), float(cv.std())
            except Exception:
                cv_mean, cv_std = float("nan"), 0.0

            try:
                pipe.fit(X_tr, y_tr)
                metrics = self._eval(pipe, X_te, y_te, task_type)
                leaderboard.append({
                    "name": name,
                    "cv_score": _round(cv_mean),
                    "cv_std": _round(cv_std),
                    "primary_metric": metric_name,
                    "primary_score": metrics["primary"],
                    "metrics": metrics["all"],
                })
            except Exception:
                continue

        if not leaderboard:
            raise ValueError("All candidate models failed to train on the dataset.")

        reverse = True  # higher is better for accuracy and R²
        leaderboard.sort(
            key=lambda r: (r["cv_score"] if r["cv_score"] is not None and not _isnan(r["cv_score"]) else -1e9),
            reverse=reverse,
        )
        split = {"X_tr": X_tr, "X_te": X_te, "y_tr": y_tr, "y_te": y_te, "n_splits": n_splits}
        return leaderboard, split

    def _eval(self, pipe, X_te, y_te, task_type: str) -> dict:
        from sklearn.metrics import (
            accuracy_score, f1_score, mean_absolute_error,
            mean_squared_error, precision_score, r2_score, recall_score,
        )
        pred = pipe.predict(X_te)
        if task_type == "classification":
            # Weighted averaging works for binary and multiclass alike and avoids
            # pos_label ambiguity when labels are strings.
            avg = "weighted"
            acc = accuracy_score(y_te, pred)
            return {
                "primary": _round(acc),
                "all": {
                    "accuracy": _round(acc),
                    "precision": _round(precision_score(y_te, pred, average=avg, zero_division=0)),
                    "recall": _round(recall_score(y_te, pred, average=avg, zero_division=0)),
                    "f1": _round(f1_score(y_te, pred, average=avg, zero_division=0)),
                },
            }
        r2 = r2_score(y_te, pred)
        rmse = float(np.sqrt(mean_squared_error(y_te, pred)))
        return {
            "primary": _round(r2),
            "all": {
                "r2": _round(r2),
                "rmse": _round(rmse),
                "mae": _round(mean_absolute_error(y_te, pred)),
            },
        }

    # ----- 5. Tuner -----------------------------------------------------------

    def _param_grid(self, name: str, n_samples: int = 100) -> dict:
        k_list = [k for k in [3, 5, 7, 11] if k <= n_samples] or [1]
        grids = {
            "Random Forest": {"model__n_estimators": [100, 200, 300], "model__max_depth": [None, 8, 16]},
            "Gradient Boosting": {"model__n_estimators": [100, 200], "model__learning_rate": [0.05, 0.1], "model__max_depth": [2, 3]},
            "Decision Tree": {"model__max_depth": [None, 5, 10, 20], "model__min_samples_split": [2, 5, 10]},
            "Logistic Regression": {"model__C": [0.1, 1.0, 10.0]},
            "Ridge": {"model__alpha": [0.1, 1.0, 10.0]},
            "KNN": {"model__n_neighbors": k_list},
            "Linear Regression": {},
        }
        return grids.get(name, {})

    def _tune(self, name, X, y, task_type, preprocessor, split) -> dict:
        X_tr, X_te, y_tr, y_te = split["X_tr"], split["X_te"], split["y_tr"], split["y_te"]
        est = self._models(task_type, n_samples=len(X_tr))[name]
        grid = self._param_grid(name, n_samples=len(X_tr))
        scoring = "accuracy" if task_type == "classification" else "r2"

        pipe = Pipeline([("prep", preprocessor), ("model", est)])
        best_params = {}
        best_cv = None
        if grid:
            try:
                gs = GridSearchCV(pipe, grid, cv=split["n_splits"], scoring=scoring, n_jobs=-1)
                gs.fit(X_tr, y_tr)
                pipe = gs.best_estimator_
                best_params = {k.replace("model__", ""): v for k, v in gs.best_params_.items()}
                best_cv = float(gs.best_score_)
            except Exception:
                pipe.fit(X_tr, y_tr)
        else:
            pipe.fit(X_tr, y_tr)

        metrics = self._eval(pipe, X_te, y_te, task_type)
        importances = self._importances(pipe, task_type)

        return {
            "name": name,
            "task_type": task_type,
            "best_params": best_params,
            "tuned_cv_score": _round(best_cv) if best_cv is not None else None,
            "test_score": metrics["primary"],
            "test_metrics": metrics["all"],
            "feature_importances": importances,
            "train_size": len(X_tr),
            "test_size": len(X_te),
        }

    def _importances(self, pipe, task_type: str) -> list:
        try:
            prep = pipe.named_steps["prep"]
            model = pipe.named_steps["model"]
            names = list(prep.get_feature_names_out())
            names = [n.split("__", 1)[-1] for n in names]
            if hasattr(model, "feature_importances_"):
                vals = model.feature_importances_
            elif hasattr(model, "coef_"):
                coef = np.asarray(model.coef_)
                vals = np.abs(coef).mean(axis=0) if coef.ndim > 1 else np.abs(coef)
            else:
                return []
            pairs = sorted(zip(names, vals), key=lambda x: x[1], reverse=True)[:10]
            total = float(sum(v for _, v in pairs)) or 1.0
            return [{"feature": n, "importance": _round(float(v)), "pct": round(float(v) / total * 100, 1)}
                    for n, v in pairs]
        except Exception:
            return []

    # ----- 6. Insights (LLM) --------------------------------------------------

    async def _insights(self, r: dict) -> dict:
        fallback = {
            "summary": (
                f"A {r['task_type']} model was trained to predict '{r['target']}'. "
                f"The best model was {r['model_card']['name']} with a test "
                f"{r['leaderboard'][0]['primary_metric']} of {r['model_card']['test_score']}."
            ),
            "findings": [],
            "recommendations": [],
        }
        if not self.openai:
            return fallback

        payload = {
            "target": r["target"], "task_type": r["task_type"],
            "profile": {
                "rows": r["profile"]["rows"], "cols": r["profile"]["cols"],
                "target_profile": r["profile"]["target_profile"],
                "correlations": r["profile"]["correlations"],
            },
            "cleaning": r["cleaning"]["log"],
            "leaderboard": [
                {"name": m["name"], "cv_score": m["cv_score"], "test": m["primary_score"]}
                for m in r["leaderboard"]
            ],
            "model_card": {
                "name": r["model_card"]["name"],
                "test_metrics": r["model_card"]["test_metrics"],
                "top_features": r["model_card"]["feature_importances"][:5],
            },
        }
        prompt = (
            "You are a senior data scientist. Given the real results of an automated ML pipeline "
            "below, write a concise interpretation. Return ONLY JSON:\n"
            "{\n"
            '  "summary": "3-4 sentence executive summary of what was built and how well it works",\n'
            '  "findings": ["a concrete insight grounded in the metrics or feature importances"],\n'
            '  "recommendations": ["a next step to improve the model or data"]\n'
            "}\n"
            "Be specific and reference the actual numbers. Do not invent metrics not present.\n\n"
            f"PIPELINE RESULTS:\n{json.dumps(payload, indent=2)[:9000]}"
        )
        try:
            resp = await self.openai.chat.completions.create(
                model=MODEL,
                messages=[{"role": "user", "content": prompt}],
                response_format={"type": "json_object"},
                temperature=0.4,
            )
            out = json.loads(resp.choices[0].message.content)
            out.setdefault("summary", fallback["summary"])
            out.setdefault("findings", [])
            out.setdefault("recommendations", [])
            return out
        except Exception:
            return fallback


# ----- module utilities -------------------------------------------------------

def _round(v):
    try:
        f = float(v)
        if _isnan(f):
            return None
        return round(f, 4)
    except (TypeError, ValueError):
        return None


def _isnan(v) -> bool:
    try:
        return math_isnan(float(v))
    except (TypeError, ValueError):
        return False


def math_isnan(x: float) -> bool:
    return x != x
