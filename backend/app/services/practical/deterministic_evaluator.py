import math
from typing import Any

from app.services.practical.evaluator_base import EvaluationResult, PracticalEvaluator


class DeterministicEvaluator(PracticalEvaluator):
    """Deterministic, reproducible evaluator for practical statistical scenarios and numerical workflows."""

    VERSION = "v1.0-deterministic"

    def evaluate(self, task: Any, submission: dict[str, Any]) -> EvaluationResult:
        rubric = task.get_rubric()
        dimensions = rubric.get("dimensions", {})
        passing_score = rubric.get("passing_score", 0.70)

        if not dimensions:
            return EvaluationResult(
                score=0.0,
                passed=False,
                feedback="Task rubric has no defined evaluation dimensions.",
                evaluator_type="DETERMINISTIC",
                evaluator_version=self.VERSION,
                status="REVIEW_REQUIRED",
            )

        dimension_scores: dict[str, float] = {}
        dimension_feedback: list[str] = []
        total_weight = 0.0
        weighted_score_accum = 0.0

        for dim_name, dim_rule in dimensions.items():
            weight = dim_rule.get("weight", 1.0)
            total_weight += weight
            submitted_val = submission.get(dim_name)

            dim_score, dim_msg = self._evaluate_dimension(dim_name, dim_rule, submitted_val)
            dimension_scores[dim_name] = dim_score
            weighted_score_accum += dim_score * weight
            dimension_feedback.append(f"{dim_name}: {dim_msg} (Score: {dim_score:.2f}/{1.0})")

        overall_score = weighted_score_accum / total_weight if total_weight > 0 else 0.0
        overall_score = max(0.0, min(1.0, overall_score))
        passed = overall_score >= passing_score

        feedback_summary = (
            f"Practical evaluation {'PASSED' if passed else 'DID NOT PASS'} with score {overall_score:.2%}. "
            f"Passing threshold is {passing_score:.0%}.\n" + "\n".join(dimension_feedback)
        )

        return EvaluationResult(
            score=overall_score,
            passed=passed,
            feedback=feedback_summary,
            dimension_scores=dimension_scores,
            evaluator_type="DETERMINISTIC",
            evaluator_version=self.VERSION,
            status="EVALUATED",
            metadata={
                "passing_score": passing_score,
                "dimension_count": len(dimensions),
                "rubric_version": task.rubric_version,
            },
        )

    def _evaluate_dimension(
        self, dim_name: str, dim_rule: dict[str, Any], submitted_val: Any
    ) -> tuple[float, str]:
        if submitted_val is None:
            return 0.0, "Missing submission for dimension."

        # Case 1: Set / List match
        if dim_rule.get("match_type") == "set_equality" or (
            isinstance(dim_rule.get("expected"), list) and not isinstance(submitted_val, (int, float, str))
        ):
            expected_list = dim_rule.get("expected", [])
            expected_set = {str(x).strip().upper() for x in expected_list}
            if isinstance(submitted_val, (list, tuple, set)):
                sub_set = {str(x).strip().upper() for x in submitted_val}
            else:
                sub_set = {str(submitted_val).strip().upper()}

            if sub_set == expected_set:
                return 1.0, "Correct match."
            
            # Partial credit for Jaccard similarity or intersection
            if expected_set:
                overlap = len(sub_set.intersection(expected_set))
                union = len(sub_set.union(expected_set))
                sim = overlap / union if union > 0 else 0.0
                return sim, f"Partial match: expected {expected_list}, got {submitted_val}"
            return 0.0, "Mismatch."

        # Case 2: Dict of numerical values
        if isinstance(dim_rule.get("expected"), dict):
            expected_dict = dim_rule["expected"]
            tolerance = dim_rule.get("tolerance", 0.01)

            if not isinstance(submitted_val, dict):
                return 0.0, f"Expected dictionary format, got {type(submitted_val).__name__}."

            correct_count = 0
            total_items = len(expected_dict)
            item_details = []

            for key, exp_num in expected_dict.items():
                actual_num = submitted_val.get(key)
                if actual_num is None:
                    item_details.append(f"{key}: missing")
                    continue
                try:
                    actual_flt = float(actual_num)
                    exp_flt = float(exp_num)
                    diff = abs(actual_flt - exp_flt)
                    if diff <= tolerance:
                        correct_count += 1
                        item_details.append(f"{key}: ok")
                    else:
                        item_details.append(f"{key}: diff {diff:.4f} > tol {tolerance}")
                except (ValueError, TypeError):
                    item_details.append(f"{key}: non-numeric value")

            ratio = correct_count / total_items if total_items > 0 else 0.0
            return ratio, f"{correct_count}/{total_items} items correct. Details: {', '.join(item_details)}"

        # Case 3: Single numerical value
        if isinstance(dim_rule.get("expected"), (int, float)):
            expected_num = float(dim_rule["expected"])
            tolerance = float(dim_rule.get("tolerance", 0.01))

            try:
                actual_num = float(submitted_val)
                diff = abs(actual_num - expected_num)
                if diff <= tolerance:
                    return 1.0, f"Correct numerical value (diff {diff:.4f} <= tol {tolerance})."
                # Give partial credit if close (within 3x tolerance)
                if diff <= tolerance * 3:
                    return 0.5, f"Within boundary but exceeded tolerance: diff {diff:.4f} (tol {tolerance})."
                return 0.0, f"Incorrect numerical value: expected {expected_num}, got {actual_num} (diff {diff:.4f} > tol {tolerance})."
            except (ValueError, TypeError):
                return 0.0, f"Expected numeric value, got '{submitted_val}'."

        # Case 4: Text / Methodology keyword evaluation
        keywords = dim_rule.get("keywords")
        if keywords and isinstance(keywords, list):
            text = str(submitted_val).strip()
            min_length = dim_rule.get("min_length", 15)

            if len(text) < min_length:
                return 0.0, f"Methodology explanation too short (length {len(text)} < minimum {min_length})."

            text_lower = text.lower()
            matched_kw = [kw for kw in keywords if kw.lower() in text_lower]
            kw_ratio = len(matched_kw) / len(keywords) if keywords else 1.0

            if kw_ratio >= 0.70:
                return 1.0, f"Comprehensive explanation ({len(matched_kw)}/{len(keywords)} keywords matched: {', '.join(matched_kw)})."
            elif kw_ratio >= 0.40:
                return 0.6, f"Adequate explanation ({len(matched_kw)}/{len(keywords)} keywords matched)."
            else:
                return 0.2, f"Explanation lacks required statistical concepts (matched {len(matched_kw)}/{len(keywords)}: {', '.join(matched_kw)})."

        return 0.0, "Dimension rule could not be evaluated."
