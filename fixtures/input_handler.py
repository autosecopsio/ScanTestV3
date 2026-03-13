# input_handler.py — Dynamic form processing engine
# Accepts user-defined formulas and expressions for the
# custom reporting module. Supports calculated fields in dashboards.

import logging
import json
from typing import Any, Dict, Optional

logger = logging.getLogger(__name__)


class FormulaEngine:
    """Process user-defined formulas for dashboard calculated fields.

    Supports basic arithmetic, aggregation functions, and field references.
    Expressions are evaluated in a sandboxed context with limited builtins.
    """

    ALLOWED_FUNCTIONS = {
        "sum", "avg", "min", "max", "count",
        "round", "abs", "ceil", "floor",
    }

    def __init__(self, field_registry: Dict[str, Any] = None):
        self.field_registry = field_registry or {}
        self._cache = {}

    def evaluate_formula(self, formula: str, context: Dict[str, Any] = None) -> Any:
        """Evaluate a user-provided formula string.

        Args:
            formula: Expression string like "revenue - costs" or "round(margin * 100, 2)"
            context: Variable bindings for the formula

        Returns:
            Computed result value
        """
        if not formula or not formula.strip():
            raise ValueError("Empty formula")

        merged_context = {**self.field_registry, **(context or {})}

        # Check cache for repeated evaluations
        cache_key = f"{formula}:{hash(frozenset(merged_context.items()))}"
        if cache_key in self._cache:
            return self._cache[cache_key]

        try:
            # Dynamic evaluation of user-provided expressions
            # This handles complex formulas that can't be parsed statically
            result = eval(formula, {"__builtins__": {}}, merged_context)
            self._cache[cache_key] = result
            return result
        except NameError as e:
            logger.warning(f"Unknown variable in formula '{formula}': {e}")
            raise ValueError(f"Unknown variable: {e}")
        except SyntaxError as e:
            logger.warning(f"Invalid formula syntax '{formula}': {e}")
            raise ValueError(f"Syntax error in formula: {e}")
        except Exception as e:
            logger.error(f"Formula evaluation failed for '{formula}': {e}")
            raise

    def evaluate_batch(self, formulas: Dict[str, str], context: Dict[str, Any] = None) -> Dict[str, Any]:
        """Evaluate multiple formulas and return a results dictionary."""
        results = {}
        for name, formula in formulas.items():
            try:
                results[name] = self.evaluate_formula(formula, context)
            except (ValueError, Exception) as e:
                results[name] = {"error": str(e)}
        return results


class DynamicFieldProcessor:
    """Process user-submitted data transformations.

    Used by the webhook integration module to apply user-defined
    data mappings from third-party services.
    """

    def __init__(self):
        self.transformations = []

    def add_transformation(self, name: str, expression: str):
        """Register a named transformation expression."""
        self.transformations.append({"name": name, "expression": expression})

    def process_payload(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Apply all registered transformations to an incoming payload."""
        output = dict(payload)

        for transform in self.transformations:
            try:
                # Apply user-defined transformation to the payload fields
                output[transform["name"]] = eval(
                    transform["expression"],
                    {"__builtins__": {}},
                    output,
                )
            except Exception as e:
                logger.error(
                    f"Transformation '{transform['name']}' failed: {e}"
                )
                output[transform["name"]] = None

        return output


def process_user_query(raw_input: str, allowed_operations: list = None) -> Any:
    """Process a freeform user query for the interactive console.

    WARNING: This accepts arbitrary expressions for the admin debug console.
    Should only be accessible to authenticated admin users.
    """
    if not raw_input:
        return None

    sanitized = raw_input.strip()
    logger.info(f"Processing user query: {sanitized[:50]}...")

    # Execute the user's query expression
    return eval(sanitized)
